from __future__ import annotations

import logging
from typing import Any

import pytest

from app.services.command_parser import (
    ALLOWED_CATEGORIES,
    _extract_json,
    _fallback,
    _is_valid_action,
    _is_valid_category,
    _is_valid_count,
    _is_valid_nonempty_str,
    _is_valid_quantity,
    _validate_command,
    _validate_commands,
    compact_json_dumps,
    parse_commands,
)


class StubClient:
    def __init__(self, response: str | Exception) -> None:
        self._response = response
        self.calls: list[dict[str, Any]] = []

    def ask(self, prompt: str, **kwargs: Any) -> str:
        # 记录调用参数，便于断言 parse_commands 透传了默认配置。
        self.calls.append({"prompt": prompt, **kwargs})
        if isinstance(self._response, Exception):
            raise self._response
        return self._response


def test_compact_json_dumps_outputs_compact_json() -> None:
    payload = [{"a": "打开", "s": "客厅", "n": "灯", "t": "Light", "q": "one"}]

    dumped = compact_json_dumps(payload)

    assert dumped == '[{"a":"打开","s":"客厅","n":"灯","t":"Light","q":"one"}]'


@pytest.mark.parametrize(
    "value",
    ["打开", "关闭", "静音", "取消静音", "设置亮度=50", "查询温度"],
)
def test_is_valid_action_accepts_supported_actions(value: str) -> None:
    assert _is_valid_action(value)


@pytest.mark.parametrize(
    "value",
    ["", "设置", "查询", "播放", " 打开"],
)
def test_is_valid_action_rejects_unsupported_actions(value: str) -> None:
    assert not _is_valid_action(value)


@pytest.mark.parametrize("value", ["客厅", "*", "*,!卧室"])
def test_is_valid_nonempty_str_accepts_nonempty_strings(value: str) -> None:
    assert _is_valid_nonempty_str(value)


@pytest.mark.parametrize("value", ["", 123, None])
def test_is_valid_nonempty_str_rejects_invalid_values(value: object) -> None:
    assert not _is_valid_nonempty_str(value)


def test_is_valid_category_uses_allowed_categories() -> None:
    assert _is_valid_category("Light", ALLOWED_CATEGORIES)
    assert not _is_valid_category("Robot", ALLOWED_CATEGORIES)


@pytest.mark.parametrize("value", ["one", "all", "any", "except"])
def test_is_valid_quantity_accepts_enum_values(value: str) -> None:
    assert _is_valid_quantity(value)


@pytest.mark.parametrize("value", ["ONE", "", "many", None])
def test_is_valid_quantity_rejects_invalid_values(value: object) -> None:
    assert not _is_valid_quantity(value)


@pytest.mark.parametrize("value", [0, 1, -3])
def test_is_valid_count_accepts_integers(value: int) -> None:
    assert _is_valid_count(value)


@pytest.mark.parametrize("value", [True, False, 1.5, "1", None])
def test_is_valid_count_rejects_non_integers(value: object) -> None:
    assert not _is_valid_count(value)


def test_validate_command_accepts_valid_payload() -> None:
    command = {"a": "打开", "s": "客厅", "n": "灯", "t": "Light", "q": "one"}

    assert _validate_command(command, ALLOWED_CATEGORIES)


@pytest.mark.parametrize(
    "command",
    [
        {"a": "打开", "s": "客厅", "n": "灯", "t": "Light"},
        {"a": "打开", "s": "客厅", "n": "灯", "t": "Light", "q": "one", "x": "bad"},
        {"a": "播放", "s": "客厅", "n": "灯", "t": "Light", "q": "one"},
        {"a": "打开", "s": "", "n": "灯", "t": "Light", "q": "one"},
        {"a": "打开", "s": "客厅", "n": "灯", "t": "Robot", "q": "one"},
        {"a": "打开", "s": "客厅", "n": "灯", "t": "Light", "q": "many"},
        {"a": "打开", "s": "客厅", "n": "灯", "t": "Light", "q": "one", "c": True},
    ],
)
def test_validate_command_rejects_invalid_payloads(command: dict[str, object]) -> None:
    assert not _validate_command(command, ALLOWED_CATEGORIES)


def test_validate_commands_requires_list_of_valid_objects() -> None:
    valid = [{"a": "打开", "s": "客厅", "n": "灯", "t": "Light", "q": "one"}]
    invalid = [{"a": "打开", "s": "客厅", "n": "灯", "t": "Light", "q": "one", "c": True}]

    assert _validate_commands(valid, ALLOWED_CATEGORIES)
    assert not _validate_commands({"a": "打开"}, ALLOWED_CATEGORIES)
    assert not _validate_commands(["not-object"], ALLOWED_CATEGORIES)
    assert not _validate_commands(invalid, ALLOWED_CATEGORIES)


def test_extract_json_parses_direct_json() -> None:
    raw = '[{"a":"打开","s":"客厅","n":"灯","t":"Light","q":"one"}]'

    parsed = _extract_json(raw)

    assert parsed == [{"a": "打开", "s": "客厅", "n": "灯", "t": "Light", "q": "one"}]


def test_extract_json_parses_first_embedded_array() -> None:
    raw = '说明：请执行[{"a":"关闭","s":"客厅","n":"空调","t":"AirConditioner","q":"one"}]谢谢'

    parsed = _extract_json(raw)

    assert parsed == [
        {"a": "关闭", "s": "客厅", "n": "空调", "t": "AirConditioner", "q": "one"}
    ]


@pytest.mark.parametrize(
    "raw,expected",
    [("not json", None), ("{\"a\":\"打开\"}", None), ("[] trailing", [])],
)
def test_extract_json_follows_two_step_parse_strategy(raw: str, expected: object) -> None:
    assert _extract_json(raw) == expected


def test_parse_commands_returns_parsed_commands_and_passes_prompt_options() -> None:
    raw = '[{"a":"打开","s":"客厅","n":"灯","t":"Light","q":"one"}]'
    client = StubClient(raw)

    result = parse_commands(client, "打开客厅的灯")

    assert result == [{"a": "打开", "s": "客厅", "n": "灯", "t": "Light", "q": "one"}]
    assert client.calls[0]["prompt"] == "打开客厅的灯"
    assert client.calls[0]["temperature"] == 0
    assert client.calls[0]["top_p"] == 0.9
    assert client.calls[0]["max_tokens"] == 512
    assert "只输出 JSON 数组" in client.calls[0]["system_prompt"]
    assert "SmartPlug" in client.calls[0]["system_prompt"]


def test_parse_commands_supports_allowed_categories_override() -> None:
    raw = '[{"a":"打开","s":"客厅","n":"设备","t":"CustomType","q":"one"}]'
    client = StubClient(raw)

    result = parse_commands(client, "打开设备", allowed_categories={"CustomType", "Unknown"})

    assert result == [{"a": "打开", "s": "客厅", "n": "设备", "t": "CustomType", "q": "one"}]


def test_parse_commands_keeps_pronoun_unknown_target_shape() -> None:
    raw = '[{"a":"关闭","s":"*","n":"*","t":"Unknown","q":"one"}]'
    client = StubClient(raw)

    result = parse_commands(client, "把它关了")

    assert result == [{"a": "关闭", "s": "*", "n": "*", "t": "Unknown", "q": "one"}]


def test_parse_commands_falls_back_when_llm_call_fails(caplog: pytest.LogCaptureFixture) -> None:
    client = StubClient(RuntimeError("boom"))

    with caplog.at_level(logging.WARNING):
        result = parse_commands(client, "打开灯")

    assert result == _fallback()
    record = next(rec for rec in caplog.records if rec.message == "command_parser.parse_failed")
    assert record.failure_type == "llm_error"
    assert record.input_text == "打开灯"
    assert not hasattr(record, "raw_response")


def test_parse_commands_falls_back_on_json_parse_error_and_logs_raw_response(
    caplog: pytest.LogCaptureFixture,
) -> None:
    raw = "这是错误输出"
    client = StubClient(raw)

    with caplog.at_level(logging.WARNING):
        result = parse_commands(client, "打开灯")

    assert result == _fallback()
    record = next(rec for rec in caplog.records if rec.failure_type == "json_parse_error")
    assert record.input_text == "打开灯"
    assert record.raw_response == raw


def test_parse_commands_truncates_raw_response_in_validation_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # 构造超长响应，验证日志里会截断到 500 字符。
    too_long_name = "灯" * 600
    raw = (
        "["
        + '{"a":"打开","s":"客厅","n":"'
        + too_long_name
        + '","t":"Robot","q":"one"}'
        + "]"
    )
    client = StubClient(raw)

    with caplog.at_level(logging.WARNING):
        result = parse_commands(client, "打开那个设备")

    assert result == _fallback()
    record = next(rec for rec in caplog.records if rec.failure_type == "validation_failed")
    assert record.input_text == "打开那个设备"
    assert len(record.raw_response) == 500
    assert record.raw_response == raw[:500]


def test_parse_commands_falls_back_when_llm_returns_non_string(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = StubClient({"unexpected": "payload"})

    with caplog.at_level(logging.WARNING):
        result = parse_commands(client, "打开灯")

    assert result == _fallback()
    record = next(rec for rec in caplog.records if rec.failure_type == "json_parse_error")
    assert record.raw_response == "{'unexpected': 'payload'}"
