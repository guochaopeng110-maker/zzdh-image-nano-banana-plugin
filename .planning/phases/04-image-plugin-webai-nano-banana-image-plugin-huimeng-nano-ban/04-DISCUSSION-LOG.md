# Phase 04: 基于 image_plugin_webai_nano_banana 复制实现 image_plugin_huimeng_nano_banana，对接 docs/require/huimeng-image-video-api.md，并与现有 6 个插件并存 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves alternatives considered.

**Date:** 2026-05-26
**Phase:** 04-image-plugin-webai-nano-banana-image-plugin-huimeng-nano-ban
**Areas discussed:** scope, task-flow, result-mapping, UI strategy, failure policy

---

## Scope

| Option | Description | Selected |
|--------|-------------|----------|
| A | 图片生成 only，严格对齐当前目标 | Yes |
| B | 图片+视频一起做 | |

**User's choice:** A
**Notes:** 首版先确保图片生成稳定闭环，避免阶段范围膨胀。

---

## Task Flow

| Option | Description | Selected |
|--------|-------------|----------|
| A | POST /api/v1/tasks + GET /api/v1/tasks/{task_id} 轮询 | Yes |
| B | 仅提交任务，不在插件内轮询 | |

**User's choice:** A
**Notes:** 按惠梦文档标准异步模式落地，插件内返回可直接使用的最终本地文件路径。

---

## Result Mapping

| Option | Description | Selected |
|--------|-------------|----------|
| A | 优先 result.image_urls，回退 result.image_url | Yes |
| B | 仅使用 result.image_url | |

**User's choice:** A
**Notes:** 兼容多图与单图结果结构，减少平台响应差异带来的失败。

---

## UI Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| A | 复用 webai UI 结构，仅替换平台必要字段 | Yes |
| B | 新增较多 huimeng 专属 UI 控件 | |

**User's choice:** A
**Notes:** 最小差异迁移，优先稳定与并存。

---

## Failure Policy

| Option | Description | Selected |
|--------|-------------|----------|
| A | failed/timeout 抛 PLUGIN_ERROR:::，并完整记录日志 | Yes |
| B | 失败时返回空列表不抛错 | |

**User's choice:** A
**Notes:** 禁止伪成功；可诊断性优先。

---

## the agent's Discretion

- 轮询间隔与超时默认值在计划阶段确定为保守稳定策略，并保持可配置。

## Deferred Ideas

- 视频生成链路
- Webhook 签名校验与回调被动通知链路
