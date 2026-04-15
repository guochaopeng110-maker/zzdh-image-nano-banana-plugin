# Testing Patterns

**Analysis Date:** 2026-04-15

## Test Framework

**Runner:**
- No automated test framework detected in this repository snapshot.
- No Python test manifests (`pytest.ini`, `pyproject.toml`, `requirements*.txt`, `tox.ini`) and no test files matching common patterns.

**Assertion Library:**
- None configured in current codebase artifacts.

**Run Commands:**
```bash
# No project-level test commands discovered from current files.
# Validation currently relies on manual plugin runtime checks.
```

## Test File Organization

**Location:**
- No dedicated `tests/` directory observed.
- No colocated `*_test.py`, `*.spec.*`, or `*.test.*` files observed.

**Naming:**
- N/A (no test files found).

## Current Verification Approach (Observed)

Given no formal tests, reliability appears to depend on:
- Manual execution through host plugin runtime calling `generate(context)` in `nano_banana_plugin_geeknow/main.py`.
- UI-driven sanity checks through:
  - `nano_banana_plugin_geeknow/ui/index.html` (settings + update checks)
  - `nano_banana_plugin_geeknow/ui/task_log.html` (task history/manual download)
  - `nano_banana_plugin_geeknow/ui/live_log.html` (streamed logs)
- Operational introspection via SQLite task table `nano_banana_plugin_geeknow/image_task_logs.db`.

## Implicit “Testable Units” in Current Design

Even without test files, these seams are suitable for unit/integration tests later:
- Pure/low-IO helpers:
  - `_normalize_base_url()`
  - `_get_valid_base_url()`
  - `_parse_version()`
  - `_is_newer_version()`
- Update/install flow (mocking network and filesystem):
  - `_check_update_available()`
  - `_execute_update()`
  - `_install_main_py()`
- Task log persistence lifecycle:
  - `_insert_task_log_entry()`
  - `_update_task_log_entry()`
  - `_fetch_task_logs()`
- Action routing contract in `handle_action()`.

## High-Value Coverage Gaps

**Provider request/response parsing:**
- `send_gemini_request`, `send_doubao_request`, `send_grok_request` have complex response handling and branching (base64/url/list/text parsing) but no automated regression coverage.

**Download and file save paths:**
- URL download + image decode/save path in `_download_image_from_url()` and `_save_image` block inside `generate()` has no automated failure/success matrix.

**Status transitions:**
- Lifecycle transitions (`running` → `generated/success/download_failed/failed`) are central for UI reliability and currently untested.

**Update safety path:**
- Backup/rollback behavior in update installer is critical and untested.

## Suggested Test Strategy (to align with current architecture)

**Unit tests (first):**
- Target helper functions and model/base URL routing logic in `nano_banana_plugin_geeknow/main.py`.
- Mock `requests` responses for provider handlers and update checks.

**Integration tests (second):**
- Use temporary SQLite file + temp output directory to validate `generate()` orchestration and task status progression.
- Exercise `handle_action()` branches with representative payloads.

**UI smoke checks (manual or E2E later):**
- Validate parameter persistence and action roundtrip in `ui/index.html`.
- Validate task table rendering + download command path in `ui/task_log.html`.
- Validate polling behavior in `ui/live_log.html`.

## Minimal Testing Conventions to Introduce (recommended baseline)

- Keep tests near source or in `nano_banana_plugin_geeknow/tests/` for plugin-local clarity.
- Name files `test_<module_or_feature>.py` if adopting `pytest`.
- Use fixtures for:
  - mocked HTTP responses
  - temporary DB/output directories
  - sample plugin contexts (`prompt`, `reference_images`, `plugin_params`)

---

*Testing analysis: 2026-04-15*
*Update when formal test framework and first suite are introduced*
