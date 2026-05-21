# webai api

WebAI API 提供兼容 OpenAI 格式的 RESTful API。

# **1. 基础信息**

- **Base URL**: `http://localhost:8316`
- **认证方式**: Bearer Token

### **请求头**

`Authorization: Bearer sk-your-secret-key
Content-Type: application/json`

### ***可用的图片模型**
1. gemini-3.1-flash-image-preview
2. gemini-3-pro-image-preview-2k
3. flux-2-pro
4. flux-2-max
5. seedream-5.0-lite
6. seedream-4.5
7. qwen-image-2.0-pro
8. grok-imagine-image-pro
9. gpt-image-1.5-high-fidelity
10. chatgpt-image-latest-high-fidelity

### ***可用的文本模型**
1. gemini-3-flash
2. gemini-2.5-pro
3. claude-sonnet-4-6
4. grok-4.1
5. glm-5.1
6. minimax-2.7
7. qwen3.5-max-preview
8. gpt-5.2
9. gpt-5.4
10. deepseek-v3.2

# **2. API 端点列表**

### **OpenAI 兼容接口**

| **方法** | **端点** | **说明** |
| --- | --- | --- |
| POST | `/v1/chat/completions` | 对话生成 |
| GET | `/v1/models` | 获取模型列表 |
| GET | `/v1/cookies` | 获取 Cookie |

# **3.错误响应**

所有 API 错误返回统一格式：

```jsx
{
  "error": {
    "message": "错误描述",
    "type": "error_type",
    "code": "ERROR_CODE"
  }
}
```

### **常见错误码**

| **HTTP 状态码** | **错误类型** | **说明** |
| --- | --- | --- |
| 401 | `unauthorized` | 认证失败 |
| 400 | `invalid_request` | 请求参数错误 |
| 404 | `not_found` | 资源不存在 |
| 429 | `rate_limit` | 请求过多 |
| 500 | `internal_error` | 服务器内部错误 |
| 503 | `service_unavailable` | 服务不可用 |

# **4.流式响应**

对于 `stream: true` 的请求，响应使用 Server-Sent Events (SSE) 格式：

```jsx
data: {"id":"...","object":"chat.completion.chunk",...}

: keep-alive

data: {"id":"...","object":"chat.completion.chunk",...}

data: [DONE]
```

**心跳保活**

流式请求会自动发送心跳包防止连接超时，格式取决于配置的 `keepalive.mode`。

# **5.Chat Completions**

对话生成接口，兼容 OpenAI Chat Completions API。

## **5.1.端点**

`POST /v1/chat/completions`

## **5.2.请求参数**

| **参数** | **类型** | **必填** | **说明** |
| --- | --- | --- | --- |
| `model` | string | ✅ | 模型名称 |
| `messages` | array | ✅ | 消息列表 |
| `stream` | boolean | ❌ | 是否启用流式响应（推荐开启） |

### **messages 格式**

```jsx
{
  "messages": [
    {
      "role": "user",
      "content": "生成一只可爱的猫"
    }
  ]
}
```

### **多模态请求（图生图）**

```jsx
{
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "让这张图片更加鲜艳"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/jpeg;base64,/9j/4AAQ..."
          }
        }
      ]
    }
  ]
}
```

## **5.3.图片限制**

| **限制项** | **说明** |
| --- | --- |
| 支持格式 | PNG, JPEG, GIF, WebP |
| 数量限制 | 默认 5 张，最大 10 张 |
| 数据格式 | Base64 Data URL (`data:image/jpeg;base64,...`) |
| 自动转换 | 服务器会自动转换为 JPG 格式 |

## **5.4.非流式响应**

### **请求示例**

```jsx
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-key" \
  -d '{
    "model": "gemini-3-pro-image-preview",
    "messages": [
      {
        "role": "user",
        "content": "generate a cat"
      }
    ]
  }'
```

### **响应示例**

```jsx
{
  "id": "chatcmpl-1732374740123",
  "object": "chat.completion",
  "created": 1732374740,
  "model": "gemini-3-pro-image-preview",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "![generated](data:image/jpeg;base64,/9j/4AAQ...)"
      },
      "finish_reason": "stop"
    }
  ]
}
```

## **5.5.流式响应**

**推荐使用**

流式模式包含心跳保活机制，可以避免长时间生成导致的连接超时。

### **请求示例**

```jsx
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-key" \
  -d '{
    "model": "gemini-3-pro-image-preview",
    "stream": true,
    "messages": [
      {
        "role": "user",
        "content": "generate a cat"
      }
    ]
  }'
```

### **响应示例**

```jsx
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1732374740,"model":"gemini-3-pro-image-preview","choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":null}]}

: keep-alive

: keep-alive

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1732374740,"model":"gemini-3-pro-image-preview","choices":[{"index":0,"delta":{"content":"![generated](data:image/jpeg;base64,/9j/4AAQ...)"},"finish_reason":"stop"}]}

data: [DONE]
```

## **5.6.错误处理**

### **队列已满 (429)**

```jsx
{
  "error": {
    "message": "队列已满",
    "type": "rate_limit_exceeded",
    "code": "QUEUE_FULL"
  }
}
```

**解决方案**

启用流式模式 (`stream: true`) 可以无限排队，避免 429 错误。

### **模型不支持 (400)**

```jsx
{
  "error": {
    "message": "没有 Worker 支持模型: invalid-model",
    "type": "invalid_request_error",
    "code": "MODEL_NOT_FOUND"
  }
}
```
