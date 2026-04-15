---
phase: 02-zlhub
plan: 02
subsystem: api
tags: [zlhub, output-paths, download, local-files, verification]

requires:
  - phase: 02-zlhub
    provides: 固定 zlhub 请求契约与 data[].url 解析能力（02-01）
provides:
  - 单图 URL 下载后本地落盘并返回绝对路径列表
  - 多图 URL 逐张下载保存与成功项聚合返回
  - 全量下载失败时抛出 PLUGIN_ERROR 防止空列表伪成功
  - Phase 2 输出路径自动验证脚本（single/multi suites）
affects: [phase-02-main-chain, host-output-consumer, task-log-audit]

tech-stack:
  added: []
  patterns: [url_list 逐项下载, success/download_failed 逐条日志记录, generated_files 非空返回守卫]

key-files:
  created:
    - .planning/scripts/verify_phase2_output_paths.py
  modified:
    - image_plugin_zlhub_nano_banana/main.py

key-decisions:
  - "多图场景采用部分成功保留策略：失败图片记录 download_failed，不丢弃已成功落盘文件。"
  - "当 image_source_url 存在但 generated_files 为空时，强制抛出 PLUGIN_ERROR:::所有图片下载失败。"
  - "输出路径验证脚本直接黑盒调用 generate(context)，校验绝对路径、文件存在性与命名后缀。"

patterns-established:
  - "Output Contract Verification: 用独立脚本验证 OUT-01/OUT-02/OUT-03 的单图/多图/全失败边界。"
  - "Per-item Download Audit: 每个 URL 单独记录 generated/success/download_failed 状态。"

requirements-completed: [OUT-01, OUT-02, OUT-03]

duration: 5 min
completed: 2026-04-15
---

# Phase 2 Plan 2: zlhub 落盘与返回路径闭环 Summary

**zlhub URL 响应已实现逐张下载落盘与绝对路径返回，并在全失败边界下阻断空列表伪成功。**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-15T14:24:00+08:00
- **Completed:** 2026-04-15T06:29:55Z
- **Tasks:** 2/2
- **Files modified:** 2

## Accomplishments
- 新增 `.planning/scripts/verify_phase2_output_paths.py`，提供 `--suite single` 与 `--suite multi` 自动验证。
- `generate(context)` 多图 URL 流程支持“部分失败保留成功项”，并为每个 URL 写入 success/download_failed 任务状态。
- 当 URL 响应全部下载失败时，`generate(context)` 抛出 `PLUGIN_ERROR:::所有图片下载失败`，避免返回空列表造成伪成功。

## Task Commits

Each task was committed atomically:

1. **Task 1: 建立主链路落盘与返回路径自动验证脚本** - `6aaab7f` (test)
2. **Task 2: 加固 generate 多图下载落盘与返回聚合逻辑** - `e58cfb9` (fix)

## Files Created/Modified
- `F:/Projects/zz-image-plugins/.claude/worktrees/agent-ad6916d8/.planning/scripts/verify_phase2_output_paths.py` - 单图/多图/全失败边界黑盒验证，输出 `PASS single_url_suite` 与 `PASS multi_url_suite`。
- `F:/Projects/zz-image-plugins/.claude/worktrees/agent-ad6916d8/image_plugin_zlhub_nano_banana/main.py` - 新增 URL 下载全失败保护分支，确保 `generated_files` 为空时抛出 `PLUGIN_ERROR`。

## Decisions Made
- 继续沿用既有 `_log_task_result` 审计模型：URL 逐项落 `generated -> success/download_failed`，提升问题可追踪性。
- 多图命名沿用 `_n{idx}` 后缀策略，避免同批次文件覆盖。

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 修复验证脚本无效 PNG fixture 导致保存失败**
- **Found during:** Task 1
- **Issue:** 初始测试 fixture 不是可解析 PNG，`PIL.Image.open` 报错导致 single suite 失败。
- **Fix:** 替换为可解析的 1x1 PNG base64 fixture。
- **Files modified:** `.planning/scripts/verify_phase2_output_paths.py`
- **Verification:** 重新执行 `--suite single` 与 `--suite multi` 均通过。
- **Committed in:** `6aaab7f`

---

**Total deviations:** 1 auto-fixed (Rule 1: 1)
**Impact on plan:** 仅修复测试数据缺陷，不改变业务范围。

## Authentication Gates
None.

## Issues Encountered
- Windows 控制台编码（GBK）下日志中的 `✓` 会触发 `logging` 输出编码告警，但不影响 `generate(context)` 执行结果与验证通过。

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 2 的 OUT-01/OUT-02/OUT-03 已由自动脚本覆盖并通过。
- 可继续推进日志页与手动下载补偿能力的后续计划。

## Self-Check: PASSED
- FOUND summary: `.planning/phases/02-zlhub/02-02-SUMMARY.md`
- FOUND commit: `6aaab7f`
- FOUND commit: `e58cfb9`
