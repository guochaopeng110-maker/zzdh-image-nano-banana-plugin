# Phase 04: 基于 image_plugin_webai_nano_banana 复制实现 image_plugin_huimeng_nano_banana，对接 docs/require/huimeng-image-video-api.md，并与现有 6 个插件并存 - Context

**Gathered:** 2026-05-26
**Status:** Ready for planning

<domain>
## Phase Boundary

基于 `image_plugin_webai_nano_banana` 的插件机制，新增独立目录 `image_plugin_huimeng_nano_banana`，实现惠梦平台“图片生成”对接闭环：提交任务、轮询结果、下载落盘、返回宿主可用本地路径，并与现有 6 个插件并存。

本阶段仅包含：
- 新建并实现 `image_plugin_huimeng_nano_banana`（`main.py`、`info.json`、`ui/`）
- 对接 `docs/require/huimeng-image-video-api.md` 中任务接口（图片生成主链路）
- 保持与 `image_plugin_webai_nano_banana` 一致的日志、任务记录、错误前缀与落盘行为

明确不做：
- 本阶段不实现视频生成功能
- 不改动现有目录：
  - `image_plugin_tduhub_nano_banana`
  - `image_plugin_tduhub_nano_banana-V2`
  - `image_plugin_zlhub_nano_banana`
  - `image_plugin_zlhub_nano_banana-V2`
  - `nano_banana_plugin_geeknow`
  - `image_plugin_webai_nano_banana`
</domain>

<decisions>
## Implementation Decisions

### 范围与并存
- **D-01:** 范围锁定为“图片生成”，不包含视频生成。
- **D-02:** 采用独立插件目录 `image_plugin_huimeng_nano_banana`，通过唯一 `_PLUGIN_ID` 与 `info.json` 名称描述区分，保证与现有 6 个插件并存。

### 接口调用与任务流
- **D-03:** 按惠梦文档采用异步任务模式：`POST /api/v1/tasks` 提交任务，获取 `task_id`。
- **D-04:** 对 `GET /api/v1/tasks/{task_id}` 进行轮询，状态机以 `pending -> processing -> completed/failed` 为准。
- **D-05:** 认证统一使用 `Authorization: Bearer <api_key>`。

### 结果提取与落盘
- **D-06:** 图片结果提取策略：优先 `result.image_urls`，为空时回退 `result.image_url`。
- **D-07:** 多图场景逐张下载并落盘，返回宿主可直接消费的本地绝对路径列表。
- **D-08:** 保持与 webai 插件一致的输出命名与 PNG 保存策略，确保可追踪与稳定落盘。

### UI 与配置
- **D-09:** 复用 `image_plugin_webai_nano_banana` 的 UI 结构与交互范式，仅替换惠梦平台必要字段，不引入大规模新控件。
- **D-10:** 必要配置项至少包括：`api_key`、`base_url`、`model`、`request_timeout`、`poll_interval_ms`、`poll_timeout_ms`（命名可在计划阶段微调）。

### 失败策略与可观测性
- **D-11:** 轮询超时、任务 failed、结果为空等场景统一抛 `PLUGIN_ERROR:::`（必要时用 `NO_RETRY:::` 标识非重试类错误），不返回伪成功空列表。
- **D-12:** 即使失败也必须完整落任务日志（running -> failed）并保留错误原因，维持实时日志可诊断性。

### the agent's Discretion
- **D-13:** 轮询默认参数（间隔、最大等待）由实现阶段按“稳定优先”给出保守默认值，并暴露为可配置项。
- **D-14:** 是否在首版启用 webhook 回调能力由规划阶段评估；若引入会增加复杂度，可先不纳入本阶段。
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase and requirement sources
- `.planning/ROADMAP.md` - Phase 04 scope, dependency, and milestone ordering
- `.planning/REQUIREMENTS.md` - Existing requirement traceability format and acceptance style
- `.planning/STATE.md` - Current milestone execution state and continuity notes

### API specification
- `docs/require/huimeng-image-video-api.md` - Huimeng auth, task submit/query contract, status model, and result fields

### Reference implementation
- `image_plugin_webai_nano_banana/main.py` - Baseline plugin contract, logging/task-log structure, output persistence pattern
- `image_plugin_webai_nano_banana/info.json` - Plugin metadata structure
- `image_plugin_webai_nano_banana/ui/index.html` - Config UI baseline
- `image_plugin_webai_nano_banana/ui/task_log.html` - Task log UI baseline
- `image_plugin_webai_nano_banana/ui/live_log.html` - Live log UI baseline

### Prior phase context
- `.planning/phases/03-webai-image-plugin-zlhub-nano-banana/03-CONTEXT.md` - Recent platform-migration decisions and coexistence constraints
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `image_plugin_webai_nano_banana/main.py` 已具备可复用骨架：`get_info()` / `generate(context)` / `handle_action(action,data)`。
- 现成的 SQLite 任务日志、实时日志缓冲、状态展示映射与输出落盘流程可直接复用并替换平台请求层。
- `ui/index.html`、`ui/task_log.html`、`ui/live_log.html` 可按“最小差异”迁移，减少 UI 返工风险。

### Established Patterns
- 插件参数从 `context['plugin_params']` 读取并默认兜底。
- 生成函数返回“本地绝对路径列表”作为宿主消费契约。
- 失败通过 `PLUGIN_ERROR:::` 前缀上抛，日志与任务表双写保证可观测。

### Integration Points
- 外部平台接入点集中在 provider request 函数；可将 webai 的单请求模型替换为 huimeng 的“提交+轮询”模型。
- 保持 `download_images/get_task_logs/get_logs` 等 action 能力与现有插件一致，降低宿主侧差异风险。
</code_context>

<specifics>
## Specific Ideas

- 先完成“图片模型”白名单与默认模型配置，视频模型条目不在本阶段开放。
- 提交任务时 `params` 结构优先对齐文档最小必需字段（prompt、可选 ratio/size 等），避免一次性引入过多平台特性。
- 为避免无穷轮询，必须配置可观测的超时上限并在日志中输出轮询次数与最后状态。
</specifics>

<deferred>
## Deferred Ideas

- 惠梦视频生成（`video_url` 结果链路）作为后续独立阶段候选。
- webhook 回调签名校验与被动通知链路（`X-HuiMeng-Signature`）暂不纳入本阶段。
- 更细颗粒平台参数（如复杂风格控制）延后到增强阶段。

None beyond above.
</deferred>

---

*Phase: 04-image-plugin-webai-nano-banana-image-plugin-huimeng-nano-ban*
*Context gathered: 2026-05-26*
