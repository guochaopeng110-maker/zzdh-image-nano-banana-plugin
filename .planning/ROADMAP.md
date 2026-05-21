# Roadmap: image_plugin_zlhub_nano_banana

## Overview

本路线图围绕“1:1 迁移并稳定出图”的核心目标推进：
先完成独立插件与并存可用，再打通 zlhub 出图与落盘主链路，随后补齐日志可观测与手动补偿闭环，最后做配置与 UI 一致性收敛。

## Phases

- [x] **Phase 01: 插件骨架与并存建立** - 建立独立插件、可被宿主识别并与 GeekNow 插件并存。
- [x] **Phase 02: zlhub 出图主链路闭环** - 打通接口调用、响应解析、多图下载落盘与宿主返回。
- [ ] **Phase 03: 日志可观测与手动补偿闭环** - 保留任务日志能力并支持 URL 未落盘场景的手动补偿。
- [ ] **Phase 04: 配置与 UI 一致性收敛** - 对齐 GeekNow 的关键配置布局交互并确保配置持久化生效。

## Phase Details

### Phase 01: 插件骨架与并存建立
**Goal**: 团队可以在不影响现有 GeekNow 插件的情况下识别并使用新的 zlhub 插件入口。  
**Depends on**: Nothing (first phase)  
**Requirements**: CORE-01, CORE-02, CORE-03  
**Plans**: 1

Plans:
- [x] 01-01-PLAN.md - 建立 zlhub 独立插件骨架、完成身份区分并交付并存校验。

### Phase 02: zlhub 出图主链路闭环
**Goal**: 用户提交提示词后可稳定获得本地落盘图片，并由宿主接收有效路径结果。  
**Depends on**: Phase 01  
**Requirements**: API-01, API-02, API-03, API-04, OUT-01, OUT-02, OUT-03  
**Plans**: 2

Plans:
- [x] 02-01-PLAN.md - 固化 zlhub API 请求/解析契约并建立自动化校验。
- [x] 02-02-PLAN.md - 完成多图下载落盘与宿主本地路径返回闭环。

### Phase 03: 日志可观测与手动补偿闭环
**Goal**: 用户可追踪任务状态、查看日志，并对未落盘任务执行手动下载补偿。  
**Depends on**: Phase 02  
**Requirements**: LOG-01, LOG-02, LOG-03, DL-01, DL-02, DL-03  
**Plans**: TBD
**UI hint**: yes

### Phase 04: 配置与 UI 一致性收敛
**Goal**: 用户在 zlhub 插件中获得与 GeekNow 近似的配置与交互体验，且配置改动可持续生效。  
**Depends on**: Phase 03  
**Requirements**: CFG-01, CFG-02, CFG-03  
**Plans**: TBD
**UI hint**: yes

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 01. 插件骨架与并存建立 | 1/1 | Executed | 2026-04-15 |
| 02. zlhub 出图主链路闭环 | 2/2 | Executed | 2026-04-15 |
| 03. 日志可观测与手动补偿闭环 | 0/TBD | Not started | - |
| 04. 配置与 UI 一致性收敛 | 0/TBD | Not started | - |
