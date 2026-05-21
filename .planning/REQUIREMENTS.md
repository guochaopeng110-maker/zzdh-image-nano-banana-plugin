# Requirements: image_plugin_zlhub_nano_banana

**Defined:** 2026-04-15  
**Core Value:** 在不引入新功能复杂度的前提下，快速提供一个与现有 GeekNow 插件体验一致、但后端切换为 zlhub 的稳定图像生成通道。

## v1 Requirements

### 插件骨架与并存
- [x] **CORE-01**: 新增独立插件目录 `image_plugin_zlhub_nano_banana`，具备可被宿主识别的基础文件（至少含 `main.py`、`info.json`、`ui/`）。
- [x] **CORE-02**: 新插件可被宿主加载且不影响 `nano_banana_plugin_geeknow` 现有可用性（并存）。
- [x] **CORE-03**: 新插件名称与描述可区分于 GeekNow 插件，避免误选。

### zlhub 接口对接与出图主链路
- [x] **API-01**: 插件可按文档地址调用 zlhub 图像生成接口（`/zhonglian/api/v1/proxy/chat/completions`）。
- [x] **API-02**: 插件可按文档字段构造图像生成请求（包含 `model`、`prompt` 等必要字段）。
- [x] **API-03**: 插件可正确解析 zlhub 响应中的 `data[].url` 并提取可下载链接。
- [x] **API-04**: 当 zlhub 返回错误或无可用链接时，插件返回可诊断错误信息，不产生伪成功结果。

### 生成结果落盘与返回
- [x] **OUT-01**: 对成功响应的图片 URL，插件可下载并保存到本地输出目录。
- [x] **OUT-02**: 插件向宿主返回有效的本地图片路径列表，供后续流程使用。
- [x] **OUT-03**: 多图响应场景下，插件可逐张下载并返回全部成功文件路径。

### 任务日志与可视化
- [ ] **LOG-01**: 插件保留任务日志能力，记录任务状态（运行中、成功、失败）。
- [ ] **LOG-02**: 插件保留任务日志页面能力（`task_log`），可查询历史任务并查看关键信息。
- [ ] **LOG-03**: 插件保留实时日志页面能力（`live_log`），可查看最近运行日志。

### 手动下载与任务补偿
- [ ] **DL-01**: 对仅生成 URL 但未成功落盘的任务，插件支持手动下载补偿。
- [ ] **DL-02**: 手动下载成功后，任务状态可更新为成功类状态并可在日志页体现。
- [ ] **DL-03**: 手动下载结果文件按可追踪命名落盘，便于定位与复查。

### 配置与 UI 一致性
- [ ] **CFG-01**: 插件提供与 GeekNow 插件尽量一致的关键配置项布局与交互方式。
- [ ] **CFG-02**: 配置变更可持久化并在生成流程中生效。
- [ ] **CFG-03**: 首版不新增超出 GeekNow 迁移目标之外的 UI 功能入口。

## Traceability

| Requirement | Phase | Status | Evidence |
|-------------|-------|--------|----------|
| CORE-01 | Phase 01 | Complete | `.planning/phases/01-plugin-skeleton-and-coexistence/01-VERIFICATION.md` |
| CORE-02 | Phase 01 | Complete | `.planning/phases/01-plugin-skeleton-and-coexistence/01-VERIFICATION.md` |
| CORE-03 | Phase 01 | Complete | `.planning/phases/01-plugin-skeleton-and-coexistence/01-VERIFICATION.md` |
| API-01 | Phase 02 | Complete | `.planning/phases/02-zlhub/02-01-SUMMARY.md` |
| API-02 | Phase 02 | Complete | `.planning/phases/02-zlhub/02-01-SUMMARY.md` |
| API-03 | Phase 02 | Complete | `.planning/phases/02-zlhub/02-01-SUMMARY.md` |
| API-04 | Phase 02 | Complete | `.planning/phases/02-zlhub/02-01-SUMMARY.md` |
| OUT-01 | Phase 02 | Complete | `.planning/phases/02-zlhub/02-02-SUMMARY.md` |
| OUT-02 | Phase 02 | Complete | `.planning/phases/02-zlhub/02-02-SUMMARY.md` |
| OUT-03 | Phase 02 | Complete | `.planning/phases/02-zlhub/02-02-SUMMARY.md` |
| LOG-01 | Phase 03 | Pending | Not executed yet |
| LOG-02 | Phase 03 | Pending | Not executed yet |
| LOG-03 | Phase 03 | Pending | Not executed yet |
| DL-01 | Phase 03 | Pending | Not executed yet |
| DL-02 | Phase 03 | Pending | Not executed yet |
| DL-03 | Phase 03 | Pending | Not executed yet |
| CFG-01 | Phase 04 | Pending | Not executed yet |
| CFG-02 | Phase 04 | Pending | Not executed yet |
| CFG-03 | Phase 04 | Pending | Not executed yet |

**Coverage:**
- v1 requirements: 19 total
- complete: 10
- pending: 9
