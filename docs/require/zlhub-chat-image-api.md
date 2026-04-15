# zlhub图片/文本API

## 1.1 接口概述

- **URL**: http://zlhub.xiaowaiyou.cn/zhonglian/api/v1/proxy/chat/completions
- **Method**: `POST`
- **Content-Type**: `application/json`

## 1.2 请求参数

### Header 参数

| **参数名** | **类型** | **必填** | **说明** |
| --- | --- | --- | --- |
| Authorization | string | 是 | 鉴权 Token，格式为 Bearer <token> |
| Content-Type | string | 是 | 固定为 application/json |

### Body 参数

请求体为 JSON 格式，包含以下字段：

| **参数名** | **类型** | **必填** | **说明** |
| --- | --- | --- | --- |
| model | string | 是 | 调用的具体模型名称，例如 doubao-seed-2.0-pro |
| stream | boolean | 否 | 是否开启流式响应，默认为 false |
| messages | array | 是 | 对话上下文或输入内容 |

### `messages` 数组元素说明

| **参数名** | **类型** | **必填** | **说明** |
| --- | --- | --- | --- |
| role | string | 是 | 角色，例如 user (用户), assistant (助手), system (系统) |
| content | array | 是 | 消息内容列表 |

### `content` 数组元素说明

| **参数名** | **类型** | **必填** | **说明** |
| --- | --- | --- | --- |
| type | string | 是 | 内容类型，例如 input_text |
| text | string | 是 | 具体的文本内容 |

## 1.3 请求示例

```
curl -X POST http://zlhub.xiaowaiyou.cn/zhonglian/api/v1/proxy/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
      "model": "qwen3.5-plus",
      "stream": true,
      "messages": [
        {
          "role": "user",
          "content": "你好，请介绍一下你自己。"
        }
      ]
    }'
```

## 1.4 响应示例

```
{
  "id": "chatcmpl-af98b1c4-7cbb-978f-9ec4-6dc51607313a",
  "model": "qwen3.5-plus",
  "usage": {
    "total_tokens": 734,
    "prompt_tokens": 16,
    "completion_tokens": 718,
    "prompt_tokens_details": {
      "text_tokens": 16
    },
    "completion_tokens_details": {
      "text_tokens": 718,
      "reasoning_tokens": 301
    }
  },
  "object": "chat.completion",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "你好！我是 Qwen3.5，阿里巴巴最新推出的通义千问大语言模型。相比之前的版本，我在多个方面进行了显著升级，旨在更精准地理解你的需求并提供高效、专业的支持。以下是我的核心能力亮点：\n\n1. **超长上下文与精准理解**  \n   原生支持 256K 上下文窗口，无论是数十万字的文档、长视频字幕，还是复杂的多轮对话，我都能完整把握内容脉络，精准定位关键信息。\n\n2. **多语言与跨模态能力**  \n   支持全球 100+ 语言流畅交互，并具备深度视觉解析能力：可分析图表、公式、科学图示，甚至从图片中提取文字（OCR），结合文本进行综合推理。\n\n3. **逻辑与代码全栈赋能**  \n   数学计算、因果推理等逻辑任务更严谨；同时能生成、调试复杂代码，支持前端页面直接生成，并理解多步骤开发流程。\n\n4. **自主任务规划与执行**  \n   可独立规划多步骤任务（如数据检索→分析→可视化），通过调用工具或代码完成闭环操作，例如自动整理表格、生成报告或操作图形界面。\n\n5. **专业领域深度优化**  \n   在医疗、法律等垂直领域经过专项训练，能提供符合行业规范的建议；对话与角色扮演更自然，指令遵循度显著提升。\n\n6. **高效架构与知识时效**  \n   采用混合注意力机制与高稀疏度 MoE 结构，推理速度与资源效率大幅优化；知识更新至 2026 年，确保信息时效性。\n\n**举个实际场景**：  \n若你需要分析一份百页英文财报，我可快速提取关键数据、对比历史趋势、生成可视化图表，并用中文总结风险点；若你提供一张手写公式图片，我能识别内容并推导解题步骤。\n\n需要处理具体任务或深入了解某项能力？欢迎随时告诉我！ 😊"
      },
      "finish_reason": "stop"
    }
  ],
  "created": 1773915735
}
```

# 图像生成

## 2.1 接口概述

- **URL**: http://zlhub.xiaowaiyou.cn/zhonglian/api/v1/proxy/chat/completions
- **Method**: `POST`
- **Content-Type**: `application/json`

## 2.2 请求参数

### Header 参数

| **参数名** | **类型** | **必填** | **说明** |
| --- | --- | --- | --- |
| Authorization | string | 是 | 鉴权 Token，格式为 Bearer <token> |
| Content-Type | string | 是 | 固定为 application/json |

### Body 参数

请求体为 JSON 格式，包含以下字段：

| **参数名** | **类型** | **必填** | **说明** |
| --- | --- | --- | --- |
| model | string | 是 | 调用的具体模型名称，例如 doubao-seed-2.0-pro |
| prompt | string | 是 | 是否开启流式响应，默认为 false |
| image | string | 否 | 对话上下文或输入内容 |
| sequential_image_generation | string | 否 | 图像生成模式 |
| response_format | string | 否 | 响应格式 |
| size | string | 否 | 大小 |
| stream | string | 否 | 是否流式 |
| watermark | bool | 否 | 水印 |

## 2.3 请求示例

```
curl -X POST http://zlhub.xiaowaiyou.cn/zhonglian/api/v1/proxy/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer xxxx" \
  -d '{
    "model": "doubao-seedream-5.0-lite",
    "prompt": "星际穿越，黑洞，黑洞里冲出一辆快支离破碎的复古列车，抢视觉冲击力，电影大片，末日既视感，动感，对比色，oc渲染，光线追踪，动态模糊，景深，超现实主义，深蓝，画面通过细腻的丰富的色彩层次塑造主体与场景，质感真实，暗黑风背景的光影效果营造出氛围，整体兼具艺术幻想感，夸张的广角透视效果，耀光，反射，极致的光影，强引力，吞噬",
    "sequential_image_generation": "disabled",
    "response_format": "url",
    "size": "2K",
    "stream": false,
    "watermark": true
}'
```

## 2.4 响应示例

```
{
    "model": "doubao-seedream-5-0-260128",
    "created": 1773917302,
    "data": [
        {
            "url": "https://ark-acg-cn-beijing.tos-cn-beijing.volces.com/doubao-seedream-5-0/0217739172732536061aa40146dbf4d117b0497e84060d7283ce3_0.jpeg?X-Tos-Algorithm=TOS4-HMAC-SHA256&X-Tos-Credential=AKLTYWJkZTExNjA1ZDUyNDc3YzhjNTM5OGIyNjBhNDcyOTQ%2F20260319%2Fcn-beijing%2Ftos%2Frequest&X-Tos-Date=20260319T104822Z&X-Tos-Expires=86400&X-Tos-Signature=c2d2852cef3ad8f0382ad2f8a14437e9d6c514d084fef8e9a6867613fd85f415&X-Tos-SignedHeaders=host",
            "size": "3136x1312"
        }
    ],
    "usage": {
        "generated_images": 1,
        "output_tokens": 16072,
        "total_tokens": 16072
    },
    "max_output_tokens": 16072
}
```