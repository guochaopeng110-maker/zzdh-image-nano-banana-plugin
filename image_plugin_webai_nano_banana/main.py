# -*- coding: utf-8 -*-
"""WebAI image relay plugin."""

import base64
import json
import logging
import os
import re
import sqlite3
import sys
import threading
from datetime import datetime
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image
from PIL import ImageFile

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
try:
    from plugin_utils import load_plugin_config
except Exception:
    def load_plugin_config(_):
        return {}

_PLUGIN_FILE = __file__
_PLUGIN_ID = "image_plugin_webai_nano_banana"
_PLUGIN_VERSION = "1.0.0"
_SUPPORTED_MODELS = [
    "gemini-3.1-flash-image-preview",
    "gemini-3-pro-image-preview-2k",
    "flux-2-pro",
    "flux-2-max",
    "seedream-5.0-lite",
    "seedream-4.5",
    "qwen-image-2.0-pro",
    "grok-imagine-image-pro",
    "gpt-image-1.5-high-fidelity",
    "chatgpt-image-latest-high-fidelity",
]

plugin_dir = Path(__file__).parent
_TASK_LOG_DB_PATH = plugin_dir / "image_task_logs.db"
_DEFAULT_BASE_URL = "http://localhost:8316"
_log_buffer = []
_log_buffer_lock = threading.Lock()
_MAX_BUFFER_LOGS = 2000

_default_params = {
    "api_key": "",
    "base_url": _DEFAULT_BASE_URL,
    "model": _SUPPORTED_MODELS[0],
    "request_timeout": 60000,
    "download_timeout": 60000,
    "stream": False,
}

ImageFile.LOAD_TRUNCATED_IMAGES = True

_logger = logging.getLogger("image.webai")
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


if not any(isinstance(h, _BufferingHandler) for h in _logger.handlers):
    bh = _BufferingHandler()
    bh.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(bh)


def _log(msg, level="INFO"):
    getattr(_logger, level.lower(), _logger.info)(msg)


def _mask_secret(value, keep=4):
    s = str(value or "")
    if len(s) <= keep:
        return "*" * len(s)
    return "*" * (len(s) - keep) + s[-keep:]


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


def _extract_base64_images_from_text(content):
    if not content:
        return []
    text = str(content)
    pattern = r"data:image\/[a-zA-Z0-9.+-]+;base64,([A-Za-z0-9+/=\n\r]+)"
    matches = re.findall(pattern, text)
    return [re.sub(r"\s+", "", m) for m in matches if m]


def _extract_stream_chunks_base64(response):
    collected_text = []
    chunk_count = 0
    for raw_line in response.iter_lines(decode_unicode=True):
        if not raw_line:
            continue
        line = raw_line.strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            break
        try:
            chunk = json.loads(payload)
        except Exception:
            continue
        choices = chunk.get("choices") or []
        if not choices:
            continue
        delta = choices[0].get("delta") or {}
        part = delta.get("content")
        if part:
            collected_text.append(str(part))
            chunk_count += 1
    _log(f"[stream] collected delta chunks={chunk_count}")
    return _extract_base64_images_from_text("".join(collected_text))


def send_webai_image_request(
    api_key,
    endpoint,
    model,
    prompt,
    reference_images,
    request_timeout=300,
    stream=False,
):
    url = f"{_normalize_base_url(endpoint)}/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    ref_count = len(reference_images or {})
    _log(
        f"[request] prepare endpoint={url} model={model} stream={bool(stream)} "
        f"timeout_s={request_timeout} refs={ref_count}"
    )

    content_parts = [{"type": "text", "text": prompt}]
    for name, img_path in (reference_images or {}).items():
        if not os.path.exists(img_path) or os.path.getsize(img_path) <= 0:
            _log(f"[request] skip invalid reference key={name} path={img_path}", "WARNING")
            continue
        with open(img_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        content_parts.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_data}"},
            }
        )
        _log(f"[request] attached reference key={name} size={os.path.getsize(img_path)} bytes")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": content_parts if len(content_parts) > 1 else prompt,
            }
        ],
        "stream": bool(stream),
    }
    _log(f"[request] payload prepared content_parts={len(content_parts)}")

    response = requests.post(url, json=payload, headers=headers, timeout=request_timeout, stream=bool(stream))
    _log(f"[response] http_status={response.status_code} stream={bool(stream)}")
    if response.status_code != 200:
        raise Exception(f"HTTP {response.status_code}: {response.text}")

    if stream:
        images = _extract_stream_chunks_base64(response)
        _log(f"[response] parsed stream images={len(images)}")
    else:
        data = response.json()
        choices = data.get("choices") or []
        _log(f"[response] parsed choices={len(choices)}")
        if not choices:
            raise Exception("NO_RETRY:::API response has no choices")
        msg = choices[0].get("message") or {}
        images = _extract_base64_images_from_text(msg.get("content"))
        _log(f"[response] extracted inline images={len(images)}")

    if not images:
        raise Exception("NO_RETRY:::API response contains no image data")

    return images, None


def get_info():
    return {
        "name": "Image Relay Plugin - webai",
        "description": "Generate images via WebAI OpenAI-compatible chat/completions API.",
        "version": _PLUGIN_VERSION,
        "author": "unknown",
    }


def handle_action(action, data=None):
    data = data or {}
    _log(f"[action] received action={action}")
    if action == "open_live_logs":
        return {"ok": True, "open_page": "live_log.html"}
    if action == "open_task_logs":
        return {"ok": True, "open_page": "task_log.html"}
    if action == "get_task_logs":
        limit = int(data.get("limit", 200))
        status = data.get("status")
        logs = _fetch_task_logs(limit=limit, status_filter=status)
        _log(f"[action] get_task_logs limit={limit} status={status or 'ALL'} rows={len(logs)}")
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
        _log(f"[action] get_logs since_index={since_index} returned={len(logs)}")
        return {"ok": True, "logs": logs}
    return {"ok": False, "error": f"unknown action: {action}"}


def generate(context):
    prompt = context.get("prompt", "")
    reference_images = context.get("reference_images", {})
    output_dir = context.get("output_dir", "")
    plugin_params = context.get("plugin_params", {}) or {}
    viewer_index = context.get("viewer_index", 0)

    api_key = str(plugin_params.get("api_key", "")).strip()
    base_url = _normalize_base_url(plugin_params.get("base_url") or _DEFAULT_BASE_URL)
    model = str(plugin_params.get("model", _SUPPORTED_MODELS[0]))
    request_timeout = int(plugin_params.get("request_timeout", 300))
    stream_mode = str(plugin_params.get("stream", "false")).lower() in ("1", "true", "yes", "on")

    if not api_key:
        raise Exception("PLUGIN_ERROR:::missing api_key")

    os.makedirs(output_dir, exist_ok=True)
    _log(
        f"[generate] context viewer_index={viewer_index} prompt_len={len(str(prompt))} "
        f"refs={len(reference_images or {})} output_dir={output_dir}"
    )
    _log(
        f"[generate] params base_url={base_url} model={model} stream={stream_mode} "
        f"request_timeout_s={request_timeout} api_key={_mask_secret(api_key)}"
    )
    task_log_context = {
        "model_name": model,
        "task_mode": "stream" if stream_mode else "non-stream",
        "prompt": prompt,
    }
    task_log_id = _log_task_result(task_log_context, status="running")
    _log(f"[generate] start model={model} mode={task_log_context['task_mode']} task_log_id={task_log_id}")

    try:
        image_data_base64, _ = send_webai_image_request(
            api_key=api_key,
            endpoint=base_url,
            model=model,
            prompt=prompt,
            reference_images=reference_images,
            request_timeout=request_timeout,
            stream=stream_mode,
        )
        _log("[generate] request succeeded")
    except Exception as e:
        _log_task_result(task_log_context, status="failed", error=str(e), log_id=task_log_id, completed=True)
        _log(f"[generate] request failed: {e}", "ERROR")
        raise Exception(f"PLUGIN_ERROR:::{e}")

    generated_files = []
    image_list = image_data_base64 if isinstance(image_data_base64, list) else [image_data_base64]
    _log(f"[generate] decode images count={len(image_list)}")
    for idx, b64_image in enumerate(image_list):
        _log(f"[generate] decoding image {idx + 1}/{len(image_list)}")
        img = Image.open(BytesIO(base64.b64decode(b64_image)))
        img.load()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        suffix = f"_n{idx+1}" if len(image_list) > 1 else ""
        filename = f"{viewer_index:04d}_image_{timestamp}{suffix}.png"
        path = str(Path(output_dir) / filename)
        img.save(path, "PNG")
        generated_files.append(path)
        _log(f"[generate] persisted image {idx + 1}/{len(image_list)} bytes={os.path.getsize(path)}")
        _log_task_result(
            task_log_context,
            status="success",
            local_path=path,
            log_id=task_log_id if idx == 0 else None,
            completed=(idx == len(image_list) - 1),
        )
        _log(f"[generate] saved image {idx + 1}/{len(image_list)}: {path}")

    if not generated_files:
        _log_task_result(task_log_context, status="failed", error="all images failed to save", log_id=task_log_id, completed=True)
        raise Exception("PLUGIN_ERROR:::all images failed to save")

    _log(f"[generate] completed files={len(generated_files)}")
    return generated_files


_init_params = _default_params.copy()
_init_params.update(load_plugin_config(_PLUGIN_FILE))
_init_task_log_db()
