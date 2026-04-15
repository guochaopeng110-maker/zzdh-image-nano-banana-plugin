# -*- coding: utf-8 -*-
"""
Nano Banana 中转插件 - zlhub
通过 zlhub API 调用 nano banana 2、doubao-seedream-4.5 模型生成图片
"""

import base64
import collections
import hashlib
import json
import logging
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import threading
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from plugin_utils import load_plugin_config

# --------------------- 工具 ---------------------


def _serialize_reference_images(reference_images):
    try:
        return json.dumps(reference_images, ensure_ascii=False, default=str)
    except Exception as err:
        print(f"[TaskLog] 序列化参考图片失败: {err}")
        return str(reference_images)


def _dict_to_json(data):
    if not data:
        return None
    try:
        return json.dumps(data, ensure_ascii=False, default=str)
    except Exception as err:
        print(f"[TaskLog] 序列化 metadata 失败: {err}")
        return None


def _normalize_base_url(url: str) -> str:
    if not url:
        return ""
    return url.rstrip("/")


def image_to_base64(image_path):
    """
    将图片转换为 base64
    """
    try:
        with Image.open(image_path) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")

            buffered = BytesIO()
            img.save(buffered, format="PNG")
            base64_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            return base64_str
    except Exception as e:
        print(f"Error converting image to base64: {str(e)}")
        return None


class ImageDownloadError(Exception):
    def __init__(self, message, image_url=None):
        super().__init__(message)
        self.image_url = image_url


def _get_valid_base_url(url: str) -> str:
    normalized = _normalize_base_url(url)
    if not normalized:
        return _normalize_base_url(_DEFAULT_BASE_URL)
    for suffix in ("/v1beta", "/v1"):
        if normalized.endswith(suffix):
            normalized = _normalize_base_url(normalized[: -len(suffix)])
            break
    if normalized in _VALID_BASE_URLS:
        return normalized
    return _normalize_base_url(_DEFAULT_BASE_URL)


# --------------------- 工具 ---------------------

# --------------------- SQLite 任务日志 ---------------------

_STATUS_DISPLAY_MAP = {
    "running": ("运行中", "#FFD600"),
    "generated": ("生成成功", "#4CAF50"),  # API 返回 URL，生成成功
    "success": ("下载成功", "#4CAF50"),  # 下载到本地成功
    "manual_success": ("手动下载成功", "#4CAF50"),
    "failed": ("生成失败", "#FF5252"),
    "no_retry_error": ("生成失败", "#FF5252"),
    "download_failed": ("下载失败", "#42A5F5"),
    "manual_failed": ("下载失败", "#42A5F5"),
}


def _get_status_display(status_key):
    status_key = (status_key or "").lower()
    return _STATUS_DISPLAY_MAP.get(status_key, (status_key or "未知", "#FFFFFF"))


def _init_task_log_db():
    try:
        conn = sqlite3.connect(_TASK_LOG_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS image_task_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                completed_at TEXT,
                model_display TEXT,
                model_name TEXT,
                prompt TEXT,
                aspect_ratio TEXT,
                image_size TEXT,
                reference_images TEXT,
                base_url TEXT,
                endpoint TEXT,
                task_mode TEXT,
                status TEXT,
                image_url TEXT,
                local_path TEXT,
                error TEXT,
                metadata TEXT
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_image_logs_status ON image_task_logs(status)"
        )
        cursor.execute("PRAGMA table_info(image_task_logs)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if "task_mode" not in existing_cols:
            cursor.execute("ALTER TABLE image_task_logs ADD COLUMN task_mode TEXT")
        if "completed_at" not in existing_cols:
            cursor.execute("ALTER TABLE image_task_logs ADD COLUMN completed_at TEXT")
        conn.commit()
    except Exception as err:
        print(f"[TaskLog] 初始化数据库失败: {err}")
    finally:
        if "conn" in locals():
            conn.close()


def _insert_task_log_entry(entry):
    try:
        conn = sqlite3.connect(_TASK_LOG_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO image_task_logs (
                created_at, completed_at, model_display, model_name, prompt, aspect_ratio,
                image_size, reference_images, base_url, endpoint, task_mode, status,
                image_url, local_path, error, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.get("created_at"),
                entry.get("completed_at"),
                entry.get("model_display"),
                entry.get("model_name"),
                entry.get("prompt"),
                entry.get("aspect_ratio"),
                entry.get("image_size"),
                entry.get("reference_images"),
                entry.get("base_url"),
                entry.get("endpoint"),
                entry.get("task_mode"),
                entry.get("status"),
                entry.get("image_url"),
                entry.get("local_path"),
                entry.get("error"),
                entry.get("metadata"),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as err:
        print(f"[TaskLog] 写入失败: {err}")
    finally:
        if "conn" in locals():
            conn.close()
    return None


def _update_task_log_entry(log_id, **fields):
    if not fields:
        return
    assignments = []
    values = []
    for key, value in fields.items():
        assignments.append(f"{key} = ?")
        values.append(value)
    values.append(log_id)
    try:
        conn = sqlite3.connect(_TASK_LOG_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE image_task_logs SET {', '.join(assignments)} WHERE id = ?", values
        )
        conn.commit()
    except Exception as err:
        print(f"[TaskLog] 更新失败: {err}")
    finally:
        if "conn" in locals():
            conn.close()


def _fetch_task_logs(limit=None, status_filter=None, task_ids=None, require_url=False):
    try:
        conn = sqlite3.connect(_TASK_LOG_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT * FROM image_task_logs WHERE 1=1"
        params = []
        if status_filter:
            placeholders = ",".join(["?"] * len(status_filter))
            query += f" AND status IN ({placeholders})"
            params.extend(status_filter)
        if task_ids:
            placeholders = ",".join(["?"] * len(task_ids))
            query += f" AND id IN ({placeholders})"
            params.extend(task_ids)
        if require_url:
            query += " AND image_url IS NOT NULL AND image_url != ''"
        query += " ORDER BY id DESC"
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as err:
        print(f"[TaskLog] 查询失败: {err}")
        return []
    finally:
        if "conn" in locals():
            conn.close()


def get_recent_task_logs(limit=20, status=None):
    status_filter = [status] if status else None
    return _fetch_task_logs(limit=limit, status_filter=status_filter)


def _download_file_from_url(image_url, timeout):
    download_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
    response = requests.get(
        image_url,
        headers=download_headers,
        timeout=timeout,
        stream=True,
    )
    if response.status_code != 200:
        raise Exception(f"HTTP {response.status_code}")
    return response.content


def _infer_filename_from_log(log):
    if log.get("local_path"):
        return os.path.basename(log["local_path"])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"task_{log['id']}_{timestamp}.png"


def download_images_from_logs(
    task_ids=None, status_filter=None, output_dir=None, limit=None, download_timeout=300
):
    logs = _fetch_task_logs(
        limit=limit, status_filter=status_filter, task_ids=task_ids, require_url=True
    )
    if not logs:
        return []
    target_dir = Path(output_dir) if output_dir else (plugin_dir / "manual_downloads")
    target_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for log in logs:
        image_url = log.get("image_url")
        if not image_url:
            results.append(
                {"id": log["id"], "status": "skipped", "message": "日志中无图片URL"}
            )
            continue
        metadata = {}
        if log.get("metadata"):
            try:
                metadata = json.loads(log["metadata"])
            except json.JSONDecodeError:
                metadata = {}
        timeout = int(metadata.get("download_timeout", download_timeout))
        filename = _infer_filename_from_log(log)
        dest_path = target_dir / filename
        try:
            file_bytes = _download_file_from_url(image_url, timeout)
            with open(dest_path, "wb") as f:
                f.write(file_bytes)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            _update_task_log_entry(
                log["id"],
                status="manual_success",
                local_path=str(dest_path),
                error=None,
                completed_at=timestamp,
            )
            results.append(
                {"id": log["id"], "status": "success", "message": str(dest_path)}
            )
        except Exception as err:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            _update_task_log_entry(
                log["id"],
                status="download_failed",
                error=str(err),
                completed_at=timestamp,
            )
            results.append({"id": log["id"], "status": "failed", "message": f"{err}"})
    return results


def _log_task_result(
    task_context,
    status,
    image_url=None,
    local_path=None,
    error=None,
    log_id=None,
    completed=False,
):
    if not task_context:
        return None
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if log_id:
        update_fields = {
            "status": status,
            "image_url": image_url or "",
            "local_path": local_path,
            "error": error,
        }
        if completed:
            update_fields["completed_at"] = timestamp
        _update_task_log_entry(
            log_id, **{k: v for k, v in update_fields.items() if v is not None}
        )
        print(f"[TaskLog] 更新任务日志 ID={log_id}, 状态={status}")
        return log_id
    entry = {
        "created_at": timestamp,
        "completed_at": timestamp if completed else None,
        "model_display": task_context.get("model_display"),
        "model_name": task_context.get("model_name"),
        "prompt": task_context.get("prompt"),
        "aspect_ratio": task_context.get("aspect_ratio"),
        "image_size": task_context.get("image_size"),
        "reference_images": _serialize_reference_images(
            task_context.get("reference_images", {})
        ),
        "base_url": task_context.get("base_url"),
        "endpoint": task_context.get("endpoint"),
        "task_mode": task_context.get("task_mode"),
        "status": status,
        "image_url": image_url or "",
        "local_path": local_path,
        "error": error,
        "metadata": _dict_to_json(task_context.get("metadata")),
    }
    log_id = _insert_task_log_entry(entry)
    if log_id:
        print(f"[TaskLog] 已记录任务日志 ID={log_id}, 状态={status}")
    return log_id


# --------------------- SQLite 任务日志 ---------------------

# --------------------- 实时日志 ---------------------


class _BufferingHandler(logging.Handler):
    """将日志记录缓存到内存，供 iframe 实时日志面板拉取。"""

    def emit(self, record):
        global _log_index
        with _log_lock:
            _log_index += 1
            _log_buffer.append(
                {
                    "index": _log_index,
                    "time": datetime.fromtimestamp(record.created).strftime("%H:%M:%S"),
                    "level": record.levelname,
                    "message": self.format(record),
                }
            )


def _setup_logging():
    """初始化全局 Logger"""
    logger = logging.getLogger("image.GeekNow")  # 要去video不同
    logger.setLevel(logging.INFO)
    logger.handlers = []

    # 增加时间格式，方便在日志文件中查看
    fmt = logging.Formatter("%(asctime)s - [%(name)s] %(message)s")

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    # 内存缓存（供 UI 实时查看）
    buf_handler = _BufferingHandler()
    buf_handler.setFormatter(fmt)
    logger.addHandler(buf_handler)

    # 文件输出
    try:
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 以日期和时间区分文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"plugin_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to create log file: {e}")

    return logger


def _log(msg, level="INFO"):
    """
    兼容旧代码的 _log 调用，转发到 standard logging
    """
    if str(level).upper() == "ERROR":
        _logger.error(msg)
    elif str(level).upper() == "WARNING":
        _logger.warning(msg)
    elif str(level).upper() == "DEBUG":
        _logger.debug(msg)
    else:
        _logger.info(msg)


def get_buffered_logs(since_index=0):
    """返回索引 > since_index 的所有缓冲日志条目。"""
    with _log_lock:
        return [e for e in _log_buffer if e["index"] > since_index]


def _task_status_to_log_level(status_key):
    status_key = (status_key or "").lower()
    if status_key in {"failed", "no_retry_error", "download_failed", "manual_failed"}:
        return "ERROR"
    if status_key == "running":
        return "WARNING"
    return "INFO"


def _extract_time_text(dt_text):
    text = str(dt_text or "").strip()
    if len(text) >= 19:
        return text[11:19]
    return datetime.now().strftime("%H:%M:%S")


def _format_task_log_message(task_log):
    status_key = (task_log.get("status") or "").lower()
    status_text, _ = _get_status_display(status_key)
    parts = [f"[TaskLog#{task_log.get('id')}] {status_text}"]

    if task_log.get("model_display"):
        parts.append(f"模型: {task_log.get('model_display')}")

    if task_log.get("error"):
        parts.append(f"错误: {task_log.get('error')}")
    elif task_log.get("local_path"):
        parts.append(f"本地: {task_log.get('local_path')}")
    elif task_log.get("image_url"):
        parts.append(f"URL: {task_log.get('image_url')}")

    return " | ".join(parts)


def _seed_buffer_from_task_logs(limit=100):
    """当实时日志缓冲为空时，使用任务日志做跨上下文兜底。"""
    global _log_index

    logs = _fetch_task_logs(limit=limit)
    if not logs:
        return 0

    logs.sort(key=lambda item: int(item.get("id") or 0))

    with _log_lock:
        if _log_buffer or _log_index > 0:
            return 0

        for item in logs:
            idx = int(item.get("id") or 0)
            if idx <= 0:
                _log_index += 1
                idx = _log_index
            else:
                _log_index = max(_log_index, idx)

            _log_buffer.append(
                {
                    "index": idx,
                    "time": _extract_time_text(
                        item.get("completed_at") or item.get("created_at")
                    ),
                    "level": _task_status_to_log_level(item.get("status")),
                    "message": _format_task_log_message(item),
                }
            )

    return len(logs)


# --------------------- 实时日志 ---------------------


# --------------------- 插件必要 ---------------------
def get_info():
    """返回插件信息"""
    return {
        "name": "图片中转插件 - zlhub(迁移版)",
        "description": "通过 zlhub 中转 API 生成图片，支持文本提示词和参考图片\n注意：软件未与任何中转平台达成合作，不对任何中转平台的安全性负责，请谨慎辨别。",
        "version": "1.0.0",
        "author": "unknown",
    }


def handle_action(action, data=None):
    """
    处理来自 iframe 的自定义动作请求
    """
    if data is None:
        data = {}
    if action == "open_live_logs":
        # 返回打开页面的指令，宿主引擎会据此打开 live_log.html
        return {"ok": True, "open_page": "live_log.html"}
    elif action == "open_task_logs":
        return {"ok": True, "open_page": "task_log.html"}
    elif action == "get_task_logs":
        limit = data.get("limit", 200)
        status = data.get("status")
        logs = get_recent_task_logs(limit=limit, status=status)
        for log in logs:
            status_key = log.get("status", "")
            display_text, color = _get_status_display(status_key)
            log["status_display"] = display_text
            log["status_color"] = color
        return {"ok": True, "logs": logs}
    elif action == "download_images":
        task_ids = data.get("task_ids", [])
        if not task_ids:
            return {"ok": False, "error": "未选择任务"}
        results = download_images_from_logs(task_ids=task_ids)
        return {"ok": True, "results": results}
    elif action == "get_logs":
        since = data.get("since_index", 0)
        logs = get_buffered_logs(since_index=since)
        if not logs:
            _seed_buffer_from_task_logs(limit=100)
            logs = get_buffered_logs(since_index=since)
        return {"ok": True, "logs": logs}
    elif action == "check_update":
        return _check_update_available()

    elif action == "do_update":
        return _execute_update(
            data.get("download_url", ""),
            data.get("sha256", ""),
        )
    else:
        return {"ok": False, "error": f"未知动作: {action}"}


def send_zlhub_image_request(
    api_key,
    endpoint,
    model,
    prompt,
    reference_images,
    aspect_ratio="16:9",
    request_timeout=300,
    image_size="2K",
    download_timeout=300,
):
    """
    发送 zlhub chat/completions 图像请求（nano banana 2 / doubao-seedream-4.5 同接口）

    Args:
        api_key: API 密钥
        endpoint: API 端点
        model: 模型名称
        prompt: 提示词
        reference_images: 参考图片路径字典 {position: path}
        aspect_ratio: 图片比例 (例如: '16:9', '1:1', '9:16')
        request_timeout: 请求超时时间
        image_size: 图片尺寸配置（映射到 zlhub 字段 size）

    Returns:
        (base64 编码的图片数据, 图片URL/URL列表)
    """
    _log(
        f"send_zlhub_image_request: model={model}, prompt={prompt}, aspect_ratio={aspect_ratio}"
    )

    normalized_base = _normalize_base_url(endpoint)
    url = f"{normalized_base}/zhonglian/api/v1/proxy/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    # 处理参考图片：有参考图时 image 必须为数组；文生图时 image 为空字符串
    image_mode = bool(reference_images)
    image_value = [] if image_mode else ""

    if image_mode:
        valid_image_paths = []
        for position, img_path in reference_images.items():
            if os.path.exists(img_path) and os.path.getsize(img_path) > 0:
                valid_image_paths.append((position, img_path))

        image_list = []
        use_url_mode = False

        if valid_image_paths:
            # 第一阶段: 尝试把所有图片都上传到图床
            url_list = []
            all_upload_success = True

            for position, img_path in valid_image_paths:
                image_url = upload_image_to_host(img_path)
                if image_url:
                    url_list.append(image_url)
                    _log(f"[图床] 上传成功: {position} -> {image_url}")
                else:
                    _log(f"[图床] 上传失败: {position} -> {img_path}")
                    all_upload_success = False
                    break

            # 第二阶段: 根据上传结果决定使用URL还是base64
            if all_upload_success and len(url_list) == len(valid_image_paths):
                image_list = url_list
                use_url_mode = True
                _log("[zlhub] 所有参考图片上传成功，使用URL模式")
            else:
                _log("[zlhub] 图床上传失败，全部回退到base64模式")
                for position, img_path in valid_image_paths:
                    try:
                        with open(img_path, "rb") as f:
                            image_data = base64.b64encode(f.read()).decode("utf-8")
                        image_list.append(image_data)
                        _log(f"添加参考图片(base64模式): {position} -> {img_path}")
                    except Exception as e:
                        _log(f"加载图片失败 {img_path}: {e}")

            if image_list:
                image_value = image_list
            _log(
                f"[zlhub API 请求] 参考图片模式: {'URL' if use_url_mode else 'base64'}"
            )

    payload = {
        "model": model,
        "prompt": prompt,
        "response_format": "url",
        "size": image_size,
        "stream": False,
        "watermark": True,
        "sequential_image_generation": "disabled",
        "image": image_value,
    }

    _log(f"[zlhub API 请求] 请求端点: {url}")
    _log("[zlhub API 请求] 请求头: Authorization=Bearer ***")

    payload_display = payload.copy()
    if isinstance(payload_display.get("image"), list):
        payload_display["image"] = [
            img
            if isinstance(img, str) and img.startswith("http")
            else f"<base64图片数据，长度: {len(img)} 字符>"
            for img in payload_display["image"]
        ]
    _log(
        f"[Doubao API 请求] 请求体: {json.dumps(payload_display, indent=2, ensure_ascii=False)}"
    )

    # 发送请求
    response = requests.post(
        url, json=payload, headers=headers, timeout=request_timeout
    )

    if response.status_code != 200:
        raise Exception(f"HTTP {response.status_code}: {response.text}")

    data = response.json()
    _log(f"[zlhub API 响应] {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")

    if "data" not in data or len(data["data"]) == 0:
        raise Exception("NO_RETRY:::API 未返回有效结果")

    image_urls = []
    for idx, image_result in enumerate(data["data"]):
        _log(f"[zlhub] 第 {idx + 1} 个结果: {image_result}")
        if isinstance(image_result, dict) and image_result.get("url"):
            image_urls.append(image_result["url"])

    if not image_urls:
        raise Exception("NO_RETRY:::API 响应中未包含任何图片 URL")

    _log(f"[Doubao] 共获取到 {len(image_urls)} 张图片 URL")
    return None, image_urls[0] if len(image_urls) == 1 else image_urls


def _download_image_from_url(image_url, download_timeout=300):
    """
    从 URL 下载图片并返回 base64 数据

    Args:
        image_url: 图片 URL
        download_timeout: 下载超时时间

    Returns:
        base64 编码的图片数据

    Raises:
        ImageDownloadError: 下载失败时抛出
    """
    print(f"开始下载图片: {image_url}")
    try:
        download_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        img_response = requests.get(
            image_url,
            headers=download_headers,
            timeout=download_timeout,
            stream=True,
        )

        if img_response.status_code == 200:
            image_data_base64 = base64.b64encode(img_response.content).decode("utf-8")
            print(f"✓ 成功下载图片")
            return image_data_base64
        else:
            error_msg = f"下载图片失败，HTTP 状态码: {img_response.status_code}"
            raise ImageDownloadError(error_msg, image_url)

    except requests.exceptions.Timeout as e:
        error_msg = f"下载图片超时: {str(e)}"
        raise ImageDownloadError(error_msg, image_url)
    except ImageDownloadError:
        raise
    except Exception as e:
        error_msg = f"下载图片时出错: {str(e)}"
        raise ImageDownloadError(error_msg, image_url)


def upload_image_to_host(image_path, timeout=60):
    """
    将图片上传到图床获取URL

    Args:
        image_path: 本地图片路径
        timeout: 请求超时时间

    Returns:
        str: 成功返回图片URL，失败返回None
    """
    url = "https://imageproxy.zhongzhuan.chat/api/upload"
    print(f"[图床] 正在上传: {image_path} 到 {url}")

    try:
        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f)}
            response = requests.post(url, files=files, timeout=timeout)

            if response.status_code == 200:
                data = response.json()
                image_url = data.get("url")
                if image_url:
                    print(f"[图床] 上传成功: {image_url}")
                    return image_url
                else:
                    print(f"[图床] 上传失败: 响应中未找到 'url' 字段。响应: {data}")
                    return None
            else:
                print(
                    f"[图床] 上传失败: 状态码 {response.status_code}, 响应: {response.text}"
                )
                return None
    except Exception as e:
        print(f"[图床] 上传时发生错误: {e}")
        return None


def generate(context):
    """
    主生成函数 - 通过中转 API 调用 Gemini 2.5 Flash Image 生成图片

    参数:
        context: 字典，包含以下键:
            - prompt: 正向提示词
            - reference_images: 参考图片字典 {位置: 图片路径}
            - output_dir: 输出目录
            - plugin_params: 插件自定义参数 (api_key, base_url 等)

    返回:
        生成的图片路径列表

    注意：参数同步已由 plugin_engine 在主线程中调用 _force_sync_params_from_ui() 完成
    不要在此函数中调用，因为此函数在工作线程中执行，无法安全访问UI控件
    """
    _log("\n" + "=" * 60)
    _log("Nano Banana zlhub 插件开始生成")
    _log("=" * 60)

    # ── 解析参数 ──────────────────────────────────────────────
    prompt = context.get("prompt", "")
    reference_images = context.get("reference_images", {})
    output_dir = context.get("output_dir", "")
    plugin_params = context.get("plugin_params", {}) or {}
    viewer_index = context.get("viewer_index", 0)

    api_key = str(plugin_params.get("api_key", ""))
    base_url = _get_valid_base_url(
        plugin_params.get("base_url")
        or plugin_params.get("endpoint")
        or _init_params.get("base_url")
    )
    model_display = str(plugin_params.get("model", "nano banana 2"))
    aspect_ratio = str(plugin_params.get("aspect_ratio", "16:9"))
    image_size = str(plugin_params.get("image_size", "2K"))
    request_timeout = int(plugin_params.get("request_timeout", 300))
    download_timeout = int(plugin_params.get("download_timeout", 300))

    if model_display not in MODEL_NAME_MAP:
        model_display = "nano banana 2"
    model = MODEL_NAME_MAP[model_display]

    # 构造 endpoint（zlhub 固定根路径，具体接口路径由请求函数补齐）
    normalized_base = _normalize_base_url(base_url)
    endpoint = normalized_base

    # 日志摘要
    _log(f"\n===== 生成参数 =====")
    _log(f"正向提示词:   {prompt}")
    _log(f"参考图片数量: {len(reference_images)}")
    _log(
        f"API Key:      {'已设置 (' + str(len(api_key)) + ' 字符)' if api_key else '未设置'}"
    )
    _log(f"Base URL:     {base_url}")
    _log(f"Endpoint:     {endpoint}")
    _log(
        f"模型:         {model_display}"
        + (f" -> {model}" if model != model_display else "")
    )
    _log(f"图片比例:     {aspect_ratio}")
    _log(f"图片尺寸:     {image_size}")
    _log(f"请求超时:     {request_timeout} 秒")
    _log(f"下载超时:     {download_timeout} 秒")
    _log(f"==================\n")

    # 前置校验
    if not api_key.strip():
        _log("错误: 未设置 API Key，请在插件设置中填写")
        return []
    if not endpoint.strip():
        _log("错误: 未设置 Endpoint")
        return []

    os.makedirs(output_dir, exist_ok=True)

    # 初始化任务日志
    task_log_context = {
        "model_display": model_display,
        "model_name": model,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "image_size": image_size,
        "reference_images": reference_images.copy()
        if isinstance(reference_images, dict)
        else reference_images,
        "base_url": base_url,
        "endpoint": endpoint,
        "task_mode": "图生图" if reference_images else "文生图",
        "metadata": {
            "request_timeout": request_timeout,
            "download_timeout": download_timeout,
            "viewer_index": viewer_index,
            "source": "zlhub",
        },
    }
    task_log_id = _log_task_result(task_log_context, status="running")

    # 调用 API
    clean_endpoint = endpoint.strip().rstrip("/")

    api_name = "zlhub Chat Completions API"
    _log(f"正在调用 {api_name}...")

    common_kwargs = dict(
        api_key=api_key,
        endpoint=clean_endpoint,
        model=model,
        prompt=prompt,
        reference_images=reference_images,
        aspect_ratio=aspect_ratio,
        request_timeout=request_timeout,
        download_timeout=download_timeout,
    )

    try:
        image_data_base64, image_source_url = send_zlhub_image_request(
            **common_kwargs, image_size=image_size
        )
    except Exception as e:
        error_msg = f"API 调用失败: {e}"
        _log(f"{error_msg}")
        import traceback

        traceback.print_exc()
        _log_task_result(
            task_log_context,
            status="failed",
            error=error_msg,
            log_id=task_log_id,
            completed=True,
        )
        raise Exception(f"PLUGIN_ERROR:::{error_msg}")

    # 处理返回结果
    generated_files = []

    def _save_image(image_data: bytes, suffix: str = "") -> str:
        """将原始字节保存为 PNG，返回本地路径。"""
        img = Image.open(BytesIO(image_data))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{viewer_index:04d}_image_{timestamp}{suffix}.png"
        path = str(Path(output_dir) / filename)
        img.save(path, "PNG")
        return path

    if image_data_base64:
        # API 直接返回 base64
        try:
            output_path = _save_image(base64.b64decode(image_data_base64))
            generated_files.append(output_path)
            _log_task_result(
                task_log_context,
                status="success",
                image_url=image_source_url,
                local_path=output_path,
                log_id=task_log_id,
                completed=True,
            )
            _log(f"✓ 图片保存成功: {output_path}")
        except Exception as e:
            error_msg = f"图片保存失败: {e}"
            _log(f"{error_msg}")
            _log("   提示: API 已返回数据，但保存到本地失败")
            _log_task_result(
                task_log_context,
                status="download_failed",
                image_url=image_source_url,
                error=error_msg,
                log_id=task_log_id,
                completed=True,
            )

    elif image_source_url:
        # ─API 返回 URL（单个或列表）
        url_list = (
            image_source_url
            if isinstance(image_source_url, list)
            else [image_source_url]
        )
        _log(f"图片生成成功，共 {len(url_list)} 张图片")

        for idx, url in enumerate(url_list):
            _log(f"处理第 {idx + 1}/{len(url_list)} 张图片: {url}")
            log_id = task_log_id if idx == 0 else None
            suffix = f"_n{idx + 1}" if len(url_list) > 1 else ""

            _log_task_result(
                task_log_context,
                status="generated",
                image_url=url,
                log_id=log_id,
                completed=False,
            )
            try:
                raw = base64.b64decode(_download_image_from_url(url, download_timeout))
                output_path = _save_image(raw, suffix)
                generated_files.append(output_path)
                _log_task_result(
                    task_log_context,
                    status="success",
                    local_path=output_path,
                    log_id=log_id,
                    completed=True,
                )
                _log(f"✓ 图片 {idx + 1} 下载成功: {output_path}")
            except ImageDownloadError as e:
                error_msg = f"图片 {idx + 1} 下载失败: {e}"
                _log(f"{error_msg}")
                _log("   提示：图片已生成，可通过「任务日志/手动拉图」功能稍后下载")
                _log_task_result(
                    task_log_context,
                    status="download_failed",
                    error=str(e),
                    log_id=log_id,
                    completed=True,
                )

        if not generated_files:
            error_msg = "所有图片下载失败"
            _log(error_msg)
            _log_task_result(
                task_log_context,
                status="failed",
                error=error_msg,
                log_id=task_log_id,
                completed=True,
            )
            raise Exception(f"PLUGIN_ERROR:::{error_msg}")
    else:
        error_msg = "API 响应中未包含图片数据"
        _log(f"{error_msg}")
        _log_task_result(
            task_log_context,
            status="failed",
            error=error_msg,
            log_id=task_log_id,
            completed=True,
        )
        raise Exception(f"PLUGIN_ERROR:::{error_msg}")

    _log("\n" + "=" * 60)
    _log(f"Nano Banana zlhub 插件完成，共生成 {len(generated_files)} 张图片")
    _log("=" * 60 + "\n")

    return generated_files


# --------------------- generate ---------------------

# 保存插件文件路径，用于配置管理
_PLUGIN_FILE = __file__
_PLUGIN_ID = "image_plugin_zlhub_nano_banana"
_PLUGIN_VERSION = "1.0.2"

plugin_dir = Path(__file__).parent

# 可选的 API Base URL 选项（供用户切换不同线路）
_BASE_URL_OPTIONS = [("zlhub", "http://zlhub.xiaowaiyou.cn")]

_DEFAULT_BASE_URL = _BASE_URL_OPTIONS[0][1]

_VALID_BASE_URLS = {_normalize_base_url(url) for _, url in _BASE_URL_OPTIONS}

_TASK_LOG_DB_PATH = plugin_dir / "image_task_logs.db"

_log_buffer = collections.deque(maxlen=1000)
_log_index = 0
_log_lock = threading.Lock()
_logger = _setup_logging()

_default_params = {
    "api_key": "",
    "base_url": _DEFAULT_BASE_URL,
    "model": "nano banana 2",
    "aspect_ratio": "16:9",
    "image_size": "2K",
    "request_timeout": 60000,
    "download_timeout": 60000,
    "retry_count": 0,
}

# 模型列表(显示名称)
AVAILABLE_MODELS = [
    "nano banana 2",
    "doubao-seedream-4.5",
]

# 显示名称到 API 模型名称的映射
MODEL_NAME_MAP = {
    "nano banana 2": "nano banana 2",
    "doubao-seedream-4.5": "doubao-seedream-4.5",
}

# Doubao 模型的宽高比到尺寸映射
DOUBAO_SIZE_MAP = {
    "1:1": "2048x2048",
    "4:3": "2304x1728",
    "3:4": "1728x2304",
    "16:9": "2560x1440",
    "9:16": "1440x2560",
    "3:2": "2496x1664",
    "2:3": "1664x2496",
    "21:9": "3024x1296",
}

# Grok 模型的宽高比到尺寸映射
GROK_SIZE_MAP = {
    "1:1": "2048x2048",
    "4:3": "2304x1728",
    "3:4": "1728x2304",
    "16:9": "2560x1440",
    "9:16": "1440x2560",
    "3:2": "2496x1664",
    "2:3": "1664x2496",
    "21:9": "3024x1296",
}

# 图片比例列表
ASPECT_RATIOS = [
    "1:1",
    "16:9",
    "9:16",
    "4:3",
    "3:4",
]

_init_task_log_db()

_init_params = _default_params.copy()
_init_params.update(load_plugin_config(_PLUGIN_FILE))
_init_params["base_url"] = _get_valid_base_url(
    _init_params.get("base_url") or _init_params.get("endpoint") or _DEFAULT_BASE_URL
)
print(
    f"[Nano Banana GeekNow] 插件初始化完成，API Key: {'已设置(' + str(len(_init_params.get('api_key', ''))) + '字符)' if _init_params.get('api_key') else '未设置'}, Base URL: {_get_valid_base_url(_init_params.get('base_url', _DEFAULT_BASE_URL))}"
)
