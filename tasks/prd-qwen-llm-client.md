# PRD: Qwen LLM 客户端类

## Introduction

创建一个基于 DashScope SDK 的 Qwen LLM 客户端类，作为项目中调用阿里云通义千问模型的通用封装。该类提供简洁的 API 接口，支持同步调用、System Prompt 配置和参数自定义，为后续扩展多轮对话管理预留接口。

## Goals

- 提供简洁易用的 Qwen LLM 调用接口
- 封装 DashScope SDK 的复杂性，对外暴露清晰的 API
- 支持灵活的参数配置（temperature、top_p、max_tokens 等）
- 支持自定义 System Prompt
- 为后续多轮对话管理预留扩展点
- 遵循项目现有的代码规范和架构模式

## User Stories

### US-001: 创建 QwenClient 基础类
**Description:** 作为开发者，我需要一个封装 DashScope SDK 的客户端类，以便统一管理 Qwen LLM 的调用。

**Acceptance Criteria:**
- [ ] 在 `app/core/` 目录下创建 `qwen_client.py` 文件
- [ ] 类名为 `QwenClient`，支持通过构造函数配置 API Key 和默认模型
- [ ] API Key 支持从环境变量 `DASHSCOPE_API_KEY` 读取
- [ ] 默认模型为 `qwen-flash`
- [ ] `mypy` 类型检查通过

### US-002: 实现同步调用方法
**Description:** 作为开发者，我需要一个同步调用方法来发送请求并获取 LLM 响应。

**Acceptance Criteria:**
- [ ] 实现 `chat(messages: list[dict]) -> str` 方法
- [ ] 支持传入 messages 列表（包含 role 和 content）
- [ ] 返回模型生成的文本内容
- [ ] 正确处理 HTTP 状态码，非 200 时抛出异常
- [ ] `mypy` 类型检查通过

### US-003: 支持 System Prompt 配置
**Description:** 作为开发者，我需要能够配置 System Prompt 来定义 LLM 的行为。

**Acceptance Criteria:**
- [ ] 构造函数支持 `system_prompt: str | None` 参数
- [ ] 调用时自动将 system_prompt 作为第一条 system 消息插入
- [ ] 支持在单次调用时覆盖默认 system_prompt
- [ ] `mypy` 类型检查通过

### US-004: 支持生成参数配置
**Description:** 作为开发者，我需要能够配置生成参数来控制模型输出。

**Acceptance Criteria:**
- [ ] 支持配置 `temperature`（默认 0.7）
- [ ] 支持配置 `top_p`（默认 0.9）
- [ ] 支持配置 `max_tokens`（默认 2000）
- [ ] 参数可在构造函数中设置默认值，也可在单次调用时覆盖
- [ ] `mypy` 类型检查通过

### US-005: 提供便捷的单轮对话方法
**Description:** 作为开发者，我需要一个简化的方法来进行单轮对话。

**Acceptance Criteria:**
- [ ] 实现 `ask(prompt: str) -> str` 方法
- [ ] 内部将 prompt 封装为 user message 并调用 `chat` 方法
- [ ] 返回模型生成的文本内容
- [ ] `mypy` 类型检查通过

### US-006: 添加依赖到项目配置
**Description:** 作为开发者，我需要将 dashscope SDK 添加到项目依赖中。

**Acceptance Criteria:**
- [ ] 在 `pyproject.toml` 中添加 `dashscope` 依赖
- [ ] 指定最低版本要求 `>=1.20.0`

## Functional Requirements

- FR-1: `QwenClient` 类必须封装 `dashscope.Generation.call` API
- FR-2: 必须使用 `result_format='message'` 格式化响应
- FR-3: API Key 必须支持环境变量和显式传入两种方式
- FR-4: 所有公开方法必须有完整的类型注解
- FR-5: 错误响应必须转换为 Python 异常，包含错误码和错误信息
- FR-6: 类设计必须为后续添加流式调用和多轮对话管理预留扩展点

## Non-Goals

- 本次不实现流式（streaming）调用
- 本次不实现多轮对话历史管理（仅预留接口）
- 不实现自动重试机制
- 不实现连接池或并发控制
- 不实现 Function Calling / Tool Use 功能

## Technical Considerations

### DashScope SDK 使用模式

```python
from http import HTTPStatus
from dashscope import Generation

response = Generation.call(
    model="qwen-flash",
    messages=[
        {'role': 'system', 'content': 'You are a helpful assistant'},
        {'role': 'user', 'content': 'Hello'}
    ],
    result_format='message',
    temperature=0.7,
    top_p=0.9,
    max_tokens=2000
)

if response.status_code == HTTPStatus.OK:
    content = response.output.choices[0].message.content
else:
    raise Exception(f"Error: {response.code} - {response.message}")
```

### 文件位置

- 主类文件: `app/core/qwen_client.py`
- 可选：异常定义文件: `app/core/exceptions.py`

### 依赖

- `dashscope>=1.20.0`

## Success Metrics

- 类可以成功调用 Qwen 模型并返回响应
- 所有公开 API 有完整的类型注解
- `mypy` 类型检查通过
- 代码符合项目 `ruff` 规范

## Open Questions

1. 是否需要为不同环境（dev/test/prod）配置不同的默认模型？
2. 是否需要添加请求日志记录？
3. 后续多轮对话管理是否需要持久化存储？
