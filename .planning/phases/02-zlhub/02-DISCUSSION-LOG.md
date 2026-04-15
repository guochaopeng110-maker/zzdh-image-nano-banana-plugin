# Phase 2: zlhub 出图主链路闭环 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-15
**Phase:** 02-zlhub
**Areas discussed:** 请求字段对齐

---

## 请求字段对齐

| Option | Description | Selected |
|--------|-------------|----------|
| 固定模板+默认值 | 始终发送核心字段并使用稳定默认值，行为最可控 | ✓ |
| 最小必填+按需附加 | 仅发最小字段，其他按配置附加 | |
| 沿用现有分支差异 | 继续按模型分支各自组织字段 | |

**User's choice:** 固定模板+默认值
**Notes:** 以稳定性优先，减少不同配置组合下的不确定性。

---

| Option | Description | Selected |
|--------|-------------|----------|
| 严格文档字段 | 以文档字段为唯一口径 | ✓ |
| 文档字段+历史别名兼容 | 内部兼容旧别名 | |
| 保持当前命名不改 | 延续现有命名 | |

**User's choice:** 严格文档字段
**Notes:** 减少长期维护和排障歧义。

---

| Option | Description | Selected |
|--------|-------------|----------|
| 完全对齐文档示例 | 默认值按文档示例收敛 | ✓ |
| 尽量少默认，仅填必需 | 可选字段不默认 | |
| 按现有插件默认优先 | 先沿用旧默认再补齐 | |

**User's choice:** 完全对齐文档示例
**Notes:** 首版优先“稳定可预测”。

---

| Option | Description | Selected |
|--------|-------------|----------|
| 不发送 image | 无图不带字段 | |
| 发送空数组/空字符串 | 字段始终存在但为空 | |
| 按模型分支决定 | 不同分支使用不同规则 | |

**User's choice:** 发送空值，并进一步锁定为“按输入类型自动”
**Notes:** 细化决策：文本模式 `""`，图像输入模式 `[]`。

---

| Option | Description | Selected |
|--------|-------------|----------|
| 空字符串 "" | 与文档 image:string 一致 | |
| 空数组 [] | 与多图输入统一 | |
| 按输入类型自动 | 文本用""，图像输入用[] | ✓ |

**User's choice:** 按输入类型自动
**Notes:** 在类型一致性与输入场景兼容之间折中。

---

| Option | Description | Selected |
|--------|-------------|----------|
| 固定文档路径 | 统一调用文档指定路径 | ✓ |
| 可切换两种路径 | 保留旧路径并可配置切换 | |
| 保持当前路径 | 继续现有端点方式 | |

**User's choice:** 固定文档路径
**Notes:** 接口地址统一，减少环境差异引发的问题。

---

## Claude's Discretion

- 响应解析兼容范围
- 多图落盘与部分失败策略
- 失败反馈文案与分类映射

## Deferred Ideas

- 响应解析策略（未展开）
- 多图落盘规则（未展开）
- 失败反馈口径（未展开）
