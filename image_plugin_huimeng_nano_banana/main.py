# -*- coding: utf-8 -*-
"""HuiMeng image relay plugin."""

import json
import logging
import os
import sqlite3
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
try:
    from plugin_utils import load_plugin_config
except Exception:
    def load_plugin_config(_):
        return {}

_PLUGIN_FILE = __file__
_PLUGIN_ID = "image_plugin_huimeng_nano_banana"
_PLUGIN_VERSION = "1.0.0"
_SUPPORTED_MODELS = [
    "image-2-official",
    "image-2",
    "nb-2-official",
    "nb-2",
    "nb-pro",
    "nb-pro-official",
    "z-image-turbo",
    "seedream-5.0-lite",
    "seedream-4.5",
]

plugin_dir = Path(__file__).parent
_TASK_LOG_DB_PATH = plugin_dir / "image_task_logs.db"
_FILE_LOG_DIR = plugin_dir / "logs"
_DEFAULT_BASE_URL = "https://api.huimengi.com"
_IMAGE_UPLOAD_URL = "https://imageproxy.zhongzhuan.chat/api/upload"
_log_buffer = []
_log_buffer_lock = threading.Lock()
_MAX_BUFFER_LOGS = 2000
_MAX_FILE_LOG_BYTES = 5 * 1024 * 1024
_file_log_lock = threading.Lock()
_file_log_path = None

_default_params = {
    "api_key": "",
    "base_url": _DEFAULT_BASE_URL,
    "model": _SUPPORTED_MODELS[0],
    "request_timeout": 60000,
    "download_timeout": 60000,
    "poll_interval_ms": 10000,
    "poll_timeout_ms": 120000,
    "ratio": "auto",
    "quality": "medium",
    "resolution": "1k",
}

_logger = logging.getLogger("image.huimeng")
if not _logger.handlers:
    _logger.setLevel(logging.INFO)
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    _logger.addHandler(h)


class _BufferingHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            with _log_buffer_lock:
                _log_buffer.append(
                    {
                        "index": len(_log_buffer) + 1,
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "level": record.levelname.upper(),
                        "message": msg,
                    }
                )
                if len(_log_buffer) > _MAX_BUFFER_LOGS:
                    _log_buffer[:] = _log_buffer[-_MAX_BUFFER_LOGS:]
                    for i, item in enumerate(_log_buffer):
                        item["index"] = i + 1
        except Exception:
            pass


if not any(getattr(h, "_is_huimeng_buffer_handler", False) for h in _logger.handlers):
    bh = _BufferingHandler()
    bh.setFormatter(logging.Formatter("%(message)s"))
    bh._is_huimeng_buffer_handler = True
    _logger.addHandler(bh)


def _log(msg, level="INFO"):
    getattr(_logger, level.lower(), _logger.info)(msg)


def _mask_secret(value, keep=4):
    s = str(value or "")
    if len(s) <= keep:
        return "*" * len(s)
    return "*" * (len(s) - keep) + s[-keep:]


def _ensure_file_log_path():
    global _file_log_path
    with _file_log_lock:
        if _file_log_path is None:
            _FILE_LOG_DIR.mkdir(parents=True, exist_ok=True)
            filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".log"
            _file_log_path = _FILE_LOG_DIR / filename
    return _file_log_path


def _append_file_log(event, payload):
    try:
        record = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "event": event,
            "payload": payload,
        }
        line = json.dumps(record, ensure_ascii=False)
        with _file_log_lock:
            _FILE_LOG_DIR.mkdir(parents=True, exist_ok=True)
            global _file_log_path
            if _file_log_path is None:
                filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".log"
                _file_log_path = _FILE_LOG_DIR / filename
            path = _file_log_path
            projected = len((line + "\n").encode("utf-8"))
            if path.exists() and (path.stat().st_size + projected) > _MAX_FILE_LOG_BYTES:
                filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".log"
                _file_log_path = _FILE_LOG_DIR / filename
                path = _file_log_path
            with open(path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
    except Exception as e:
        _log(f"[file-log] write failed: {e}", "WARNING")


_STATUS_DISPLAY_MAP = {
    "running": ("Running", "#2d8cf0"),
    "generated": ("Generated", "#8a2be2"),
    "success": ("Downloaded", "#19be6b"),
    "manual_success": ("Manual Downloaded", "#13c2c2"),
    "download_failed": ("Download Failed", "#fa8c16"),
    "failed": ("Failed", "#f5222d"),
}


def _get_status_display(status_key):
    status_key = (status_key or "").lower()
    return _STATUS_DISPLAY_MAP.get(status_key, (status_key or "unknown", "#999999"))


def _init_task_log_db():
    conn = sqlite3.connect(_TASK_LOG_DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS image_task_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                completed_at TEXT,
                model_name TEXT,
                task_mode TEXT,
                prompt TEXT,
                status TEXT,
                error TEXT,
                image_url TEXT,
                local_path TEXT
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_image_logs_status ON image_task_logs(status)")
        conn.commit()
    finally:
        conn.close()


def _insert_task_log_entry(entry):
    conn = sqlite3.connect(_TASK_LOG_DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO image_task_logs (created_at, completed_at, model_name, task_mode, prompt, status, error, image_url, local_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.get("created_at"),
                entry.get("completed_at"),
                entry.get("model_name"),
                entry.get("task_mode"),
                entry.get("prompt"),
                entry.get("status"),
                entry.get("error"),
                entry.get("image_url"),
                entry.get("local_path"),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _update_task_log_entry(log_id, **fields):
    if not log_id:
        return
    clean = {k: v for k, v in fields.items() if v is not None}
    if not clean:
        return
    assignments = [f"{k} = ?" for k in clean.keys()]
    params = list(clean.values()) + [log_id]
    conn = sqlite3.connect(_TASK_LOG_DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE image_task_logs SET {', '.join(assignments)} WHERE id = ?", params)
        conn.commit()
    finally:
        conn.close()


def _fetch_task_logs(limit=None, status_filter=None, task_ids=None):
    conn = sqlite3.connect(_TASK_LOG_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM image_task_logs WHERE 1=1"
        params = []
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)
        if task_ids:
            placeholders = ",".join(["?"] * len(task_ids))
            query += f" AND id IN ({placeholders})"
            params.extend(task_ids)
        query += " ORDER BY id DESC"
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        rows = cursor.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _log_task_result(task_context, status, image_url=None, local_path=None, error=None, log_id=None, completed=False):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if log_id:
        _update_task_log_entry(
            log_id,
            status=status,
            image_url=image_url,
            local_path=local_path,
            error=error,
            completed_at=now if completed else None,
        )
        return log_id
    entry = {
        "created_at": now,
        "completed_at": now if completed else None,
        "model_name": task_context.get("model_name"),
        "task_mode": task_context.get("task_mode"),
        "prompt": task_context.get("prompt"),
        "status": status,
        "error": error,
        "image_url": image_url,
        "local_path": local_path,
    }
    return _insert_task_log_entry(entry)


def _normalize_base_url(url: str) -> str:
    return (url or _DEFAULT_BASE_URL).rstrip("/")


def _collect_reference_image_inputs(reference_images):
    urls = []
    local_paths = []
    if isinstance(reference_images, dict):
        values = list(reference_images.values())
    elif isinstance(reference_images, (list, tuple)):
        values = list(reference_images)
    elif isinstance(reference_images, str):
        values = [reference_images]
    else:
        values = []

    for item in values:
        value = str(item or "").strip()
        if not value:
            continue
        if value.startswith(("http://", "https://")):
            urls.append(value)
            continue
        if os.path.exists(value) and os.path.getsize(value) > 0:
            local_paths.append(value)
    return urls, local_paths


def upload_image_to_host(image_path, timeout=60):
    try:
        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f)}
            response = requests.post(_IMAGE_UPLOAD_URL, files=files, timeout=timeout)
        if response.status_code != 200:
            _log(
                f"[ref-image] upload failed status={response.status_code} path={image_path}",
                "WARNING",
            )
            return None
        data = response.json()
        image_url = data.get("url")
        if image_url:
            return str(image_url)
        _log(f"[ref-image] upload missing url path={image_path}", "WARNING")
        return None
    except Exception as e:
        _log(f"[ref-image] upload error path={image_path} err={e}", "WARNING")
        return None


def _build_reference_image_payload(reference_images):
    direct_urls, local_paths = _collect_reference_image_inputs(reference_images)
    result = list(direct_urls)
    for path in local_paths:
        image_url = upload_image_to_host(path)
        if image_url:
            result.append(image_url)
        else:
            _log(f"[ref-image] skip failed upload path={path}", "WARNING")
    return result


def _download_image_from_url(url, timeout_s):
    resp = requests.get(url, timeout=timeout_s)
    if resp.status_code != 200:
        raise Exception(f"download failed HTTP {resp.status_code}")
    return resp.content


def _build_filename(viewer_index, idx, total, url):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    suffix = f"_n{idx+1}" if total > 1 else ""
    path_part = urlparse(url).path
    ext = os.path.splitext(path_part)[1].lower()
    ext = ext if ext in (".png", ".jpg", ".jpeg", ".webp") else ".png"
    return f"{viewer_index:04d}_image_{timestamp}{suffix}{ext}"


_MODEL_PARAM_SPECS = {
    "image-2-official": {
        "defaults": {"ratio": "auto", "quality": "medium", "resolution": "1k"},
        "enum": {
            "ratio": ["auto", "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
            "quality": ["low", "medium", "high"],
            "resolution": ["1k", "2k", "4k"],
        },
    },
    "image-2": {
        "defaults": {"ratio": "1:1", "quality": "medium", "resolution": "1k"},
        "enum": {
            "ratio": ["auto", "1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9", "1:4", "4:1", "1:8", "8:1"],
            "quality": ["low", "medium", "high"],
            "resolution": ["1k", "2k", "4k"],
        },
    },
    "nb-2-official": {
        "defaults": {"ratio": "auto", "resolution": "1k"},
        "enum": {
            "ratio": ["auto", "1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9", "1:4", "4:1", "1:8", "8:1"],
            "resolution": ["1k", "2k", "4k"],
        },
    },
    "nb-2": {
        "defaults": {"ratio": "auto", "resolution": "1K"},
        "enum": {
            "ratio": ["auto", "1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9", "1:4", "4:1", "1:8", "8:1"],
            "resolution": ["1K", "2K", "4K"],
        },
    },
    "nb-pro": {
        "defaults": {"ratio": "auto", "resolution": "1K"},
        "enum": {
            "ratio": ["auto", "1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9"],
            "resolution": ["1K", "2K", "4K"],
        },
    },
    "nb-pro-official": {
        "defaults": {"ratio": "auto", "resolution": "1k"},
        "enum": {
            "ratio": ["auto", "1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
            "resolution": ["1k", "2k", "4k"],
        },
    },
    "seedream-5.0-lite": {
        "defaults": {"ratio": "1:1", "resolution": "2K"},
        "enum": {
            "ratio": ["1:1", "4:3", "3:4", "16:9", "9:16", "3:2", "2:3", "21:9"],
            "resolution": ["2K", "3K"],
        },
    },
    "seedream-4.5": {
        "defaults": {"ratio": "1:1", "resolution": "2K"},
        "enum": {
            "ratio": ["1:1", "4:3", "3:4", "16:9", "9:16", "3:2", "2:3", "21:9"],
            "resolution": ["2K", "4K"],
        },
    },
    "z-image-turbo": {
        "defaults": {"orientation": "横屏"},
        "enum": {
            "orientation": ["横屏", "竖屏"],
        },
    },
}


def _coerce_enum(value, allowed, default_value):
    raw = str(value or "").strip()
    if not raw:
        return default_value
    lower_map = {str(item).lower(): item for item in allowed}
    return lower_map.get(raw.lower(), default_value)


def _build_model_params(model, prompt, plugin_params):
    model = str(model or "").strip()
    base = {"prompt": prompt}
    spec = _MODEL_PARAM_SPECS.get(model)
    if not spec:
        base["ratio"] = str(plugin_params.get("ratio") or "auto").strip() or "auto"
        base["resolution"] = str(plugin_params.get("resolution") or "1k").strip() or "1k"
        return base

    for field, allowed_values in spec.get("enum", {}).items():
        default_value = spec.get("defaults", {}).get(field)
        selected = _coerce_enum(plugin_params.get(field), allowed_values, default_value)
        if selected:
            base[field] = selected
    return base


def submit_huimeng_task(api_key, endpoint, model, params, request_timeout_s):
    url = f"{_normalize_base_url(endpoint)}/api/v1/tasks"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {"model": model, "params": params}
    payload_for_log = {"model": model, "params": params}
    _log(
        f"[request] submit endpoint={url} model={model} timeout_s={request_timeout_s} payload={json.dumps(payload_for_log, ensure_ascii=False)}"
    )
    _append_file_log(
        "submit.request",
        {
            "url": url,
            "method": "POST",
            "headers": {"Content-Type": "application/json", "Authorization": f"Bearer {_mask_secret(api_key)}"},
            "json": payload_for_log,
            "timeout_s": request_timeout_s,
        },
    )
    resp = requests.post(url, json=payload, headers=headers, timeout=request_timeout_s)
    _log(f"[response] submit status_code={resp.status_code} body={resp.text[:1000]}")
    _append_file_log(
        "submit.response",
        {
            "url": url,
            "status_code": resp.status_code,
            "body": resp.text,
        },
    )
    if resp.status_code != 200:
        raise Exception(f"HTTP {resp.status_code}: {resp.text}")
    data = resp.json()
    task_id = data.get("task_id") or data.get("id")
    if not task_id:
        raise Exception("NO_RETRY:::task_id missing")
    return str(task_id)


def poll_huimeng_result(api_key, endpoint, task_id, request_timeout_s, poll_interval_ms, poll_timeout_ms):
    url = f"{_normalize_base_url(endpoint)}/api/v1/tasks/{task_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    _log(f"[request] poll endpoint={url} timeout_s={request_timeout_s} interval_ms={poll_interval_ms} timeout_ms={poll_timeout_ms}")
    start = time.time()
    rounds = 0
    while True:
        rounds += 1
        _append_file_log(
            "poll.request",
            {
                "url": url,
                "method": "GET",
                "headers": {"Authorization": f"Bearer {_mask_secret(api_key)}"},
                "task_id": task_id,
                "round": rounds,
                "timeout_s": request_timeout_s,
            },
        )
        resp = requests.get(url, headers=headers, timeout=request_timeout_s)
        _log(f"[response] poll status_code={resp.status_code}")
        _append_file_log(
            "poll.response",
            {
                "url": url,
                "task_id": task_id,
                "round": rounds,
                "status_code": resp.status_code,
                "body": resp.text,
            },
        )
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}: {resp.text}")
        data = resp.json()
        status = str(data.get("status", "")).lower()
        _log(f"[poll] task_id={task_id} round={rounds} status={status}")
        if status == "completed":
            result = data.get("result") or {}
            _log(
                "[poll] completed task_id={} result.size={} result.ratio={} result.resolution={}".format(
                    task_id,
                    result.get("size"),
                    result.get("ratio"),
                    result.get("resolution"),
                )
            )
            urls = result.get("image_urls") or []
            if not urls and result.get("image_url"):
                urls = [result.get("image_url")]
            urls = [u for u in urls if u]
            if not urls:
                raise Exception("NO_RETRY:::completed but no image urls")
            return urls
        if status == "failed":
            raise Exception(f"NO_RETRY:::{data.get('error_message') or 'task failed'}")
        if (time.time() - start) * 1000 > poll_timeout_ms:
            raise Exception("PLUGIN_ERROR:::poll timeout")
        time.sleep(max(0.1, poll_interval_ms / 1000.0))


def get_info():
    return {
        "name": "Image Relay Plugin - huimeng",
        "description": "Generate images via HuiMeng async task API.",
        "version": _PLUGIN_VERSION,
        "author": "unknown",
    }


def handle_action(action, data=None):
    data = data or {}
    if action != "get_logs":
        _log(f"[action] received action={action}")
    if action == "open_live_logs":
        return {"ok": True, "open_page": "live_log.html"}
    if action == "open_task_logs":
        return {"ok": True, "open_page": "task_log.html"}
    if action == "get_task_logs":
        limit = int(data.get("limit", 200))
        status = data.get("status")
        logs = _fetch_task_logs(limit=limit, status_filter=status)
        for log in logs:
            status_text, status_color = _get_status_display(log.get("status"))
            log["status_display"] = status_text
            log["status_color"] = status_color
            log["model_display"] = log.get("model_name")
        return {"ok": True, "logs": logs}
    if action == "download_images":
        return {"ok": True, "results": []}
    if action == "get_logs":
        since_index = int(data.get("since_index", 0))
        with _log_buffer_lock:
            logs = [item for item in _log_buffer if item["index"] > since_index]
        return {"ok": True, "logs": logs}
    return {"ok": False, "error": f"unknown action: {action}"}


def generate(context):
    prompt = context.get("prompt", "")
    output_dir = context.get("output_dir", "")
    plugin_params = context.get("plugin_params", {}) or {}
    reference_images = context.get("reference_images", {}) or {}
    viewer_index = context.get("viewer_index", 0)

    api_key = str(plugin_params.get("api_key", "")).strip()
    base_url = _normalize_base_url(plugin_params.get("base_url") or _DEFAULT_BASE_URL)
    model = str(plugin_params.get("model", _SUPPORTED_MODELS[0]))
    request_timeout_s = max(1, int(plugin_params.get("request_timeout", 60000)) // 1000)
    download_timeout_s = max(1, int(plugin_params.get("download_timeout", 60000)) // 1000)
    poll_interval_ms = max(10000, int(plugin_params.get("poll_interval_ms", 10000)))
    poll_timeout_ms = int(plugin_params.get("poll_timeout_ms", 120000))

    if not api_key:
        raise Exception("PLUGIN_ERROR:::missing api_key")

    os.makedirs(output_dir, exist_ok=True)
    direct_urls, local_paths = _collect_reference_image_inputs(reference_images)
    image_refs = _build_reference_image_payload(reference_images)
    _log(
        f"[generate] reference_images input={len(reference_images) if isinstance(reference_images, dict) else 0} direct_urls={len(direct_urls)} local_paths={len(local_paths)} resolved_urls={len(image_refs)}"
    )

    task_log_context = {
        "model_name": model,
        "task_mode": "img2img" if image_refs else "txt2img",
        "prompt": prompt,
    }
    task_log_id = _log_task_result(task_log_context, status="running")

    try:
        model_params = _build_model_params(model, prompt, plugin_params)
        if image_refs:
            model_params["image"] = image_refs[0] if len(image_refs) == 1 else image_refs
        _log(f"[generate] model={model} params={json.dumps(model_params, ensure_ascii=False)}")
        task_id = submit_huimeng_task(api_key, base_url, model, model_params, request_timeout_s)
        _log(f"[generate] submitted task_id={task_id}")
        url_list = poll_huimeng_result(
            api_key, base_url, task_id, request_timeout_s, poll_interval_ms, poll_timeout_ms
        )
        _log(f"[generate] completed urls={len(url_list)}")
    except Exception as e:
        _log_task_result(task_log_context, status="failed", error=str(e), log_id=task_log_id, completed=True)
        raise Exception(f"PLUGIN_ERROR:::{e}")

    generated_files = []
    for idx, image_url in enumerate(url_list):
        try:
            content = _download_image_from_url(image_url, download_timeout_s)
            filename = _build_filename(viewer_index, idx, len(url_list), image_url)
            path = str(Path(output_dir) / filename)
            with open(path, "wb") as f:
                f.write(content)
            generated_files.append(path)
            _log_task_result(
                task_log_context,
                status="success",
                image_url=image_url,
                local_path=path,
                log_id=task_log_id if idx == 0 else None,
                completed=(idx == len(url_list) - 1),
            )
        except Exception as e:
            _log_task_result(task_log_context, status="download_failed", image_url=image_url, error=str(e), log_id=task_log_id)

    if not generated_files:
        _log_task_result(task_log_context, status="failed", error="all images failed to download", log_id=task_log_id, completed=True)
        raise Exception("PLUGIN_ERROR:::all images failed to download")

    return generated_files


_init_params = _default_params.copy()
_init_params.update(load_plugin_config(_PLUGIN_FILE))
_init_task_log_db()
