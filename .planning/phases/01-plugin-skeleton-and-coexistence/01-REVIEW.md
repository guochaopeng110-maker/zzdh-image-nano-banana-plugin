---
phase: 01-plugin-skeleton-and-coexistence
reviewed: 2026-04-15T04:39:29Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - image_plugin_zlhub_nano_banana/.gitignore
  - image_plugin_zlhub_nano_banana/info.json
  - image_plugin_zlhub_nano_banana/main.py
  - image_plugin_zlhub_nano_banana/ui/index.html
  - image_plugin_zlhub_nano_banana/ui/live_log.html
  - image_plugin_zlhub_nano_banana/ui/task_log.html
findings:
  critical: 4
  warning: 2
  info: 0
  total: 6
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-04-15T04:39:29Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Reviewed all scoped plugin runtime and UI files at standard depth. I found multiple security issues in update handling and popup message handling, plus correctness issues in timeout/update-version logic. The highest-risk items are unsafe ZIP extraction during self-update, API key leakage into logs, and missing origin validation for cross-window messaging.

## Critical Issues

### CR-01: Self-update ZIP extraction is vulnerable to path traversal (Zip Slip)

**File:** `image_plugin_zlhub_nano_banana/main.py:238`
**Issue:** `_resolve_update_main_py()` calls `archive.extractall(extract_dir)` directly on untrusted ZIP content. A crafted archive can write files outside `extract_dir` via `../` paths.
**Fix:** Validate each member path before extraction and reject entries escaping the target directory.

```python
with zipfile.ZipFile(package_path, 'r') as archive:
    for member in archive.infolist():
        target = (extract_dir / member.filename).resolve()
        if not str(target).startswith(str(extract_dir.resolve()) + os.sep):
            raise Exception(f"非法压缩包路径: {member.filename}")
    archive.extractall(extract_dir)
```

### CR-02: API key is written to logs in plaintext

**File:** `image_plugin_zlhub_nano_banana/main.py:986`
**Issue:** `send_gemini_request()` logs all arguments including `api_key` directly (`_log(f"send_gemini_request: {api_key}, ...")`). This exposes credentials in runtime logs and live-log UI.
**Fix:** Never log raw secrets; mask or omit API key values.

```python
masked = f"***{api_key[-4:]}" if api_key else "<empty>"
_log(f"send_gemini_request: api_key={masked}, endpoint={endpoint}, model={model}, ...")
```

### CR-03: Popup message handlers accept messages from any origin

**File:** `image_plugin_zlhub_nano_banana/ui/live_log.html:85-90`
**Issue:** `window.addEventListener('message', ...)` processes events without validating `evt.origin`/`evt.source`. Combined with permissive `postMessage(..., '*')`, any page can inject forged action data into this popup.
**Fix:** Enforce strict origin/source checks before dispatching handlers.

```javascript
var allowedOrigin = window.location.origin
window.addEventListener('message', function (evt) {
  if (evt.origin !== allowedOrigin) return
  if (evt.source !== window.opener) return
  var d = evt.data
  if (!d || d.__typetale_plugin !== true || d.type !== 'action') return
  // ...
})
```

### CR-04: Same cross-origin message trust issue in task log popup

**File:** `image_plugin_zlhub_nano_banana/ui/task_log.html:119-124`
**Issue:** Same missing origin/source validation as above; popup accepts and renders external message payloads.
**Fix:** Apply the same strict `evt.origin` and `evt.source` checks in this file.

```javascript
if (evt.origin !== window.location.origin) return
if (evt.source !== window.opener) return
```

## Warnings

### WR-01: Network requests ignore configured timeout values

**File:** `image_plugin_zlhub_nano_banana/main.py:824,954,1081,114`
**Issue:** Several HTTP calls do not pass `timeout=...` (`requests.post` for provider APIs and `requests.get` for update manifest). This can hang indefinitely despite timeout params being present in UI/config.
**Fix:** Pass explicit timeout values to each request and use the corresponding config (`request_timeout` for API calls, dedicated timeout for update checks).

### WR-02: Update comparison logic marks equal versions as “has update”

**File:** `image_plugin_zlhub_nano_banana/main.py:213-223,138-149`
**Issue:** `_is_newer_version()` returns `remote >= local`, but `_check_update_available()` interprets true as update available. Equal versions are incorrectly treated as updates.
**Fix:** Use strict greater-than for update availability, or rename function and invert caller logic accordingly.

```python
return tuple(remote) > tuple(local)
```

---

_Reviewed: 2026-04-15T04:39:29Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
