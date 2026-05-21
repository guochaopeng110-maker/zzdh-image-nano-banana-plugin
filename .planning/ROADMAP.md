# Roadmap: image_plugin_zlhub_nano_banana

## Overview

本路线图围绕“1:1 迁移并稳定出图”的核心目标推进：
先完成独立插件与并存可用，再打通 zlhub 出图与落盘主链路，随后补齐日志可观测与手动补偿闭环，最后做配置与 UI 一致性收敛。

## Phases

- [x] **Phase 01: 插件骨架与并存建立** - 建立独立插件、可被宿主识别并与 GeekNow 插件并存。
- [x] **Phase 02: zlhub 出图主链路闭环** - 打通接口调用、响应解析、多图下载落盘与宿主返回。

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

### Phase 03: webai平台图片生成对接(参考image_plugin_zlhub_nano_banana)

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd-plan-phase 03 to break down)
