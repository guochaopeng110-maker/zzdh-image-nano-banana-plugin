<!-- GSD:project-start source:PROJECT.md -->
## Project

**image_plugin_zlhub_nano_banana**
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python (CPython 3.12 inferred from `nano_banana_plugin_geeknow/__pycache__/main.cpython-312.pyc`) for plugin runtime logic in `nano_banana_plugin_geeknow/main.py`.
- HTML/CSS/JavaScript for plugin configuration and monitoring UI in `nano_banana_plugin_geeknow/ui/index.html`, `nano_banana_plugin_geeknow/ui/task_log.html`, and `nano_banana_plugin_geeknow/ui/live_log.html`.
- JSON for plugin metadata/config in `nano_banana_plugin_geeknow/info.json` and persisted plugin params via host config.
- Markdown for integration reference docs in `docs/require/zlhub-chat-image-api.md`.
## Runtime
- Host plugin engine runtime (plugin contract exposes `get_info()`, `generate(context)`, `handle_action(action, data)` in `nano_banana_plugin_geeknow/main.py`).
- Python standard library is heavily used (`sqlite3`, `threading`, `logging`, `tempfile`, `zipfile`, `hashlib`, `pathlib`, `urllib.parse`).
- No Python package manifest found (`requirements.txt`, `pyproject.toml`, `Pipfile` absent).
- JavaScript package manifests exist only in tooling folders (`.claude/package.json`, `.agent/package.json`, `.gemini/package.json`) and contain minimal metadata (`{"type":"commonjs"}`).
## Frameworks
- No web framework (plugin-style single module architecture in `nano_banana_plugin_geeknow/main.py`).
- Host-provided Plugin SDK bridge on frontend (`../../../plugin-sdk.js` loaded in `nano_banana_plugin_geeknow/ui/index.html`).
- Built-in SQLite persistence through `sqlite3` in `nano_banana_plugin_geeknow/main.py`.
- Image processing through Pillow (`from PIL import Image`) in `nano_banana_plugin_geeknow/main.py`.
- HTTP integration through `requests` in `nano_banana_plugin_geeknow/main.py`.
## Key Dependencies
- `requests` — external HTTP calls to model APIs, update manifest, image upload/download.
- `Pillow` (`PIL.Image`) — image decode/encode and PNG saving pipeline.
- `sqlite3` (stdlib) — task logging and manual download state tracking in local DB.
- `plugin_utils.load_plugin_config` — loads host-side plugin config for runtime parameters.
- Python stdlib logging + custom buffering handler for live logs (`_BufferingHandler` in `nano_banana_plugin_geeknow/main.py`).
- Local filesystem as working storage (`manual_downloads/`, generated output directory from `context['output_dir']`).
## Configuration
- Plugin params are user-configurable in `nano_banana_plugin_geeknow/ui/index.html` and consumed in `generate(context)` (`api_key`, `base_url`, `model`, `aspect_ratio`, `image_size`, timeouts, retry count).
- Plugin metadata is defined in `nano_banana_plugin_geeknow/info.json` and returned via `get_info()`.
- No explicit build pipeline found for plugin runtime code.
- UI assets are static HTML pages loaded by host plugin runtime.
## Platform Requirements
- Python runtime with `requests` and `Pillow` available.
- Host application/plugin engine that loads this plugin contract and serves the UI pages.
- Local plugin deployment model (code and UI files live under `nano_banana_plugin_geeknow/`).
- External API connectivity required for image generation flows.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- Plugin runtime entry is a single module file: `main.py`.
- UI pages use lowercase snake/word style names: `index.html`, `task_log.html`, `live_log.html`.
- Documentation filenames use descriptive kebab-case (`docs/require/zlhub-chat-image-api.md`).
- Internal helper functions prefer leading underscore + snake_case, e.g., `_normalize_base_url`, `_fetch_task_logs`, `_download_image_from_url` in `nano_banana_plugin_geeknow/main.py`.
- Public/contract functions use plain snake_case without underscore: `get_info`, `handle_action`, `generate`.
- Provider functions follow `send_<provider>_request` naming (`send_grok_request`, `send_doubao_request`, `send_gemini_request`).
- Local variables are snake_case (`request_timeout`, `image_source_url`, `task_log_context`).
- Module-level constants are UPPER_SNAKE_CASE (`_PLUGIN_ID`, `_DEFAULT_BASE_URL`, `MODEL_NAME_MAP`).
- “Private” module globals conventionally use underscore prefix (`_logger`, `_log_buffer`, `_init_params`).
## Code Style
- 4-space indentation in Python.
- Heavy use of section dividers and Chinese doc/comments for readability.
- Mix of f-strings and plain strings.
- Long lines are present in logging/debug sections (line-length not strictly enforced).
- Vanilla JS in `<script>` blocks (no framework/toolchain).
- DOM references cached into `var` variables at top-level.
- Event listeners defined inline via `addEventListener`.
## Import Organization
- Blank lines separate import groups.
- Import sorting is mostly logical/manual, not strictly alphabetical.
## Error Handling
- Broad `try/except Exception` is the dominant pattern across network, file, and DB operations.
- API/provider functions raise exceptions with prefixed sentinel strings (`NO_RETRY:::`, `PLUGIN_ERROR:::`) to signal behavior upstream.
- UI action methods return structured `{ok: False, error: ...}` objects rather than throwing in many branches.
- A custom exception class exists for image download (`ImageDownloadError`), but most other failures use generic `Exception`.
- Update flow includes rollback semantics (`_install_main_py`) on failed install copy.
## Logging
- Python `logging` with custom buffered handler in `nano_banana_plugin_geeknow/main.py`.
- `_log()` wrapper centralizes level usage (`INFO`, `WARNING`, `ERROR`, `DEBUG`).
- Frequent operational logs around API calls, parameters, and status transitions.
- Task events are duplicated in structured SQLite task log state (`_log_task_result`).
- Live-log UI polls buffered logs every 2s (`nano_banana_plugin_geeknow/ui/live_log.html`).
## Comments & Documentation
- Section banners divide major functional blocks (updates, SQLite logs, plugin required functions, generation path).
- Inline comments explain branch decisions (e.g., URL vs base64 fallback for reference images).
- User-facing Chinese labels/messages are embedded in logs and UI for direct operator visibility.
- Most top-level functions include concise Chinese docstrings describing args/returns.
- Docstring thoroughness varies by function.
## Function Design
- Single-file functional style with many helpers and minimal class abstraction (except logging handler + custom exception).
- `generate()` is the orchestration-heavy function coordinating validation, routing, persistence, networking, and file output.
- Provider adapters return tuples `(image_data_base64, image_url_or_urls)`.
- Action handlers consistently return dict payloads for UI consumption.
- `generate()` returns list of generated file paths.
## Module Design
- Monolithic module design with grouped sections rather than multi-module package decomposition.
- Module-level constants hold provider/model/base URL maps and defaults.
- New providers are added by introducing another `send_*_request` helper and extending model routing in `generate()`.
- UI extension follows adding controls in `ui/index.html` + wiring read path in `generate()`.
## Deviations / Legacy Notes
- A `retry_count` parameter is present in UI/default params but does not currently influence request retry behavior in `generate()` path.
- Some logging paths sanitize secrets, but there is inconsistent masking discipline in one provider function (covered in concerns).
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Single Python module (`nano_banana_plugin_geeknow/main.py`) contains integration, persistence, update, logging, and generation orchestration logic.
- Host-driven plugin contract (`get_info`, `generate`, `handle_action`) defines execution boundaries.
- UI pages are static HTML files that communicate with host/runtime bridge via message passing and Plugin SDK actions.
- Local-first operational state via SQLite + filesystem.
## Layers
- Purpose: Provide host-required entry points and action dispatch.
- Contains: `get_info()`, `generate(context)`, `handle_action(action, data)` in `nano_banana_plugin_geeknow/main.py`.
- Depends on: Service and utility functions in same module.
- Used by: Host plugin engine.
- Purpose: Adapt runtime params + inputs into provider-specific HTTP requests.
- Contains: `send_gemini_request()`, `send_doubao_request()`, `send_grok_request()`.
- Depends on: `requests`, image utility functions, upload/download helpers.
- Used by: `generate(context)`.
- Purpose: Record lifecycle of generation/download tasks for UI observability and manual recovery.
- Contains: SQLite init/query/update helpers and `_log_task_result()`.
- Depends on: `sqlite3`, JSON serialization helpers.
- Used by: `generate()`, `handle_action('get_task_logs')`, `handle_action('download_images')`.
- Purpose: Cross-cutting helpers for URL normalization, image conversion, file operations, logging, update flow.
- Contains: `_normalize_base_url`, `_get_valid_base_url`, `image_to_base64`, `_download_image_from_url`, `upload_image_to_host`, update functions.
- Depends on: stdlib + external libs.
- Used by: Gateway and contract layers.
- Purpose: Configure plugin params and expose task/log controls.
- Contains: static pages `nano_banana_plugin_geeknow/ui/index.html`, `ui/task_log.html`, `ui/live_log.html`.
- Depends on: `plugin-sdk.js` and host window messaging bridge.
- Used by: End-user via host app plugin panel/popup windows.
## Data Flow
- Persistent state: SQLite DB (`image_task_logs.db`) + host plugin config values.
- Ephemeral state: in-memory log buffer (`_log_buffer`) and transient temp directories for updates.
## Key Abstractions
- Purpose: Route one plugin UX to multiple backend APIs.
- Examples: model prefix checks in `generate()` (`grok-`, `doubao-`, default Gemini).
- Pattern: Conditional strategy dispatch.
- Purpose: Normalize operational statuses across generation and manual download.
- Examples: statuses `running`, `generated`, `success`, `download_failed`, `manual_success`, `failed`.
- Pattern: Append/update lifecycle rows in SQLite.
- Purpose: Handle many UI commands via one host callback.
- Examples: `open_task_logs`, `get_task_logs`, `download_images`, `get_logs`, `check_update`, `do_update`.
- Pattern: String-based command dispatch inside `handle_action()`.
## Entry Points
- Location: `nano_banana_plugin_geeknow/main.py:get_info()`.
- Trigger: Host plugin discovery/metadata render.
- Location: `nano_banana_plugin_geeknow/main.py:generate(context)`.
- Trigger: User starts image generation in host app.
- Location: `nano_banana_plugin_geeknow/main.py:handle_action(action, data)`.
- Trigger: UI pages invoke plugin actions.
- `nano_banana_plugin_geeknow/ui/index.html` (main config panel)
- `nano_banana_plugin_geeknow/ui/task_log.html` (task table + manual download)
- `nano_banana_plugin_geeknow/ui/live_log.html` (polling live logs)
## Error Handling
- Mostly exception-driven, with action handlers returning `{ok: False, error: ...}` on UI paths.
- Generation path raises host-parseable exceptions with prefixes (e.g., `PLUGIN_ERROR:::` and `NO_RETRY:::` patterns).
- HTTP status checks before response parsing in provider/update helpers.
- Broad `except Exception` blocks are common across IO/network/database layers.
- Update installer includes rollback on copy failure (`_install_main_py`).
## Cross-Cutting Concerns
- Standard logger created in `_setup_logging()` with console handler + in-memory buffering handler.
- `_log()` wrapper keeps older callsites consistent.
- Input validation is mostly lightweight (presence checks, URL base normalization, supported base URL whitelist, response shape checks).
- Uses bearer token auth for external model calls.
- Update channel supports optional SHA256 verification before install.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
