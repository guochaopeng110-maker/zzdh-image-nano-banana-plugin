---
status: testing
phase: 04-image-plugin-webai-nano-banana-image-plugin-huimeng-nano-ban
source: [04-01-SUMMARY.md]
started: 2026-05-26T04:40:00Z
updated: 2026-05-26T04:42:00Z
---

## Current Test

number: 2
name: 参数配置与模型下拉
expected: |
  插件配置页可编辑 `api_key/base_url/model/request_timeout/download_timeout/poll_interval_ms/poll_timeout_ms`，
  模型下拉包含文档中的 9 个图片模型标识。
awaiting: user response

## Tests

### 1. 插件并存识别
expected: 在字字动画宿主中，插件列表可看到独立的 `Image Relay Plugin - huimeng`，且不影响已有 6 个插件的加载和可用性。
result: pass

### 2. 参数配置与模型下拉
expected: 插件配置页可编辑 `api_key/base_url/model/request_timeout/download_timeout/poll_interval_ms/poll_timeout_ms`，模型下拉包含文档中的 9 个图片模型标识。
result: [pending]

### 3. 异步提交与轮询完成
expected: 触发生成后，插件按“提交任务 -> 轮询状态”流程执行，任务状态从 running 进入 success 或 failed，日志可见轮询状态变化。
result: [pending]

### 4. 图片结果提取策略
expected: completed 响应中优先读取 `result.image_urls`，为空时回退 `result.image_url`，单图/多图均可继续下载链路。
result: [pending]

### 5. 本地落盘与路径返回
expected: 成功生成后返回本地绝对路径列表，文件真实存在于 output_dir，多图时返回全部成功项。
result: [pending]

### 6. 失败分支可诊断
expected: task failed、轮询超时、空结果等情况会抛 `PLUGIN_ERROR:::`（或 `NO_RETRY:::`），并在任务日志记录失败原因。
result: [pending]

## Summary

total: 6
passed: 1
issues: 0
pending: 5
skipped: 0
blocked: 0

## Gaps

[none yet]
