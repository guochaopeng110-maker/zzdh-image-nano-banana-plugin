---
phase: 01-plugin-skeleton-and-coexistence
plan: 01
subsystem: infra
tags: [python-plugin, zlhub, coexistence, plugin-metadata]

requires:
  - phase: 00-initialization
    provides: 项目需求、路线图与执行约束
provides:
  - 新增 image_plugin_zlhub_nano_banana 独立插件骨架
  - 完成 zlhub 身份标识与 _PLUGIN_ID 入口隔离
  - 提供并存自动化校验脚本用于回归
affects: [phase-02-api-integration, plugin-loading, coexistence-validation]

tech-stack:
  added: []
  patterns: [并存目录复制骨架, 运行时入口断言校验, 元数据身份区分]

key-files:
  created:
    - image_plugin_zlhub_nano_banana/main.py
    - image_plugin_zlhub_nano_banana/info.json
    - image_plugin_zlhub_nano_banana/ui/index.html
    - image_plugin_zlhub_nano_banana/ui/task_log.html
    - image_plugin_zlhub_nano_banana/ui/live_log.html
    - image_plugin_zlhub_nano_banana/.gitignore
    - .planning/scripts/verify_phase1_coexistence.py
  modified: []

key-decisions:
  - 固定新插件名称为“图片中转插件 - zlhub(迁移版)”并在描述中包含 zlhub，避免与 GeekNow 混淆。
  - 将新插件 _PLUGIN_ID 固定为 image_plugin_zlhub_nano_banana，避免更新清单匹配错位。
  - 并存校验脚本在缺少宿主 plugin_utils 依赖时注入最小 stub，确保仓库内可重复验证。

patterns-established:
  - "并存基线模式: 新插件目录复制成熟骨架后再做身份差异化。"
  - "回归校验模式: 通过路径导入双插件并做入口与名称断言。"

requirements-completed: [CORE-01, CORE-02, CORE-03]

duration: 4min
completed: 2026-04-15
---

# Phase 1 Plan 1: 插件骨架与并存建立 Summary

**交付了可被宿主识别的 zlhub 独立插件骨架，并用自动化脚本验证与 GeekNow 插件可并存加载且入口完整。**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-15T04:27:29Z
- **Completed:** 2026-04-15T04:32:04Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- 新建 `image_plugin_zlhub_nano_banana/`，包含 `main.py`、`info.json`、`ui/` 与运行产物忽略规则。
- 完成新插件身份区分：`info.json`、`get_info()`、启动/完成日志、`_PLUGIN_ID`、UI 标题与主标题均体现 zlhub。
- 创建 `.planning/scripts/verify_phase1_coexistence.py`，自动断言两插件入口可调用、名称可区分、基础文件齐全。

## Task Commits

Each task was committed atomically:

1. **Task 1: 建立 zlhub 插件独立目录与基础骨架（CORE-01）** - `7fa0954` (feat)
2. **Task 2: 完成插件身份区分与入口隔离（CORE-03）** - `9d22b1f` (feat)
3. **Task 3: 增加并存自动化校验脚本（CORE-02）** - `904e4ed` (test)

## Files Created/Modified
- `image_plugin_zlhub_nano_banana/main.py` - 新插件独立运行入口（复制骨架后完成 zlhub 身份隔离）。
- `image_plugin_zlhub_nano_banana/info.json` - 新插件元数据名称与描述。
- `image_plugin_zlhub_nano_banana/ui/index.html` - 插件主界面标题与主标题 zlhub 化。
- `image_plugin_zlhub_nano_banana/ui/task_log.html` - 任务日志页骨架。
- `image_plugin_zlhub_nano_banana/ui/live_log.html` - 实时日志页骨架。
- `image_plugin_zlhub_nano_banana/.gitignore` - Python 缓存、任务库、手动下载目录忽略规则。
- `.planning/scripts/verify_phase1_coexistence.py` - 并存自动验收脚本。

## Decisions Made
- 采用“先复制成熟骨架、后做身份差异化”的方式，减少 Phase 1 改动风险，保障后续 Phase 2 可直接接入 zlhub 主链路。
- 并存校验脚本以文件路径导入作为统一入口校验方式，同时覆盖运行时入口与静态元数据差异。

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] 解决工作树缺失阶段目录导致计划文件不可见**
- **Found during:** Task 1
- **Issue:** 当前并行 worktree 未同步 `.planning/phases/01-plugin-skeleton-and-coexistence/`，导致计划引用路径在工作树内不存在。
- **Fix:** 在不修改共享跟踪文件的前提下，使用主仓库同名 PLAN 作为执行依据，并在工作树内按计划产出目标文件。
- **Files modified:** 无（仅执行路径调整）
- **Verification:** 后续 3 个任务验收命令全部通过
- **Committed in:** `7fa0954`（任务实现提交）

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** 未引入范围变化；仅为执行环境修正，计划目标全部达成。

## Issues Encountered
- Windows 终端输出中文出现编码异常，但断言与退出码均正确，不影响验收结论。

## User Setup Required
None - no external service configuration required.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: import-surface | `.planning/scripts/verify_phase1_coexistence.py` | 新增基于 `importlib.util.spec_from_file_location` 的动态模块加载路径，需要保持仅加载仓库内受控插件文件。 |

## Next Phase Readiness
- 已具备可识别、可区分、可并存的新插件骨架，Phase 2 可在 `image_plugin_zlhub_nano_banana/main.py` 上直接实现 zlhub 接口主链路。
- 并存自动化校验脚本可作为后续改动的快速回归门禁。

---
*Phase: 01-plugin-skeleton-and-coexistence*
*Completed: 2026-04-15*

## Self-Check: PASSED
- Verified key files exist on disk.
- Verified task commit hashes exist in git history (`7fa0954`, `9d22b1f`, `904e4ed`).
