# External Integrations

**Analysis Date:** 2026-04-15

## APIs & External Services

**Image Generation API Gateway (GeekNow endpoints):**
- Service role: Primary model gateway for Gemini/Doubao/Grok image generation requests from `nano_banana_plugin_geeknow/main.py`.
- Base nodes configured in code/UI:
  - `https://www.geeknow.top`
  - `https://api.geeknow.top`
  - `https://geek.closeai.icu`
- Auth: Bearer token from plugin param `api_key` (`Authorization: Bearer <token>`).
- Endpoint patterns:
  - Gemini-style: `{base_url}/v1beta/models/{model}:generateContent`
  - OpenAI-compatible image API for Grok/Doubao: `{base_url}/v1/images/generations`

**Update Manifest Service:**
- `https://chrome.geeknow.top/manifest.json` in `nano_banana_plugin_geeknow/ui/index.html`.
- Used by `handle_action('check_update')` → `_check_update_available()` in `nano_banana_plugin_geeknow/main.py`.
- Expected schema includes `plugins[]`, `plugin_id`, `version`, `download_url`, `sha256`.

**Image Upload Proxy (reference image hosting):**
- `https://imageproxy.zhongzhuan.chat/api/upload` in `upload_image_to_host()` (`nano_banana_plugin_geeknow/main.py`).
- Used by Grok/Doubao flows to upload local reference images and switch from base64 payload to URL payload when possible.
- Auth: None observed in code (multipart file upload).

**Reference Documentation API:**
- `docs/require/zlhub-chat-image-api.md` documents another external proxy endpoint: `http://zlhub.xiaowaiyou.cn/zhonglian/api/v1/proxy/chat/completions`.
- This appears to be integration/reference documentation and is not directly invoked in current plugin runtime code.

## Data Storage

**Databases:**
- Local SQLite database `nano_banana_plugin_geeknow/image_task_logs.db`.
- Access layer in `nano_banana_plugin_geeknow/main.py` via `_init_task_log_db()`, `_insert_task_log_entry()`, `_update_task_log_entry()`, `_fetch_task_logs()`.
- Stores generation metadata, status, URLs, local paths, errors, and timestamps.

**File Storage:**
- Local output directories:
  - Generation output: runtime `context['output_dir']` in `generate()`.
  - Manual re-download output: `nano_banana_plugin_geeknow/manual_downloads/` via `download_images_from_logs()`.
- Temporary update extraction/install workspace uses system temp directories via `tempfile.mkdtemp()`.

## Authentication & Identity

**Provider model:**
- API key-based auth only (no OAuth/session flow).
- Secret source: plugin UI parameter `api_key` persisted by host plugin config.
- Requests use `Authorization: Bearer {api_key}` in generation calls.

## Monitoring & Observability

**Plugin-local logging:**
- Console + in-memory buffered logs (`_log_buffer`) in `nano_banana_plugin_geeknow/main.py`.
- UI polling endpoint through `handle_action('get_logs')` consumed by `nano_banana_plugin_geeknow/ui/live_log.html`.

**Task status tracking:**
- SQLite-backed operational logs rendered in `nano_banana_plugin_geeknow/ui/task_log.html`.

## Environment Configuration

**Development/Runtime keys (as plugin params):**
- `api_key`
- `base_url`
- `model`
- `aspect_ratio`
- `image_size`
- `request_timeout`
- `download_timeout`
- `retry_count`
- `update_manifest_url` (UI writes fixed manifest URL)

**Secret handling pattern:**
- Secret value originates from UI input and is persisted by host plugin config.
- Code logs mask some auth output (`Authorization=Bearer ***`), but there is at least one raw API key log path in `send_gemini_request` (see concerns).

## Webhooks & Callbacks

**Incoming webhooks:**
- None observed.

**Outgoing callbacks:**
- None observed; communication is synchronous request/response HTTP polling style.

---

*Integration audit: 2026-04-15*
*Update when adding/removing third-party services or auth paths*
