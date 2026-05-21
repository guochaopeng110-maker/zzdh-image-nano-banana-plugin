# -*- coding: utf-8 -*-
"""WebAI image relay plugin."""

import base64
import json
import logging
import os
import re
import sys
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


def _log(msg, level="INFO"):
    getattr(_logger, level.lower(), _logger.info)(msg)


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

    content_parts = [{"type": "text", "text": prompt}]
    for _, img_path in (reference_images or {}).items():
        if not os.path.exists(img_path) or os.path.getsize(img_path) <= 0:
            continue
        with open(img_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        content_parts.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_data}"},
            }
        )

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

    response = requests.post(url, json=payload, headers=headers, timeout=request_timeout, stream=bool(stream))
    if response.status_code != 200:
        raise Exception(f"HTTP {response.status_code}: {response.text}")

    if stream:
        images = _extract_stream_chunks_base64(response)
    else:
        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise Exception("NO_RETRY:::API response has no choices")
        msg = choices[0].get("message") or {}
        images = _extract_base64_images_from_text(msg.get("content"))

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
    if action == "open_live_logs":
        return {"ok": True, "open_page": "live_log.html"}
    if action == "open_task_logs":
        return {"ok": True, "open_page": "task_log.html"}
    if action == "get_task_logs":
        return {"ok": True, "logs": []}
    if action == "download_images":
        return {"ok": True, "results": []}
    if action == "get_logs":
        return {"ok": True, "logs": []}
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
    except Exception as e:
        raise Exception(f"PLUGIN_ERROR:::{e}")

    generated_files = []
    image_list = image_data_base64 if isinstance(image_data_base64, list) else [image_data_base64]
    for idx, b64_image in enumerate(image_list):
        img = Image.open(BytesIO(base64.b64decode(b64_image)))
        img.load()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        suffix = f"_n{idx+1}" if len(image_list) > 1 else ""
        filename = f"{viewer_index:04d}_image_{timestamp}{suffix}.png"
        path = str(Path(output_dir) / filename)
        img.save(path, "PNG")
        generated_files.append(path)

    if not generated_files:
        raise Exception("PLUGIN_ERROR:::all images failed to save")

    return generated_files


_init_params = _default_params.copy()
_init_params.update(load_plugin_config(_PLUGIN_FILE))
