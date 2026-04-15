# Roadmap: image_plugin_zlhub_nano_banana

## Overview

该路线图围绕“1:1 迁移且稳定出图”的核心价值展开：先完成新插件骨架与并存可用，再打通 zlhub 出图与落盘主链路，随后补齐日志可视化与手动下载补偿，最后做配置与 UI 一致性收敛，确保团队在不增加新功能复杂度的前提下平滑切换。

## Phases

**Phase 编号规则：**
- 整数 Phase（1, 2, 3）：计划内里程碑工作
- 小数 Phase（2.1, 2.2）：插入式紧急工作（如需）

- [ ] **Phase 1: 插件骨架与并存建立** - 建立独立插件、可被宿主识别并与 GeekNow 插件并存。
- [ ] **Phase 2: zlhub 出图主链路闭环** - 打通接口调用、响应解析、多图下载落盘与宿主返回。
- [ ] **Phase 3: 日志可观测与手动补偿闭环** - 保留任务日志能力并支持 URL 未落盘场景的手动补偿。
- [ ] **Phase 4: 配置与 UI 一致性收敛** - 对齐 GeekNow 的关键配置布局交互并确保配置持久化生效。

## Phase Details

### Phase 1: 插件骨架与并存建立
**Goal**: 团队可以在不影响现有 GeekNow 插件的情况下识别并使用新的 zlhub 插件入口。
**Depends on**: Nothing (first phase)
**Requirements**: CORE-01, CORE-02, CORE-03
**Success Criteria** (what must be TRUE):
  1. 宿主可识别并加载 `image_plugin_zlhub_nano_banana` 插件目录，且基础文件结构完整可见。
  2. 新旧两个插件可在同一宿主环境下并存可用，启用新插件不会导致 GeekNow 插件不可用。
  3. 用户在插件列表或入口信息中可明确区分 zlhub 插件与 GeekNow 插件，避免误选。
**Plans**: 1 plans
Plans:
- [x] 01-01-PLAN.md — 建立 zlhub 独立插件骨架、完成身份区分并交付并存自动化校验

### Phase 2: zlhub 出图主链路闭环
**Goal**: 用户提交提示词后可稳定获得本地落盘图片，并由宿主接收有效路径结果。
**Depends on**: Phase 1
**Requirements**: API-01, API-02, API-03, API-04, OUT-01, OUT-02, OUT-03
**Success Criteria** (what must be TRUE):
  1. 用户发起生成后，插件可按文档地址与字段成功调用 zlhub 图像生成接口并完成请求。
  2. 当 zlhub 返回图像结果时，插件可正确解析 `data[].url`，并将可用图片逐张下载到本地输出目录。
  3. 宿主收到的结果为有效本地图片路径列表，且可直接用于后续字字动画流程。
  4. 在多图响应场景下，插件可返回全部成功下载文件路径，不丢图。
  5. 当 zlhub 返回错误或无可用链接时，用户可看到可诊断错误信息，且不会出现伪成功结果。
**Plans**: 2 plans
Plans:
- [ ] 02-01-PLAN.md — 固化 zlhub API 请求/解析契约并建立自动化校验
- [ ] 02-02-PLAN.md — 完成多图下载落盘与宿主本地路径返回闭环

### Phase 3: 日志可观测与手动补偿闭环
**Goal**: 用户可追踪任务状态、查看日志，并对未落盘任务执行手动下载补偿。
**Depends on**: Phase 2
**Requirements**: LOG-01, LOG-02, LOG-03, DL-01, DL-02, DL-03
**Success Criteria** (what must be TRUE):
  1. 用户可在任务日志中看到任务状态流转（运行中、成功、失败）及关键信息。
  2. 用户可在 `task_log` 页面查询历史任务并定位需要补偿的任务记录。
  3. 用户可在 `live_log` 页面查看最近运行日志并快速判断当前执行情况。
  4. 对于仅生成 URL 但未落盘的任务，用户可手动触发下载补偿并在成功后看到状态更新为成功类状态。
  5. 手动下载产物按可追踪命名落盘，便于团队复查与问题定位。
**Plans**: TBD
**UI hint**: yes

### Phase 4: 配置与 UI 一致性收敛
**Goal**: 用户在 zlhub 插件中获得与 GeekNow 近似的配置与交互体验，且配置改动可持续生效。
**Depends on**: Phase 3
**Requirements**: CFG-01, CFG-02, CFG-03
**Success Criteria** (what must be TRUE):
  1. 用户在配置页面看到的关键配置项布局与交互方式与 GeekNow 插件保持尽量一致。
  2. 用户修改配置后可持久化保存，重新进入插件后仍保持最新配置值。
  3. 用户使用更新后的配置发起生成时，生成行为按新配置生效，且首版不存在超出迁移目标的新 UI 功能入口。
**Plans**: TBD
**UI hint**: yes

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. 插件骨架与并存建立 | 0/1 | Planned | - |
| 2. zlhub 出图主链路闭环 | 0/2 | Not started | - |
| 3. 日志可观测与手动补偿闭环 | 0/TBD | Not started | - |
| 4. 配置与 UI 一致性收敛 | 0/TBD | Not started | - |
