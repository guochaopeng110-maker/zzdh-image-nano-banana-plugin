---
phase: 02-zlhub
plan: 01
status: complete
subsystem: api
tags: [zlhub, doubao, api-contract, requests, parsing]

requires:
  - phase: 01-plugin-skeleton-and-coexistence
    provides: zlhub 插件目录骨架与 generate/provider 调度主流程
provides:
  - zlhub 固定端点请求与 Bearer 鉴权头对齐
  - D-01~D-04 请求字段/默认值契约固化
  - data[].url 多图解析与无 URL 快速失败契约
  - Phase 2 API 契约自动验证脚本（request/parse suites）
affects: [phase-02-output-chain, verification, provider-adapter]

tech-stack:
  added: []
  patterns: [固定字段白名单 payload, data[].url 显式遍历提取, NO_RETRY/PLUGIN_ERROR 前缀错误分层]

key-files:
  created:
    - .planning/scripts/verify_phase2_api_contract.py
  modified:
    - image_plugin_zlhub_nano_banana/main.py

key-decisions:
  - "Doubao/zlhub 路径固定为 /zhonglian/api/v1/proxy/chat/completions，不再使用 /v1/images/generations。"
  - "send_doubao_request 仅返回 URL/URL 列表，并在无可用 data[].url 时抛出 NO_RETRY 前缀错误。"
  - "请求体采用固定键集合并锁定默认值，避免隐式字段透传。"

patterns-established:
  - "Provider Contract Guard: 使用独立脚本黑盒验证请求与解析契约。"
  - "Failure Clarity: provider 内 NO_RETRY，generate 层统一包装 PLUGIN_ERROR。"

requirements-completed: [API-01, API-02, API-03, API-04]

duration: 2 min
completed: 2026-04-15
---

# Phase 2 Plan 1: zlhub API 契约锁定 Summary

**zlhub 出图调用已锁定固定 chat/completions 端点与严格 payload 字段契约，并实现 data[].url 全量提取与可诊断失败。**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-15T14:06:56+08:00
- **Completed:** 2026-04-15T06:08:39Z
- **Tasks:** 2/2
- **Files modified:** 2

## Accomplishments
- 新增 Phase 2 API 契约验证脚本，支持 `--suite request` 与 `--suite parse`。
- `send_doubao_request` 固化到 `.../zhonglian/api/v1/proxy/chat/completions`，并对齐 D-01~D-04 字段与默认值。
- 响应解析改为遍历 `data[].url` 返回单图/多图；无可用 URL 直接抛 `NO_RETRY:::`，避免伪成功。

## Task Commits

Each task was committed atomically:

1. **Task 1: 建立 API 契约自动验证脚本（请求字段 + 解析失败分支）** - `8da5219` (test)
2. **Task 2: 按 D-01~D-05 固化 zlhub 请求与 data[].url 解析** - `1a17c23` (feat)

## Files Created/Modified
- `F:/Projects/zz-image-plugins/.claude/worktrees/agent-ae220158/.planning/scripts/verify_phase2_api_contract.py` - black-box 校验 request/parse 契约并输出 PASS 标记。
- `F:/Projects/zz-image-plugins/.claude/worktrees/agent-ae220158/image_plugin_zlhub_nano_banana/main.py` - 固定 zlhub 端点、payload 键集合、data[].url 多图解析与失败分支。

## Decisions Made
- 使用 `requests.post(..., timeout=request_timeout)` 强制应用超时配置，满足外部 API 快速失败要求。
- `image` 字段按任务模式固定：文生图 `""`，图生图 `[]`（或有效数组），保持接口口径一致。

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] 为验证脚本添加 plugin_utils 导入替身**
- **Found during:** Task 1
- **Issue:** 独立执行脚本导入 `image_plugin_zlhub_nano_banana.main` 时，运行环境缺少 `plugin_utils` 导致模块加载失败。
- **Fix:** 在验证脚本中注入最小 `plugin_utils` stub（仅 `load_plugin_config`），确保黑盒校验可独立运行。
- **Files modified:** `.planning/scripts/verify_phase2_api_contract.py`
- **Verification:** `python ...verify_phase2_api_contract.py --suite request` 与 `--suite parse` 均可执行并输出 PASS。
- **Committed in:** `8da5219`

---

**Total deviations:** 1 auto-fixed (Rule 3: 1)
**Impact on plan:** 仅解除测试执行阻塞，无业务范围扩展。

## Authentication Gates
None.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- API-01~API-04 对应契约已可自动验证。
- 可进入 Phase 2 后续计划（落盘链路与宿主返回有效本地路径）。

## Self-Check: PASSED
- FOUND summary: `.planning/phases/02-zlhub/02-01-SUMMARY.md`
- FOUND commit: `8da5219`
- FOUND commit: `1a17c23`

---
*Phase: 02-zlhub*
*Completed: 2026-04-15*
