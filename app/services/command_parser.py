from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

ALLOWED_CATEGORIES: tuple[str, ...] = (
    "AirConditioner",
    "Blind",
    "Charger",
    "Fan",
    "Hub",
    "Light",
    "NetworkAudio",
    "Unknown",
    "Switch",
    "Television",
    "Washer",
    "SmartPlug",
)

ALLOWED_FIELDS = ("a", "s", "n", "t", "q", "c")
REQUIRED_FIELDS = ("a", "s", "n", "t", "q")
VALID_FIXED_ACTIONS = {"打开", "关闭", "静音", "取消静音"}
VALID_ACTION_PREFIXES = ("设置", "查询")
VALID_QUANTITIES = {"one", "all", "any", "except"}
_FALLBACK_COMMAND = {"a": "UNKNOWN", "s": "*", "n": "*", "t": "Unknown", "q": "one"}

# 通过提示词约束输出形状，便于后续做严格校验。
_SYSTEM_PROMPT = """
你是智能家居用户指令解析器。
请严格遵守以下规则：
1) 只输出 JSON 数组，不解释、不要代码块、不要多余文本。
2) 输出尽量紧凑：不要换行，字段间不需要空格。
3) 数组元素对象字段只允许（按顺序输出）：a,s,n,t,q,c。
4) a（动作）：固定动作仅可为 打开/关闭/静音/取消静音；
   设置动作必须是 设置<属性>=<值>；查询动作必须是 查询<属性>。
5) s（房间）：未知用 "*"；多房间可用 ","；排除房间用 "!" 前缀。
6) n（设备名）：未知用 "*"；泛指类型使用中文原文（如 灯/插座/空调/窗帘）。
7) t（类型）只能是：{categories}；不确定用 Unknown。
8) q 只能是 one/all/any/except；泛指类型默认 all；不确定用 one。
9) c 仅在数量明确时输出为整数，否则不要输出该字段。
10) 多动作/多目标要拆成多个对象并按语序输出；每个对象仅含一个动作和一个目标。
11) 指代词（它/那个/刚才那个）且目标不明确时，保留动作，输出 s="*", n="*", t="Unknown", q="one"。
12) 完全无法解析时输出：[{{"a":"UNKNOWN","s":"*","n":"*","t":"Unknown","q":"one"}}]。
""".strip()


def compact_json_dumps(payload: Any) -> str:
    """输出紧凑 JSON，避免无意义空白。"""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _fallback() -> list[dict[str, Any]]:
    """解析失败时返回统一兜底结构。"""
    return [dict(_FALLBACK_COMMAND)]


def _truncate_raw_response(raw_response: Any) -> str:
    return str(raw_response)[:500]


def _is_valid_action(value: object) -> bool:
    if not isinstance(value, str):
        return False

    if value in VALID_FIXED_ACTIONS:
        return True

    for prefix in VALID_ACTION_PREFIXES:
        if value.startswith(prefix):
            return len(value) > len(prefix)

    return False


def _is_valid_nonempty_str(value: object) -> bool:
    return isinstance(value, str) and value != ""


def _is_valid_category(value: object, allowed_categories: set[str]) -> bool:
    return isinstance(value, str) and value in allowed_categories


def _is_valid_quantity(value: object) -> bool:
    return isinstance(value, str) and value in VALID_QUANTITIES


def _is_valid_count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_command(command: object, allowed_categories: set[str]) -> bool:
    if not isinstance(command, dict):
        return False

    command_keys = set(command)
    if command_keys - set(ALLOWED_FIELDS):
        return False

    if not set(REQUIRED_FIELDS).issubset(command_keys):
        return False

    if not _is_valid_action(command.get("a")):
        return False

    if not _is_valid_nonempty_str(command.get("s")):
        return False

    if not _is_valid_nonempty_str(command.get("n")):
        return False

    if not _is_valid_category(command.get("t"), allowed_categories):
        return False

    if not _is_valid_quantity(command.get("q")):
        return False

    if "c" in command and not _is_valid_count(command["c"]):
        return False

    return True


def _validate_commands(commands: object, allowed_categories: set[str]) -> bool:
    if not isinstance(commands, list):
        return False

    if not commands:
        return False

    return all(_validate_command(command, allowed_categories) for command in commands)


def _extract_json(raw_response: object) -> list[dict[str, Any]] | None:
    # 两阶段解析：先整段 JSON，再从包裹文本里提取数组。
    if not isinstance(raw_response, str):
        return None

    try:
        parsed = json.loads(raw_response.strip())
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, list):
        return parsed

    match = re.search(r"\[.*\]", raw_response, re.DOTALL)
    if not match:
        return None

    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None

    if isinstance(parsed, list):
        return parsed

    return None


def parse_commands(
    client: Any,
    text: str,
    *,
    allowed_categories: set[str] | tuple[str, ...] = ALLOWED_CATEGORIES,
    temperature: float = 0,
    top_p: float = 0.9,
    max_tokens: int = 512,
) -> list[dict[str, Any]]:
    # 校验时统一使用 set，避免重复创建和线性查找。
    allowed_categories_set = set(allowed_categories)
    system_prompt = _SYSTEM_PROMPT.format(
        categories=", ".join(allowed_categories),
    )

    try:
        raw_response = client.ask(
            text,
            system_prompt=system_prompt,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )
    except Exception:
        logger.warning(
            "command_parser.parse_failed",
            extra={
                "failure_type": "llm_error",
                "input_text": text,
            },
        )
        return _fallback()

    commands = _extract_json(raw_response)
    if commands is None:
        logger.warning(
            "command_parser.parse_failed",
            extra={
                "failure_type": "json_parse_error",
                "input_text": text,
                "raw_response": _truncate_raw_response(raw_response),
            },
        )
        return _fallback()

    if not _validate_commands(commands, allowed_categories_set):
        logger.warning(
            "command_parser.parse_failed",
            extra={
                "failure_type": "validation_failed",
                "input_text": text,
                "raw_response": _truncate_raw_response(raw_response),
            },
        )
        return _fallback()

    return commands
