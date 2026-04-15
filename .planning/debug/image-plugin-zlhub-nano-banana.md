---
status: root_cause_found
trigger: "image_plugin_zlhub_nano_banana 插件问题：实时日志无输出，但任务日志有；生成时报错 API 调用失败 HTTP 403 {\"error\":\"上游返回异常\"...}。请给出最快的排查与修复路径。"
created: "2026-04-15T07:46:51.703Z"
updated: "2026-04-15T08:18:00.000Z"
---

## Current Focus

hypothesis: 实时日志为空是因为日志缓冲是进程内内存结构，而任务日志走 SQLite 跨执行上下文可见；HTTP 403 来自当前请求路径/协议与 zlhub 实际放行接口不匹配（或该路径鉴权策略不同）
test: 对比 live_log/task_log 通信协议与 handle_action 对接；对比当前插件请求路径与参考实现请求路径
expecting: 若通信协议一致且 task_log 正常而 live_log 为空，则更可能是日志存储介质差异（内存 vs SQLite）；若当前使用 proxy/chat/completions 而参考实现使用 v1/images/generations，则 403 高概率由接口路径/策略差异触发
next_action: user_decision_fix_or_plan
reasoning_checkpoint: null
tdd_checkpoint: null

## Symptoms

expected: 实时日志持续输出；任务日志状态正确流转；成功生成并落盘图片
actual: 实时日志始终为空；任务日志有记录但失败；出现 HTTP 403
errors: API 调用失败: HTTP 403: {"error":"上游返回异常"...}
reproduction: 填 API Key 后直接文生图即可稳定复现
started: 首次加载到字字动画后即出现

## Eliminated

- 实时日志页与任务日志页前端通信协议不一致（已排除：两者均使用 window.opener.postMessage + __typetale_plugin + type=plugin_action，回包监听 type=action）
- handle_action 未实现 get_logs（已排除：main.py 明确支持 get_logs 并返回 {ok: True, logs}）

## Evidence

- timestamp: 2026-04-15T08:07:00.000Z
  source: F:/Projects/zz-image-plugins/image_plugin_zlhub_nano_banana/ui/live_log.html
  detail: 实时日志页面每 2 秒发送 get_logs(since_index)，协议与 task_log 页面一致

- timestamp: 2026-04-15T08:08:00.000Z
  source: F:/Projects/zz-image-plugins/image_plugin_zlhub_nano_banana/main.py
  detail: handle_action 包含 get_logs 分支并调用 get_buffered_logs；_BufferingHandler 将日志写入 _log_buffer（内存 deque）

- timestamp: 2026-04-15T08:10:00.000Z
  source: F:/Projects/zz-image-plugins/image_plugin_zlhub_nano_banana/main.py
  detail: 任务日志通过 SQLite 持久化（_log_task_result），与实时日志内存缓冲是两套链路

- timestamp: 2026-04-15T08:12:00.000Z
  source: F:/Projects/zz-image-plugins/image_plugin_zlhub_nano_banana/main.py
  detail: 当前请求使用 /zhonglian/api/v1/proxy/chat/completions，返回非 200 时直接抛出 HTTP 状态和响应文本

- timestamp: 2026-04-15T08:14:00.000Z
  source: F:/Projects/zz-image-plugins/nano_banana_plugin_geeknow/main.py
  detail: 参考实现的 Doubao 请求路径为 /v1/images/generations，协议与当前迁移版存在显著差异

## Specialist Review

- timestamp: 2026-04-15T08:16:00.000Z
  specialist_hint: python
  result: SUGGEST_CHANGE（先最小化修复）
  notes: 优先将“可观测性修复”和“403 修复”拆开验证。先让实时日志跨执行上下文可见（不要仅依赖进程内 deque），再最小改动对齐已验证可用的请求路径/载荷进行 A/B 对照，避免同时改多处导致定位失真。

## Resolution

root_cause: 实时日志依赖进程内 _log_buffer，而任务日志写入 SQLite；在宿主执行上下文分离时会出现“任务日志有、实时日志空”。同时当前迁移版请求走 /zhonglian/api/v1/proxy/chat/completions，与已知可用实现的 /v1/images/generations 不一致，触发上游 403（鉴权/白名单/协议路径不匹配）。
fix: 未应用（待用户选择）
verification: 已完成静态链路对比与实现差异比对；待运行验证修复
files_changed: [
  "F:/Projects/zz-image-plugins/.planning/debug/image-plugin-zlhub-nano-banana.md"
]
