# 图像模型的params参数说明

### 1. Image 2官方

Image 2 官方图像生成模型，支持文生图、图生图，支持low/medium/high质量和1k/2k/4k分辨率。

**请求示例**

```jsx
POST /api/v1/tasks
{
  "model": "image-2-official",
  "params": {
    "prompt": "你的提示词",
    "ratio": "auto",
    "quality": "medium",
    "resolution": "1k"
  }
}
```

**参数说明**

| **参数** | **类型** | **必填** | **说明** |
| --- | --- | --- | --- |
| image | [ "string", "array" ] | 否 | 参考图片URL，支持单图或多图(最多10张) |
| ratio | string | 否 | 宽高比可选值: auto | 1:1 | 2:3 | 3:2 | 3:4 | 4:3 | 4:5 | 5:4 | 9:16 | 16:9 | 21:9默认: 1:1 |
| prompt | string | 是 | 图像描述文本 |
| quality | string | 否 | 生成质量可选值: low | medium | high默认: medium |
| resolution | string | 否 | 输出分辨率可选值: 1k | 2k | 4k默认: 1k |

### 2.Image 2

高质量图像生成模型，支持文生图、图生图，支持多张参考图片，支持1K/2K/4K分辨率和质量调节。

**请求示例:**

```jsx
POST /api/v1/tasks
{
  "model": "image-2",
  "params": {
    "prompt": "你的提示词",
    "ratio": "16:9",
    "quality": "medium",
    "resolution": "2k"
  }
}
```

**参数说明**

| **参数** | **类型** | **必填** | **说明** |
| --- | --- | --- | --- |
| image | [ "string", "array" ] | 否 | 参考图片URL，支持单图或多图(最多14张) |
| ratio | string | 否 | 宽高比可选值: auto | 1:1 | 16:9 | 9:16 | 4:3 | 3:4 | 3:2 | 2:3 | 5:4 | 4:5 | 21:9 | 1:4 | 4:1 | 1:8 | 8:1默认: 1:1 |
| prompt | string | 是 | 图像描述文本 |
| resolution | string | 否 | 输出分辨率可选值: 1k | 2k | 4k默认: 1k |

### 3. NB 2 官方

Nano Banana 2 官方图像生成模型，支持文生图、图生图，支持1k/2k/4k分辨率。

**请求示例:**

```jsx
POST /api/v1/tasks
{
  "model": "nb-2-official",
  "params": {
    "prompt": "你的提示词",
    "ratio": "auto",
    "resolution": "1k"
  }
}
```

**参数说明:**

| **参数** | **类型** | **必填** | **说明** |
| --- | --- | --- | --- |
| image | [ "string", "array" ] | 否 | 参考图片URL，支持单图或多图(最多14张) |
| ratio | string | 否 | 宽高比可选值: auto | 1:1 | 16:9 | 9:16 | 4:3 | 3:4 | 3:2 | 2:3 | 5:4 | 4:5 | 21:9 | 1:4 | 4:1 | 1:8 | 8:1默认: 1:1 |
| prompt | string | 是 | 图像描述文本 |
| resolution | string | 否 | 输出分辨率可选值: 1k | 2k | 4k默认: 1k |

### 4. NB 2

Nano Banana 2 图像生成模型，支持文生图、图生图、多图参考，支持1K/2K/4K分辨率

**请求示例:**

```jsx
POST /api/v1/tasks
{
  "model": "nb-2",
  "params": {
    "prompt": "你的提示词",
    "ratio": "auto",
    "resolution": "1K"
  }
}
```

**参数说明:**

| **参数** | **类型** | **必填** | **说明** |
| --- | --- | --- | --- |
| image | [ "string", "array" ] | 否 | 参考图片URL，支持单图或多图(最多9张) |
| ratio | string | 否 | 宽高比可选值: auto | 1:1 | 16:9 | 9:16 | 4:3 | 3:4 | 3:2 | 2:3 | 5:4 | 4:5 | 21:9 | 1:4 | 4:1 | 1:8 | 8:1默认: auto |
| prompt | string | 是 | 图像描述文本 |
| resolution | string | 否 | 输出分辨率可选值: 1K | 2K | 4K默认: 1K |

### 5. NB Pro

Nano Banana Pro 图像生成模型，支持文生图、图生图、多图参考，支持1K/2K/4K分辨率。

**请求示例:**

```
POST /api/v1/tasks
{
  "model": "nb-pro",
  "params": {
    "prompt": "你的提示词",
    "ratio": "auto",
    "resolution": "1K"
  }
}
```

**参数说明:**

| **参数** | **类型** | **必填** | **说明** |
| --- | --- | --- | --- |
| image | [ "string", "array" ] | 否 | 参考图片URL，支持单图或多图(最多9张) |
| ratio | string | 否 | 宽高比可选值: auto | 1:1 | 16:9 | 9:16 | 4:3 | 3:4 | 3:2 | 2:3 | 5:4 | 4:5 | 21:9默认: auto |
| prompt | string | 是 | 图像描述文本 |
| resolution | string | 否 | 输出分辨率可选值: 1K | 2K | 4K默认: 1K |

### 6. NB Pro官方

Nano Banana Pro 官方图像生成模型，支持文生图、图生图，支持1k/2k/4k分辨率。

**请求示例:**

```jsx
POST /api/v1/tasks
{
  "model": "nb-pro-official",
  "params": {
    "prompt": "你的提示词",
    "ratio": "auto",
    "resolution": "1k"
  }
}
```

**参数说明:**

| **参数** | **类型** | **必填** | **说明** |
| --- | --- | --- | --- |
| image | [ "string", "array" ] | 否 | 参考图片URL，支持单图或多图(最多10张) |
| ratio | string | 否 | 宽高比可选值: auto | 1:1 | 3:2 | 2:3 | 3:4 | 4:3 | 4:5 | 5:4 | 9:16 | 16:9 | 21:9默认: 1:1 |
| prompt | string | 是 | 图像描述文本 |
| resolution | string | 否 | 输出分辨率可选值: 1k | 2k | 4k默认: 1k |

### 7. Z Image Turbo

阿里巴巴高速图像生成模型，擅长写实风格，出图速度快，支持横屏和竖屏两种画面方向。

**请求示例:**

```jsx
POST /api/v1/tasks
{
  "model": "z-image-turbo",
  "params": {
    "prompt": "你的提示词",
    "orientation": "横屏"
  }
}
```

**参数说明:**

### **参数说明**

| **参数** | **类型** | **必填** | **说明** |
| --- | --- | --- | --- |
| prompt | string | 是 | 图像描述文本 |
| orientation | string | 否 | 画面方向可选值: 横屏 | 竖屏默认: 横屏 |

### 8. Seedream 5.0 Lite

新一代图像生成模型，支持文生图、图生图、多图融合、联网搜索，最高3K分辨率。

**请求示例:**

```jsx
POST /api/v1/tasks
{
  "model": "seedream-5.0-lite",
  "params": {
    "prompt": "你的提示词",
    "ratio": "1:1",
    "resolution": "2K"
  }
}
```

**参数说明:**

| **参数** | **类型** | **必填** | **说明** |
| --- | --- | --- | --- |
| image | [ "string", "array" ] | 否 | 参考图片URL，支持单图或多图(最多14张) |
| ratio | string | 否 | 宽高比可选值: 1:1 | 4:3 | 3:4 | 16:9 | 9:16 | 3:2 | 2:3 | 21:9默认: 1:1 |
| prompt | string | 是 | 图像描述文本，建议不超过300个汉字或600个英文单词 |
| resolution | string | 否 | 分辨率可选值: 2K | 3K默认: 2K |
| output_format | string | 否 | 输出格式可选值: jpeg | png默认: jpeg |

### 9. Z Image Turbo

高质量图像生成模型，支持文生图、图生图、多图融合，最高4K分辨率。

**请求示例:**

```jsx
POST /api/v1/tasks
{
  "model": "seedream-4.5",
  "params": {
    "prompt": "你的提示词",
    "ratio": "1:1",
    "resolution": "2K"
  }
}
```

**参数说明:**

| **参数** | **类型** | **必填** | **说明** |
| --- | --- | --- | --- |
| image | [ "string", "array" ] | 否 | 参考图片URL，支持单图或多图(最多14张) |
| ratio | string | 否 | 宽高比可选值: 1:1 | 4:3 | 3:4 | 16:9 | 9:16 | 3:2 | 2:3 | 21:9默认: 1:1 |
| prompt | string | 是 | 图像描述文本，建议不超过300个汉字或600个英文单词 |
| resolution | string | 否 | 分辨率可选值: 2K | 4K默认: 2K |