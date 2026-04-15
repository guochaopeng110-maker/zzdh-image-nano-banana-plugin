# Technology Stack

**Analysis Date:** 2026-04-15

## Languages

**Primary:**
- Python (CPython 3.12 inferred from `nano_banana_plugin_geeknow/__pycache__/main.cpython-312.pyc`) for plugin runtime logic in `nano_banana_plugin_geeknow/main.py`.

**Secondary:**
- HTML/CSS/JavaScript for plugin configuration and monitoring UI in `nano_banana_plugin_geeknow/ui/index.html`, `nano_banana_plugin_geeknow/ui/task_log.html`, and `nano_banana_plugin_geeknow/ui/live_log.html`.
- JSON for plugin metadata/config in `nano_banana_plugin_geeknow/info.json` and persisted plugin params via host config.
- Markdown for integration reference docs in `docs/require/zlhub-chat-image-api.md`.

## Runtime

**Environment:**
- Host plugin engine runtime (plugin contract exposes `get_info()`, `generate(context)`, `handle_action(action, data)` in `nano_banana_plugin_geeknow/main.py`).
- Python standard library is heavily used (`sqlite3`, `threading`, `logging`, `tempfile`, `zipfile`, `hashlib`, `pathlib`, `urllib.parse`).

**Package Manager:**
- No Python package manifest found (`requirements.txt`, `pyproject.toml`, `Pipfile` absent).
- JavaScript package manifests exist only in tooling folders (`.claude/package.json`, `.agent/package.json`, `.gemini/package.json`) and contain minimal metadata (`{"type":"commonjs"}`).

## Frameworks

**Core:**
- No web framework (plugin-style single module architecture in `nano_banana_plugin_geeknow/main.py`).
- Host-provided Plugin SDK bridge on frontend (`../../../plugin-sdk.js` loaded in `nano_banana_plugin_geeknow/ui/index.html`).

**Data & IO:**
- Built-in SQLite persistence through `sqlite3` in `nano_banana_plugin_geeknow/main.py`.
- Image processing through Pillow (`from PIL import Image`) in `nano_banana_plugin_geeknow/main.py`.
- HTTP integration through `requests` in `nano_banana_plugin_geeknow/main.py`.

## Key Dependencies

**Critical:**
- `requests` — external HTTP calls to model APIs, update manifest, image upload/download.
- `Pillow` (`PIL.Image`) — image decode/encode and PNG saving pipeline.
- `sqlite3` (stdlib) — task logging and manual download state tracking in local DB.
- `plugin_utils.load_plugin_config` — loads host-side plugin config for runtime parameters.

**Infrastructure:**
- Python stdlib logging + custom buffering handler for live logs (`_BufferingHandler` in `nano_banana_plugin_geeknow/main.py`).
- Local filesystem as working storage (`manual_downloads/`, generated output directory from `context['output_dir']`).

## Configuration

**Environment / Runtime Params:**
- Plugin params are user-configurable in `nano_banana_plugin_geeknow/ui/index.html` and consumed in `generate(context)` (`api_key`, `base_url`, `model`, `aspect_ratio`, `image_size`, timeouts, retry count).
- Plugin metadata is defined in `nano_banana_plugin_geeknow/info.json` and returned via `get_info()`.

**Build / Packaging:**
- No explicit build pipeline found for plugin runtime code.
- UI assets are static HTML pages loaded by host plugin runtime.

## Platform Requirements

**Development:**
- Python runtime with `requests` and `Pillow` available.
- Host application/plugin engine that loads this plugin contract and serves the UI pages.

**Production / Deployment:**
- Local plugin deployment model (code and UI files live under `nano_banana_plugin_geeknow/`).
- External API connectivity required for image generation flows.

---

*Stack analysis: 2026-04-15*
*Update after dependency/runtime contract changes*
