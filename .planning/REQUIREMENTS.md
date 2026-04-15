# Requirements: image_plugin_zlhub_nano_banana

**Defined:** 2026-04-15
**Core Value:** 在不引入新功能复杂度的前提下，快速提供一个与现有 GeekNow 插件体验一致、但后端切换为 zlhub 的稳定图片生成通道。

## v1 Requirements

首版要求：1:1 迁移、并存、稳定出图，不新增产品能力。

### 插件骨架与并存

- [ ] **CORE-01**: 新增独立插件目录 `image_plugin_zlhub_nano_banana`，具备可被宿主识别的基础文件（至少含 `main.py`、`info.json`、`ui/`）
- [ ] **CORE-02**: 新插件可被宿主加载且不影响 `nano_banana_plugin_geeknow` 的现有可用性（并存）
- [ ] **CORE-03**: 新插件名称与描述可区分于 GeekNow 插件，避免团队内部误用

### zlhub 接口对接与出图主链路

- [ ] **API-01**: 插件可按文档地址调用 zlhub 图像生成接口（`/zhonglian/api/v1/proxy/chat/completions`）
- [ ] **API-02**: 插件可按文档字段构造图像生成请求（至少包含 `model`、`prompt`，并支持文档给出的图像参数字段）
- [ ] **API-03**: 插件可正确解析 zlhub 图像响应中的 `data[].url` 并提取可下载图片链接
- [ ] **API-04**: 当 zlhub 返回错误或无可用图片链接时，插件返回可诊断错误信息，不产出伪成功结果

### 生成结果落盘与返回

- [ ] **OUT-01**: 对于成功响应的图片 URL，插件可下载并保存到本地输出目录
- [ ] **OUT-02**: 插件向宿主返回有效的本地图片路径列表，供字字动画后续流程使用
- [ ] **OUT-03**: 多图响应场景下，插件可逐张下载并返回全部成功文件路径

### 任务日志与可视化

- [ ] **LOG-01**: 插件保留任务日志能力，记录任务状态（如运行中、成功、失败）
- [ ] **LOG-02**: 插件保留任务日志页面能力（task_log），可查询历史任务并查看关键信息
- [ ] **LOG-03**: 插件保留实时日志页面能力（live_log），可查看最近运行日志

### 手动下载与任务补偿

- [ ] **DL-01**: 对于仅生成 URL 但未成功落盘的任务，插件支持手动下载补偿
- [ ] **DL-02**: 手动下载成功后，任务状态可更新为成功类状态并可在日志页体现
- [ ] **DL-03**: 手动下载结果文件按可追踪命名落盘，便于团队定位与复查

### 配置与 UI 一致性

- [ ] **CFG-01**: 插件提供与 GeekNow 插件尽量一致的关键配置项布局与交互方式
- [ ] **CFG-02**: 配置变更可持久化并在生成流程中生效
- [ ] **CFG-03**: 首版不新增超出 GeekNow 迁移目标之外的 UI 功能入口

## v2 Requirements

延后到后续版本，不进入当前路线图。

### 能力扩展

- **EXT-01**: 在 1:1 迁移完成后，评估并引入 zlhub 特有能力（如更丰富参数模板）
- **EXT-02**: 提供跨平台或跨宿主场景的插件适配
- **EXT-03**: 增加高级可观测性能力（更细粒度指标面板/告警）

## Out of Scope

明确排除项，用于避免范围蔓延。

| Feature | Reason |
|---------|--------|
| 新增超出 GeekNow 的产品功能 | 用户明确首版仅做 1:1 迁移，不加新功能 |
| 替换或改造原 nano_banana_plugin_geeknow | 用户明确要求新旧并存，避免影响现有流程 |
| 非当前字字动画团队场景的扩展 | 当前目标是团队内部稳定交付，不做跨场景扩张 |

## Traceability

路线图创建后更新映射。每个 v1 需求必须且仅映射到一个 Phase。

| Requirement | Phase | Status |
|-------------|-------|--------|
| CORE-01 | Phase 1 | Pending |
| CORE-02 | Phase 1 | Pending |
| CORE-03 | Phase 1 | Pending |
| API-01 | Phase 2 | Pending |
| API-02 | Phase 2 | Pending |
| API-03 | Phase 2 | Pending |
| API-04 | Phase 2 | Pending |
| OUT-01 | Phase 2 | Pending |
| OUT-02 | Phase 2 | Pending |
| OUT-03 | Phase 2 | Pending |
| LOG-01 | Phase 3 | Pending |
| LOG-02 | Phase 3 | Pending |
| LOG-03 | Phase 3 | Pending |
| DL-01 | Phase 3 | Pending |
| DL-02 | Phase 3 | Pending |
| DL-03 | Phase 3 | Pending |
| CFG-01 | Phase 4 | Pending |
| CFG-02 | Phase 4 | Pending |
| CFG-03 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 19 total
- Mapped to phases: 19
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-15*
*Last updated: 2026-04-15 after roadmap mapping*
