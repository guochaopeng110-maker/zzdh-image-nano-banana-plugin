# Phase 2: zlhub 出图主链路闭环 - Context

**Gathered:** 2026-04-15
**Status:** Ready for planning

<domain>
## Phase Boundary

打通 zlhub 出图主链路：从请求发起、响应解析、图片下载落盘到宿主返回有效本地路径列表，确保在错误场景下返回可诊断失败而非伪成功。

</domain>

<decisions>
## Implementation Decisions

### 请求字段对齐
- **D-01:** 请求体采用“固定模板 + 默认值”策略：固定发送核心字段（`model`、`prompt`、`response_format`、`size`、`stream`、`watermark`、`sequential_image_generation`），未配置项使用稳定默认值。
- **D-02:** 字段命名与映射严格对齐 zlhub 文档字段，文档字段作为唯一口径（例如配置 `image_size` 映射为请求字段 `size`）。
- **D-03:** 默认值对齐文档示例：`response_format=url`、`stream=false`、`watermark=true`、`sequential_image_generation=disabled`；`size` 采用插件当前默认值。
- **D-04:** 无参考图时仍发送 `image` 空值，格式按输入类型自动：文本模式发送空字符串，图像输入模式发送空数组。
- **D-05:** 接口地址固定为文档路径 `/zhonglian/api/v1/proxy/chat/completions`，不做多端点切换。

### Claude's Discretion
- 响应解析兼容范围（仅 `data[].url` 还是兼容额外格式）的具体实现细节。
- 多图落盘命名细节与部分下载失败时的返回策略。
- 失败反馈到宿主的错误文案分层与内部错误分类映射。

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and acceptance
- `.planning/ROADMAP.md` — Phase 2 目标、依赖、成功标准与边界。
- `.planning/REQUIREMENTS.md` — API-01~API-04、OUT-01~OUT-03 的验收要求。

### API specification
- `docs/require/zlhub-chat-image-api.md` — zlhub 接口地址、请求字段、图像响应（`data[].url`）与示例。

### Project-level constraints
- `.planning/PROJECT.md` — 首版 1:1 迁移、并存不替换、优先稳定出图等非功能约束。

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `image_plugin_zlhub_nano_banana/main.py` `generate(context)`：已具备参数读取、模型分发、下载落盘、返回路径主流程骨架。
- `image_plugin_zlhub_nano_banana/main.py` `send_grok_request` / `send_doubao_request` / `send_gemini_request`：已有请求构建与响应处理适配层，可统一字段口径。
- `image_plugin_zlhub_nano_banana/main.py` `_download_image_from_url`：已具备 URL 下载能力，可复用到多图落盘链路。
- `image_plugin_zlhub_nano_banana/main.py` `_log_task_result`、`download_images_from_logs`：已有任务状态与补偿下载关联能力。

### Established Patterns
- Provider adapter 统一返回 `(image_data_base64, image_url_or_urls)`，主流程可在同一出口处理单图/多图。
- 错误使用 `PLUGIN_ERROR:::` / `NO_RETRY:::` 前缀，便于上游区分可重试与不可重试失败。
- 任务状态已使用 SQLite 记录，具备 `generated` / `download_failed` 等状态流转基础。

### Integration Points
- `generate(context)` 中 `context['plugin_params']` 与 `context['output_dir']` 是主链路配置与落盘入口。
- `handle_action(action, data)` 中任务日志与手动下载动作与主链路结果共享同一日志数据源。
- `info.json` 的插件身份与描述已独立，可在不破坏并存前提下推进主链路实现。

</code_context>

<specifics>
## Specific Ideas

无额外“像某产品那样”的交互参考；本轮核心是先锁定请求字段口径并保证稳定出图。

</specifics>

<deferred>
## Deferred Ideas

- 本轮未展开的灰区（后续如需可再次 discuss）：
  - 响应解析策略（严格 `data[].url` vs 兼容兜底格式）
  - 多图落盘规则（命名与部分失败返回口径）
  - 失败反馈口径（对宿主错误暴露粒度）

</deferred>

---

*Phase: 02-zlhub*
*Context gathered: 2026-04-15*
