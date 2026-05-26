---
status: investigating
trigger: "image_plugin_huimeng_nano_banana: 按模型动态构建params，请求参数以 docs/require/图像模型的params参数说明.md 为准"
created: "2026-05-26T06:55:23.716Z"
updated: "2026-05-26T06:55:23.716Z"
---

## Current Focus

hypothesis: 当前任务提交请求对不同模型复用同一套 params 组装逻辑，导致包含不适配字段、缺失必要字段或默认值/枚举不符合模型契约。
test: 对照 docs/require/图像模型的params参数说明.md 与 image_plugin_huimeng_nano_banana 中的请求构建代码，逐模型比对最终下发 params。
expecting: 能定位出模型参数映射缺失点（字段白名单、默认值、枚举范围、大小写规范、image 多图上限等）。
next_action: gather initial evidence
reasoning_checkpoint: null
tdd_checkpoint: null

## Symptoms

expected: 提交任务时 params 严格符合所选模型的参数契约。
actual: params 未按模型动态构建，存在跨模型参数混用风险。
errors: 暂未提供具体报错；当前以契约不一致为主要故障线索。
reproduction: 选择不同模型提交任务，检查请求体 params 与文档约定是否一致。
started: 现状问题（具体起始时间待补充）

## Eliminated

- hypothesis: 用户输入本身缺失导致请求失败
  reason: 问题描述指出核心在“按模型动态构建 params 的逻辑缺失/不完整”，非单次输入异常。

## Evidence

- timestamp: 2026-05-26T06:55:23.716Z
  source: F:/Projects/zz-image-plugins/docs/require/图像模型的params参数说明.md
  detail: 文档明确不同模型 params 字段、默认值、枚举范围存在差异，不能统一模板直传。

## Resolution

root_cause: null
fix: null
verification: null
files_changed: []
