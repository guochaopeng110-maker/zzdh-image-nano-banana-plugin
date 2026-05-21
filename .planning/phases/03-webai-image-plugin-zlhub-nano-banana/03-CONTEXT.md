# Phase 03: webai平台图片生成对接(参考image_plugin_zlhub_nano_banana) - Context

**Gathered:** 2026-05-21
**Status:** Ready for planning

<domain>
## Phase Boundary

基于 `image_plugin_zlhub_nano_banana` 的插件机制，实现一个新的 webai 中转平台图片生成插件。

本阶段只做以下范围：
- 新建独立插件目录并完成 webai 对接主链路（请求、解析、下载落盘、宿主返回）
- 对齐已有插件机制（参数读取、日志、任务记录、错误前缀）
- 提供最小可验证脚本，证明接口契约和输出路径有效

明确不做：
- 不修改以下既有目录中的代码：
  - `image_plugin_tduhub_nano_banana`
  - `image_plugin_tduhub_nano_banana-V2`
  - `image_plugin_zlhub_nano_banana`
  - `image_plugin_zlhub_nano_banana-V2`
  - `nano_banana_plugin_geeknow`
</domain>

<decisions>
## Implementation Decisions

### 接口与请求契约
- **D-01:** 基础地址默认使用文档值 `http://localhost:8316`，认证方式使用 `Authorization: Bearer <api_key>`。
- **D-02:** 生成接口固定走 `POST /v1/chat/completions`。
- **D-03:** 请求体采用 OpenAI Chat Completions 兼容结构：`model` + `messages` + 可选 `stream`。
- **D-04:** 文生图时，`messages[0].content` 使用纯文本提示词；图生图时使用多模态数组（`text` + `image_url`），其中图片使用 Data URL（base64）。
- **D-05:** 首版同时支持非流式与流式（`stream=false/true`）两种模式，且两种模式都必须稳定落盘。
- **D-06:** 在 `index.html` 提供流式/非流式可选配置项，保存到插件参数并在请求时生效。

### 响应解析与落盘
- **D-07:** 非流式：从 `choices[].message.content` 提取图片数据（优先解析 markdown/data-url 中的 base64 图像内容）。
- **D-08:** 流式：从 SSE 增量片段中聚合最终图片内容，确保与非流式一致的落盘结果。
- **D-09:** 如果未提取到可用图像数据，返回可诊断失败（`NO_RETRY:::` / `PLUGIN_ERROR:::`），不返回伪成功空结果。
- **D-10:** 输出路径与命名策略复用参考插件模式，返回宿主可直接消费的本地绝对路径列表。

### 兼容性与风险约束
- **D-11:** 新插件目录独立，`_PLUGIN_ID`、`info.json` 名称/描述与现有插件可区分，确保并存。
- **D-12:** 不改动现有五个已验证插件目录，仅在新 webai 插件目录和 `.planning` 下新增/修改。
</decisions>

<canonical_refs>
## Canonical References

- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `docs/require/webai-chat-image-api .md`
- `image_plugin_zlhub_nano_banana/main.py`
- `image_plugin_zlhub_nano_banana/info.json`
- `image_plugin_zlhub_nano_banana/ui/index.html`
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- 参考 `image_plugin_zlhub_nano_banana` 的插件结构：`main.py` + `info.json` + `ui/`
- 复用其主流程组织方式：`get_info()` / `generate(context)` / `handle_action(action, data)`
- 复用其下载落盘与任务日志模式（SQLite 任务记录、错误前缀分层）

### Integration Points
- 宿主输入来自 `context['plugin_params']` 与 `context['output_dir']`
- 结果输出为本地图片绝对路径列表
- UI 参数沿用同类插件机制，聚焦 webai 必需配置（api_key/base_url/model/timeout 等）
</code_context>

<deferred>
## Deferred Ideas

- webai 流式（SSE）输出的实时增量展示（后续版本）
- 更复杂的内容提取兜底策略（多种 markdown/HTML 混排）
- 多模型路由策略与自动降级
</deferred>

---

*Phase: 03-webai-image-plugin-zlhub-nano-banana*
*Context gathered: 2026-05-21*
