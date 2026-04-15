# Phase 2: zlhub 出图主链路闭环 - Pattern Map

**Mapped:** 2026-04-15
**Files analyzed:** 1
**Analogs found:** 1 / 1

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `image_plugin_zlhub_nano_banana/main.py` | service (plugin runtime orchestrator) | request-response + file-I/O + CRUD(status log) | `nano_banana_plugin_geeknow/main.py` | exact |

## Pattern Assignments

### `image_plugin_zlhub_nano_banana/main.py` (service, request-response + file-I/O)

**Analog:** `nano_banana_plugin_geeknow/main.py`

**Imports pattern** (lines 6-29):
```python
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
```

**Core orchestration pattern (`generate`)** (lines 1249-1274, 1330-1349):
```python
prompt = context.get('prompt', '')
reference_images = context.get('reference_images', {})
output_dir = context.get('output_dir', '')
plugin_params = context.get('plugin_params', {}) or {}
viewer_index = context.get('viewer_index', 0)

api_key = str(plugin_params.get('api_key', ''))
base_url = _get_valid_base_url(
    plugin_params.get('base_url')
    or plugin_params.get('endpoint')
    or _init_params.get('base_url')
)
...
model = MODEL_NAME_MAP.get(model_display, model_display)

normalized_base = _normalize_base_url(base_url)
is_doubao_model = model.startswith('doubao-') or model.startswith('grok-')
endpoint = normalized_base if is_doubao_model else f"{normalized_base}/v1beta"
...
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

if model.startswith('grok-'):
    image_data_base64, image_source_url = send_grok_request(**common_kwargs)
elif model.startswith('doubao-'):
    image_data_base64, image_source_url = send_doubao_request(**common_kwargs)
else:
    image_data_base64, image_source_url = send_gemini_request(
        **common_kwargs, image_size=image_size
    )
```

**Request payload template pattern (OpenAI-compatible provider path)** (lines 792-809, 923-939):
```python
url = f"{endpoint}/v1/images/generations"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

payload = {
    "model": model,
    "prompt": prompt,
    "n": 1,
    "size": size
}

if image_list:
    payload["image"] = image_list
```

**Response parse pattern (`data[].url` / `b64_json`)** (lines 833-855, 963-980):
```python
if 'data' not in data or len(data['data']) == 0:
    raise Exception("NO_RETRY:::API 未返回有效结果")

image_urls = []
for idx, image_result in enumerate(data['data']):
    if 'url' in image_result and image_result['url']:
        image_urls.append(image_result['url'])

if not image_urls:
    raise Exception("NO_RETRY:::API 响应中未包含任何图片 URL")

return None, image_urls[0] if len(image_urls) == 1 else image_urls
```

```python
image_result = data['data'][0]
if 'b64_json' in image_result and image_result['b64_json']:
    return image_result['b64_json'], image_result.get('url')
if 'url' in image_result and image_result['url']:
    return None, image_result['url']
raise Exception("NO_RETRY:::API 响应中未包含图片数据")
```

**Download + save-to-disk pattern (single and multi-image)** (lines 1362-1413):
```python
def _save_image(image_data: bytes, suffix: str = '') -> str:
    img = Image.open(BytesIO(image_data))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{viewer_index:04d}_image_{timestamp}{suffix}.png"
    path = str(Path(output_dir) / filename)
    img.save(path, 'PNG')
    return path

...
url_list = image_source_url if isinstance(image_source_url, list) else [image_source_url]
for idx, url in enumerate(url_list):
    suffix = f"_n{idx + 1}" if len(url_list) > 1 else ''
    raw = base64.b64decode(_download_image_from_url(url, download_timeout))
    output_path = _save_image(raw, suffix)
    generated_files.append(output_path)
```

**Error handling pattern (host-visible prefixed errors + task log updates)** (lines 1350-1357, 1414-1418):
```python
except Exception as e:
    error_msg = f"API 调用失败: {e}"
    _log_task_result(task_log_context, status='failed', error=error_msg,
                     log_id=task_log_id, completed=True)
    raise Exception(f"PLUGIN_ERROR:::{error_msg}")
```

```python
if 'data' not in data or len(data['data']) == 0:
    raise Exception("NO_RETRY:::API 未返回有效结果")
```

```python
else:
    error_msg = "API 响应中未包含图片数据"
    _log_task_result(task_log_context, status='failed', error=error_msg,
                     log_id=task_log_id, completed=True)
    raise Exception(f"PLUGIN_ERROR:::{error_msg}")
```

**Validation pattern (lightweight guard clauses)** (lines 1289-1295):
```python
if not api_key.strip():
    _log("错误: 未设置 API Key，请在插件设置中填写")
    return []
if not endpoint.strip():
    _log("错误: 未设置 Endpoint")
    return []
```

**Task logging lifecycle pattern** (lines 1300-1322, 563-600):
```python
task_log_context = {
    'model_display': model_display,
    'model_name': model,
    'prompt': prompt,
    ...
    'task_mode': '图生图' if reference_images else '文生图',
    'metadata': {
        'request_timeout': request_timeout,
        'download_timeout': download_timeout,
        'viewer_index': viewer_index,
        'source': (...),
    }
}
task_log_id = _log_task_result(task_log_context, status='running')
```

```python
if log_id:
    _update_task_log_entry(log_id, **{k: v for k, v in update_fields.items() if v is not None})
    return log_id
...
log_id = _insert_task_log_entry(entry)
return log_id
```

**Testing pattern:** No dedicated test files found for plugin runtime module; planner should treat runtime verification as manual/host-integrated validation.

---

## Shared Patterns

### Authentication (Bearer)
**Source:** `nano_banana_plugin_geeknow/main.py` (lines 794-797, 924-927, 1036-1039)
**Apply to:** All external API provider calls in `main.py`
```python
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}
```

### Error Prefix Contract
**Source:** `nano_banana_plugin_geeknow/main.py` (lines 835-836, 850-851, 1350-1357, 1414-1418)
**Apply to:** Provider parse failures and top-level generate failures
```python
raise Exception("NO_RETRY:::API 未返回有效结果")
...
raise Exception(f"PLUGIN_ERROR:::{error_msg}")
```

### Request/Download Status Lifecycle (SQLite)
**Source:** `nano_banana_plugin_geeknow/main.py` (lines 563-600, 1398-1412)
**Apply to:** Main generation pipeline and fallback manual download flow
```python
_log_task_result(task_log_context, status='generated', image_url=url, ...)
...
_log_task_result(task_log_context, status='success', local_path=output_path, ...)
...
_log_task_result(task_log_context, status='download_failed', error=str(e), ...)
```

### URL Download Robustness
**Source:** `nano_banana_plugin_geeknow/main.py` (lines 1143-1189)
**Apply to:** Any URL-to-local image persistence in main chain
```python
img_response = requests.get(image_url, headers=download_headers, timeout=download_timeout, stream=True)
if img_response.status_code == 200:
    return base64.b64encode(img_response.content).decode('utf-8')
raise ImageDownloadError(error_msg, image_url)
```

## No Analog Found

None.

## Metadata

**Analog search scope:**
- `F:/Projects/zz-image-plugins/image_plugin_zlhub_nano_banana/`
- `F:/Projects/zz-image-plugins/nano_banana_plugin_geeknow/`
- `F:/Projects/zz-image-plugins/.planning/phases/02-zlhub/`

**Files scanned:** 4
- `F:/Projects/zz-image-plugins/.planning/phases/02-zlhub/02-CONTEXT.md`
- `F:/Projects/zz-image-plugins/CLAUDE.md`
- `F:/Projects/zz-image-plugins/image_plugin_zlhub_nano_banana/main.py`
- `F:/Projects/zz-image-plugins/nano_banana_plugin_geeknow/main.py`

**Pattern extraction date:** 2026-04-15
