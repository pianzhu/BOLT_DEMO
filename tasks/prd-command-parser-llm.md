# PRD: 智能家居用户指令解析器（LLM JSON Parser）

## 1. Introduction / Overview

新增一个“智能家居指令解析器”模块：将用户的中文自然语言指令解析为严格的 JSON 数组（不输出解释/代码块/多余文本），供后续执行层（设备控制/查询）消费。

该功能必须复用仓库现有的 LLM 调用工具（`app/core/qwen_client.py` 的 `QwenClient`），并对模型输出做严格校验，确保下游永远拿到符合数据契约的结构。

## 2. Goals

- 将用户指令解析为符合契约的 JSON 数组（字段白名单 + 枚举校验 + 失败显式兜底）。
- 支持多动作/多目标拆分（按语序输出；每个对象只含 1 动作 + 1 目标）。
- 保证输出紧凑（不换行、字段间不需要空格），便于日志/存储/对比。
- 可验证：提供单元测试覆盖核心校验与典型解析样例。

## 3. User Stories

### US-001: 以库函数形式提供解析能力
**Description:** 作为开发者，我希望通过一个 Python 库函数调用解析器，以便在服务/脚本中复用解析逻辑。

**Acceptance Criteria:**
- [ ] 提供 `parse_commands(client, text, *, allowed_categories=..., temperature=..., top_p=..., max_tokens=...) -> list[dict]`
- [ ] 返回的每个对象只包含允许字段（`a,s,n,t,q,c`），且可被序列化为紧凑 JSON
- [ ] `uv run python -m pytest` 通过

### US-002: 严格校验模型输出并提供标准兜底
**Description:** 作为系统，我希望任何不合法输出都能被拦截并返回标准结果，避免下游处理异常或脏数据。

**Acceptance Criteria:**
- [ ] 输出不是 JSON 数组 / 元素不是对象 / 多余字段 / 必填字段缺失 / 枚举不合法 / `c` 非整数等场景 => 返回标准 UNKNOWN 数组
- [ ] 解析失败会记录结构化日志（至少包含：输入文本、失败类型）
- [ ] 单测覆盖上述失败场景

### US-003: 指代词处理（V1 不支持 @last、多轮上下文）
**Description:** 作为对话系统，我希望当用户使用“它/那个/刚才那个”等指代词且缺少明确目标时，系统保留动作但输出目标不确定，以便上层追问。

**Acceptance Criteria:**
- [ ] 当输入出现指代词且缺少明确目标时，输出对象保留动作 `a`，并使用：`s="*"`, `n="*"`, `t="Unknown"`, `q="one"`（可选 `c`）
- [ ] V1 明确不支持 `n="@last"`（避免“只看上轮设备”的错误设计）
- [ ] 将“5 轮历史上下文 + 消歧策略 + 测试集”作为后续专题（本期不实现）

## 4. Functional Requirements

- FR-1: 必须复用 `QwenClient` 发起模型调用（不新增供应商 SDK）。
- FR-2: System Prompt 必须遵循如下契约（与产品约定一致）：
  - 只输出 JSON 数组，不解释、不要代码块、不要多余文本
  - 输出尽量紧凑：不要换行，字段间不需要空格
  - 数组元素对象字段只允许（按顺序输出）：`a,s,n,t,q,c`
  - `a`（动作，中文）：打开/关闭；设置用 `设置<属性>=<值>`；查询用 `查询<属性>`；静音/取消静音
  - `s`（房间）：未知 `"*"`；多房间用 `","`；排除房间用 `"!"` 前缀（例 `"*,!卧室"`）
  - `n`（设备名）：去掉房间词，保留修饰词；不确定用 `"*"`；泛指类型（如"所有灯""三个插座"）填该类型的中文原文（如"灯""插座""空调""窗帘"），不要用 `"*"`
  - `t`（类型）：仅限允许枚举；不确定用 `"Unknown"`
  - `q`：`one|all|any|except`；泛指类型默认 `all`；不确定用 `one`
  - `c`：仅明确数量时为整数；否则不输出该字段
  - 多动作/多目标：拆成多个对象，按语序输出；每个对象只含一个动作 + 一个目标
  - 完全无法解析：输出标准 UNKNOWN 数组
- FR-3: `ALLOWED_CATEGORIES` 使用代码常量（可被注入覆盖），V1 枚举为：
  - `AirConditioner, Blind, Charger, Fan, Hub, Light, NetworkAudio, Unknown, Switch, Television, Washer, SmartPlug`
- FR-4: 解析器必须做严格校验并在失败时返回：
  - `[{"a":"UNKNOWN","s":"*","n":"*","t":"Unknown","q":"one"}]`
- FR-5: `a` 字段校验规则（前缀匹配策略）：
  - 固定动作精确匹配：`打开`、`关闭`、`静音`、`取消静音`
  - 前缀匹配：以 `设置` 或 `查询` 开头，且前缀后必须有内容（即 `设置` 单独出现不合法，`设置亮度=50` 合法）
  - 不在上述范围内的动作值视为非法
- FR-6: `s` 字段校验规则（V1 仅非空字符串）：
  - V1 只校验为非空字符串，不做房间词表匹配或格式校验
  - 后续版本可增加房间词表白名单或格式规则（如 `"*,!卧室"` 的结构校验）
- FR-7: JSON 提取策略（两级回退）：
  - 第一步：对 LLM 原始输出 `strip()` 后直接 `json.loads()`
  - 第二步：若第一步失败，用正则 `\[.*\]`（DOTALL）提取第一个 `[...]` 片段后再 `json.loads()`
  - 两步均失败则视为解析失败，返回标准 UNKNOWN 兜底
- FR-8: 解析失败日志规范：
  - 三个失败点统一使用 `logger.warning("command_parser.parse_failed", extra={...})`
  - `failure_type` 取值：`"llm_error"`（LLM 调用异常）/ `"json_parse_error"`（JSON 提取失败）/ `"validation_failed"`（校验不通过）
  - `input_text`：用户原始输入
  - `raw_response`：LLM 原始输出（截断 500 字符，仅 `json_parse_error` 和 `validation_failed` 包含）

## 5. Non-Goals (Out of Scope)

- 不实现 `@last`（不引入“只看上轮设备”的上下文捷径）。
- 不实现“5 轮历史上下文 + 消歧策略 + 测试集”（后续专题）。
- 不做自动修复重试（repair prompt）与多次调用兜底（本期以严格校验为主）。
- 不实现执行层（开灯/关灯/设置/查询的真实设备控制）。

## 6. Design Considerations (Optional)

- 输出建议通过统一的 `compact_json_dumps()` 序列化：`separators=(",", ":")`，避免空格/换行。
- 校验建议“白名单字段 + 必填字段 + 枚举 + 类型”组合，避免 silent failure。

## 7. Technical Considerations (Optional)

- 语言栈：Python；测试框架：pytest；依赖管理：uv。
- 模型调用参数建议默认：`temperature=0`（提高确定性）。
- 需要在代码中保留清晰的扩展点：未来将输入历史（5 轮）作为额外 messages 注入。

## 8. Success Metrics

- 单测覆盖关键成功/失败路径；解析器不会向上抛出未捕获异常。
- 模型输出不合规时，系统稳定返回标准兜底，不污染下游执行。

## 9. Open Questions

- `c` 的合法范围：是否允许 `0`？（V1 暂按"整数"校验，范围细化后续补充）
  - **已决定（V1）：** `c` 校验为 `int` 且非 `bool`，允许 `0` 和负数；范围约束后续版本补充
- 房间词表是否需要严格匹配已知房间名？（V1 不做词表校验，仅校验格式）
  - **已决定（V1）：** `s` 仅校验非空字符串，不做房间词表匹配（见 FR-6）
- "指代词"触发规则：是否需要更系统的中文规则/词典？（V1 由模型按 prompt 处理；后续可补充 deterministic 规则与测试集）
- `a` 字段校验策略：精确匹配 vs 前缀匹配？
  - **已决定（V1）：** 混合策略——固定动作精确匹配 + `设置`/`查询` 前缀匹配（见 FR-5）

## 10. Implementation Notes

### 文件结构
| 文件 | 操作 | 说明 |
|------|------|------|
| `app/services/command_parser.py` | 新建 | 常量、校验函数、system prompt、`parse_commands()` |
| `tests/unit/test_command_parser.py` | 新建 | 校验 + 解析的全部单元测试 |

不修改现有文件。

### 任务拆分
- T1: 常量定义 + 校验函数（`_is_valid_action`, `_is_valid_nonempty_str`, `_is_valid_category`, `_is_valid_quantity`, `_is_valid_count`, `_validate_command`, `_validate_commands`）+ 工具函数（`compact_json_dumps`, `_fallback`）
- T2: System Prompt（模块常量 `_SYSTEM_PROMPT`，使用 `{categories}` 占位符）+ JSON 提取（`_extract_json`）+ 核心函数 `parse_commands()`
- T3: 单元测试（校验函数测试 + JSON 提取测试 + parse_commands 集成测试 mock LLM）

### 扩展点
- 未来 5 轮上下文：改用 `client.chat()` 传入 history messages。当前仅留注释标记，不写代码。

### 验证方式
```bash
uv run python -m pytest tests/unit/test_command_parser.py -v
```

