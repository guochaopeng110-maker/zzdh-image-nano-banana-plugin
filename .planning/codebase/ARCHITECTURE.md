# Architecture

**Analysis Date:** 2026-04-15

## Pattern Overview

**Overall:** Monolithic plugin module with embedded static UI panels.

**Key Characteristics:**
- Single Python module (`nano_banana_plugin_geeknow/main.py`) contains integration, persistence, update, logging, and generation orchestration logic.
- Host-driven plugin contract (`get_info`, `generate`, `handle_action`) defines execution boundaries.
- UI pages are static HTML files that communicate with host/runtime bridge via message passing and Plugin SDK actions.
- Local-first operational state via SQLite + filesystem.

## Layers

**Plugin Contract Layer:**
- Purpose: Provide host-required entry points and action dispatch.
- Contains: `get_info()`, `generate(context)`, `handle_action(action, data)` in `nano_banana_plugin_geeknow/main.py`.
- Depends on: Service and utility functions in same module.
- Used by: Host plugin engine.

**Model Gateway Layer:**
- Purpose: Adapt runtime params + inputs into provider-specific HTTP requests.
- Contains: `send_gemini_request()`, `send_doubao_request()`, `send_grok_request()`.
- Depends on: `requests`, image utility functions, upload/download helpers.
- Used by: `generate(context)`.

**Persistence & Task Tracking Layer:**
- Purpose: Record lifecycle of generation/download tasks for UI observability and manual recovery.
- Contains: SQLite init/query/update helpers and `_log_task_result()`.
- Depends on: `sqlite3`, JSON serialization helpers.
- Used by: `generate()`, `handle_action('get_task_logs')`, `handle_action('download_images')`.

**Operational Utilities Layer:**
- Purpose: Cross-cutting helpers for URL normalization, image conversion, file operations, logging, update flow.
- Contains: `_normalize_base_url`, `_get_valid_base_url`, `image_to_base64`, `_download_image_from_url`, `upload_image_to_host`, update functions.
- Depends on: stdlib + external libs.
- Used by: Gateway and contract layers.

**UI Interaction Layer:**
- Purpose: Configure plugin params and expose task/log controls.
- Contains: static pages `nano_banana_plugin_geeknow/ui/index.html`, `ui/task_log.html`, `ui/live_log.html`.
- Depends on: `plugin-sdk.js` and host window messaging bridge.
- Used by: End-user via host app plugin panel/popup windows.

## Data Flow

**Image Generation Flow:**
1. Host calls `generate(context)` in `nano_banana_plugin_geeknow/main.py`.
2. `generate()` merges context/plugin params, normalizes base URL, resolves provider/model routing.
3. Initial task row is recorded with `status='running'` in SQLite.
4. Provider adapter sends HTTP request and parses response into base64 data or URL(s).
5. If base64: decode and save directly to output directory.
6. If URL(s): create generated record, download image(s), save PNG(s), update status per outcome.
7. Return local file path list to host.

**UI Action Flow (task log/live log/update):**
1. UI page sends action through Plugin SDK / postMessage bridge.
2. Host routes action to `handle_action(action, data)`.
3. Python handler dispatches to action-specific functions:
   - task logs query
   - manual downloads
   - buffered log polling
   - update check/install
4. Handler returns JSON-like action result consumed by UI page.

**Update Installation Flow:**
1. UI triggers `check_update` (manifest fetch + plugin match + version comparison).
2. UI confirms `do_update` with `download_url` and optional `sha256`.
3. `_execute_update()` downloads package, validates hash, resolves `main.py`, installs with backup rollback support, copies sibling assets.

**State Management:**
- Persistent state: SQLite DB (`image_task_logs.db`) + host plugin config values.
- Ephemeral state: in-memory log buffer (`_log_buffer`) and transient temp directories for updates.

## Key Abstractions

**Provider Strategy by Model Prefix:**
- Purpose: Route one plugin UX to multiple backend APIs.
- Examples: model prefix checks in `generate()` (`grok-`, `doubao-`, default Gemini).
- Pattern: Conditional strategy dispatch.

**Task Lifecycle Ledger:**
- Purpose: Normalize operational statuses across generation and manual download.
- Examples: statuses `running`, `generated`, `success`, `download_failed`, `manual_success`, `failed`.
- Pattern: Append/update lifecycle rows in SQLite.

**Action Router:**
- Purpose: Handle many UI commands via one host callback.
- Examples: `open_task_logs`, `get_task_logs`, `download_images`, `get_logs`, `check_update`, `do_update`.
- Pattern: String-based command dispatch inside `handle_action()`.

## Entry Points

**Plugin Metadata Entry:**
- Location: `nano_banana_plugin_geeknow/main.py:get_info()`.
- Trigger: Host plugin discovery/metadata render.

**Generation Entry:**
- Location: `nano_banana_plugin_geeknow/main.py:generate(context)`.
- Trigger: User starts image generation in host app.

**Action Entry:**
- Location: `nano_banana_plugin_geeknow/main.py:handle_action(action, data)`.
- Trigger: UI pages invoke plugin actions.

**Frontend Entrypoints:**
- `nano_banana_plugin_geeknow/ui/index.html` (main config panel)
- `nano_banana_plugin_geeknow/ui/task_log.html` (task table + manual download)
- `nano_banana_plugin_geeknow/ui/live_log.html` (polling live logs)

## Error Handling

**Strategy:**
- Mostly exception-driven, with action handlers returning `{ok: False, error: ...}` on UI paths.
- Generation path raises host-parseable exceptions with prefixes (e.g., `PLUGIN_ERROR:::` and `NO_RETRY:::` patterns).

**Patterns:**
- HTTP status checks before response parsing in provider/update helpers.
- Broad `except Exception` blocks are common across IO/network/database layers.
- Update installer includes rollback on copy failure (`_install_main_py`).

## Cross-Cutting Concerns

**Logging:**
- Standard logger created in `_setup_logging()` with console handler + in-memory buffering handler.
- `_log()` wrapper keeps older callsites consistent.

**Validation:**
- Input validation is mostly lightweight (presence checks, URL base normalization, supported base URL whitelist, response shape checks).

**Security:**
- Uses bearer token auth for external model calls.
- Update channel supports optional SHA256 verification before install.

---

*Architecture analysis: 2026-04-15*
*Update when plugin contract, provider strategy, or layer boundaries change*
