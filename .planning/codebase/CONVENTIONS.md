# Coding Conventions

**Analysis Date:** 2026-04-15

## Naming Patterns

**Files:**
- Plugin runtime entry is a single module file: `main.py`.
- UI pages use lowercase snake/word style names: `index.html`, `task_log.html`, `live_log.html`.
- Documentation filenames use descriptive kebab-case (`docs/require/zlhub-chat-image-api.md`).

**Functions:**
- Internal helper functions prefer leading underscore + snake_case, e.g., `_normalize_base_url`, `_fetch_task_logs`, `_download_image_from_url` in `nano_banana_plugin_geeknow/main.py`.
- Public/contract functions use plain snake_case without underscore: `get_info`, `handle_action`, `generate`.
- Provider functions follow `send_<provider>_request` naming (`send_grok_request`, `send_doubao_request`, `send_gemini_request`).

**Variables:**
- Local variables are snake_case (`request_timeout`, `image_source_url`, `task_log_context`).
- Module-level constants are UPPER_SNAKE_CASE (`_PLUGIN_ID`, `_DEFAULT_BASE_URL`, `MODEL_NAME_MAP`).
- “Private” module globals conventionally use underscore prefix (`_logger`, `_log_buffer`, `_init_params`).

## Code Style

**Formatting characteristics (observed, no enforced formatter config found):**
- 4-space indentation in Python.
- Heavy use of section dividers and Chinese doc/comments for readability.
- Mix of f-strings and plain strings.
- Long lines are present in logging/debug sections (line-length not strictly enforced).

**Frontend style patterns:**
- Vanilla JS in `<script>` blocks (no framework/toolchain).
- DOM references cached into `var` variables at top-level.
- Event listeners defined inline via `addEventListener`.

## Import Organization

**Order (in `nano_banana_plugin_geeknow/main.py`):**
1. Python stdlib imports.
2. Third-party imports (`requests`, `PIL`).
3. Local path adjustment and local module import (`plugin_utils`).

**Grouping:**
- Blank lines separate import groups.
- Import sorting is mostly logical/manual, not strictly alphabetical.

## Error Handling

**Patterns:**
- Broad `try/except Exception` is the dominant pattern across network, file, and DB operations.
- API/provider functions raise exceptions with prefixed sentinel strings (`NO_RETRY:::`, `PLUGIN_ERROR:::`) to signal behavior upstream.
- UI action methods return structured `{ok: False, error: ...}` objects rather than throwing in many branches.

**Error types:**
- A custom exception class exists for image download (`ImageDownloadError`), but most other failures use generic `Exception`.
- Update flow includes rollback semantics (`_install_main_py`) on failed install copy.

## Logging

**Framework:**
- Python `logging` with custom buffered handler in `nano_banana_plugin_geeknow/main.py`.
- `_log()` wrapper centralizes level usage (`INFO`, `WARNING`, `ERROR`, `DEBUG`).

**Patterns:**
- Frequent operational logs around API calls, parameters, and status transitions.
- Task events are duplicated in structured SQLite task log state (`_log_task_result`).
- Live-log UI polls buffered logs every 2s (`nano_banana_plugin_geeknow/ui/live_log.html`).

## Comments & Documentation

**When comments are used:**
- Section banners divide major functional blocks (updates, SQLite logs, plugin required functions, generation path).
- Inline comments explain branch decisions (e.g., URL vs base64 fallback for reference images).
- User-facing Chinese labels/messages are embedded in logs and UI for direct operator visibility.

**Docstring style:**
- Most top-level functions include concise Chinese docstrings describing args/returns.
- Docstring thoroughness varies by function.

## Function Design

**Shape:**
- Single-file functional style with many helpers and minimal class abstraction (except logging handler + custom exception).
- `generate()` is the orchestration-heavy function coordinating validation, routing, persistence, networking, and file output.

**Return patterns:**
- Provider adapters return tuples `(image_data_base64, image_url_or_urls)`.
- Action handlers consistently return dict payloads for UI consumption.
- `generate()` returns list of generated file paths.

## Module Design

**Structure:**
- Monolithic module design with grouped sections rather than multi-module package decomposition.
- Module-level constants hold provider/model/base URL maps and defaults.

**Extensibility approach:**
- New providers are added by introducing another `send_*_request` helper and extending model routing in `generate()`.
- UI extension follows adding controls in `ui/index.html` + wiring read path in `generate()`.

## Deviations / Legacy Notes

- A `retry_count` parameter is present in UI/default params but does not currently influence request retry behavior in `generate()` path.
- Some logging paths sanitize secrets, but there is inconsistent masking discipline in one provider function (covered in concerns).

---

*Convention analysis: 2026-04-15*
*Update when formatter/linter or plugin coding style shifts*
