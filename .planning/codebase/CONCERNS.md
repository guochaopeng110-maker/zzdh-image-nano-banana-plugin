# Codebase Concerns

**Analysis Date:** 2026-04-15

## Tech Debt

**Single-file monolith (`nano_banana_plugin_geeknow/main.py`):**
- Issue: Update flow, provider clients, task DB, logging, and action routing all live in one ~1500-line file.
- Why: Fast iteration in plugin context with minimal packaging overhead.
- Impact: High change coupling; provider tweaks can unintentionally affect action routing or persistence.
- Fix approach: Split into modules (`providers.py`, `task_log.py`, `actions.py`, `update.py`, `logging_utils.py`) while preserving contract functions in `main.py`.

**Unused retry configuration path:**
- Issue: `retry_count` is captured in UI/default params (`nano_banana_plugin_geeknow/ui/index.html`, `nano_banana_plugin_geeknow/main.py`) but not applied in request retry behavior.
- Why: UI/param surface evolved ahead of backend implementation.
- Impact: Operator expectation mismatch (setting retries currently has no effect).
- Fix approach: Implement bounded retry with backoff around provider requests and explicit logs, or remove the setting.

## Known Bugs / Behavioral Risks

**Potential API key leakage in logs:**
- Symptoms: Full API key can be emitted to logs during Gemini request path.
- Trigger: `send_gemini_request()` logs full function arguments (`f"send_gemini_request: {api_key}, ..."`).
- File: `nano_banana_plugin_geeknow/main.py` (around line 985).
- Workaround: Avoid verbose logs in production and rotate keys if exposed.
- Root cause: Debug logging statement includes raw secret.

**HTTP timeout parameters are inconsistently used:**
- Symptoms: User-provided `request_timeout` is logged and passed through helpers but not applied in provider `requests.post(...)` calls.
- Trigger: Any long-running or hung upstream request path.
- Files: `nano_banana_plugin_geeknow/main.py` in `send_grok_request`, `send_doubao_request`, `send_gemini_request`.
- Workaround: Rely on default requests/socket behavior (not ideal).
- Root cause: Timeout argument omitted in POST invocations.

## Security Considerations

**Remote update install path trust boundary:**
- Risk: Plugin downloads and installs executable code (`main.py`) from URL specified by remote manifest.
- Files: `_check_update_available()`, `_execute_update()`, `_resolve_update_main_py()`, `_install_main_py()` in `nano_banana_plugin_geeknow/main.py`.
- Current mitigation: Optional SHA256 verification if manifest includes hash; backup/rollback on install failure.
- Recommendations:
  - Require SHA256 presence and reject updates without hash.
  - Restrict update host allowlist.
  - Consider signature verification rather than hash-only trust.

**Permissive cross-window messaging in UI popups:**
- Risk: Popup comm uses `postMessage(..., '*')` and broad listener acceptance pattern.
- Files: `nano_banana_plugin_geeknow/ui/task_log.html`, `nano_banana_plugin_geeknow/ui/live_log.html`.
- Current mitigation: Custom marker (`__typetale_plugin`) and message type checks.
- Recommendations: Validate `event.origin` where host origin is known and enforce stricter sender checks.

## Performance Bottlenecks

**In-memory image conversion and response handling:**
- Problem: Base64 encode/decode and full-content buffering can spike memory for high-resolution or multi-image outputs.
- Files: `image_to_base64()`, `_download_image_from_url()`, provider handlers, `_save_image` path in `generate()`.
- Measurement: No benchmark data found in repo.
- Cause: Full payload held in memory rather than streamed/segmented processing.
- Improvement path: Add size guards, stream downloads to temp files, and avoid duplicate encode/decode passes when possible.

**Task log query scaling:**
- Problem: UI requests up to 500 rows and performs full render on each refresh.
- Files: `nano_banana_plugin_geeknow/ui/task_log.html` + `_fetch_task_logs()`.
- Measurement: No explicit latency metrics.
- Cause: Simple pagination-less approach.
- Improvement path: Add offset/page support and incremental rendering.

## Fragile Areas

**Provider response parsing with many schema branches:**
- Why fragile: Parsing handles multiple provider response formats (url, b64_json, inlineData, markdown-url text extraction, data URI).
- Files: `send_gemini_request()`, `send_doubao_request()`, `send_grok_request()` in `nano_banana_plugin_geeknow/main.py`.
- Common failures: Upstream schema drift can silently route to failure path.
- Safe modification: Add provider-specific parsing helpers + fixture-based tests before changing extraction regex or precedence.
- Test coverage: No automated tests observed.

**SQLite schema migration in-place at startup:**
- Why fragile: Startup mutates schema opportunistically with `ALTER TABLE` checks.
- Files: `_init_task_log_db()` in `nano_banana_plugin_geeknow/main.py`.
- Common failures: Corrupt DB or partial schema mismatches can degrade action reliability.
- Safe modification: Add explicit migration versioning and backup/repair strategy.
- Test coverage: No migration tests observed.

## Scaling Limits

**Local-hosted operational model:**
- Current capacity: Single-user local plugin context, bounded by local CPU/memory/disk.
- Limit: Large batch workflows and high-res image operations can degrade responsiveness.
- Symptoms at limit: Slow UI updates, prolonged generation/download handling, larger DB growth.
- Scaling path: Introduce batching controls, retention policy for task logs/files, and optional archival/cleanup actions.

## Dependencies at Risk

**Third-party endpoint stability:**
- Risk: Multiple external base URLs and upload/update endpoints are hard dependencies.
- Files: constants in `nano_banana_plugin_geeknow/main.py` and UI manifest URL in `nano_banana_plugin_geeknow/ui/index.html`.
- Impact: Any endpoint outage directly impacts generation or update workflows.
- Migration plan: Add health-check and fallback strategy with explicit user-facing diagnostics.

## Missing Critical Features

**No request retry/backoff implementation:**
- Problem: transient upstream/network failures fail immediately.
- Current workaround: manual rerun by user.
- Blocks: reliability under intermittent network/API turbulence.
- Implementation complexity: Low-medium (shared request wrapper + idempotent retry guards).

**No automated cleanup/retention for task artifacts:**
- Problem: task DB and manual download directory grow over time.
- Current workaround: manual deletion.
- Blocks: long-term maintainability for heavy users.
- Implementation complexity: Low (retention settings + cleanup action).

## Test Coverage Gaps

**Core generation orchestration:**
- What's not tested: full `generate()` lifecycle across success/failure/provider variants.
- Risk: regressions in status updates or output handling can go unnoticed until runtime.
- Priority: High.
- Difficulty to test: Medium (requires mocking HTTP and file IO).

**Update path safety:**
- What's not tested: hash validation enforcement, rollback scenarios, zip layout variations.
- Risk: failed update may partially mutate plugin state.
- Priority: High.
- Difficulty to test: Medium (temp dirs + controlled fixtures).

---

*Concerns audit: 2026-04-15*
*Update as concerns are mitigated or new production issues emerge*
