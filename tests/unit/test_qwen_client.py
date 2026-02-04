from __future__ import annotations

from http import HTTPStatus
from typing import Any, Callable

import pytest

from app.core.exceptions import QwenClientError
from app.core.qwen_client import QwenClient


class DummyMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class DummyChoice:
    def __init__(self, content: str) -> None:
        self.message = DummyMessage(content)


class DummyOutput:
    def __init__(self, content: str) -> None:
        self.choices = [DummyChoice(content)]


class DummyResponse:
    def __init__(
        self,
        status_code: int,
        *,
        content: str = "ok",
        code: str = "ERR",
        message: str = "bad",
    ) -> None:
        self.status_code = status_code
        self.output = DummyOutput(content)
        self.code = code
        self.message = message


def make_stub(
    capture: dict[str, Any],
    response: DummyResponse,
) -> Callable[..., DummyResponse]:
    def _call(**kwargs: Any) -> DummyResponse:
        capture.update(kwargs)
        return response

    return _call


def test_chat_calls_generation_with_defaults() -> None:
    capture: dict[str, Any] = {}
    stub = make_stub(capture, DummyResponse(HTTPStatus.OK, content="hi"))
    client = QwenClient(api_key="test", generation_call=stub)

    messages = [{"role": "user", "content": "Hello"}]
    result = client.chat(messages)

    assert result == "hi"
    assert capture["model"] == "qwen-flash"
    assert capture["messages"] == messages
    assert capture["result_format"] == "message"
    assert capture["temperature"] == 0.7
    assert capture["top_p"] == 0.9
    assert capture["max_tokens"] == 2000


def test_chat_inserts_system_prompt_default() -> None:
    capture: dict[str, Any] = {}
    stub = make_stub(capture, DummyResponse(HTTPStatus.OK))
    client = QwenClient(
        api_key="test",
        system_prompt="You are helpful",
        generation_call=stub,
    )

    messages = [{"role": "user", "content": "Hello"}]
    client.chat(messages)

    assert messages[0]["role"] == "user"
    assert capture["messages"][0] == {
        "role": "system",
        "content": "You are helpful",
    }


def test_chat_overrides_system_prompt() -> None:
    capture: dict[str, Any] = {}
    stub = make_stub(capture, DummyResponse(HTTPStatus.OK))
    client = QwenClient(
        api_key="test",
        system_prompt="default",
        generation_call=stub,
    )

    client.chat(
        [{"role": "user", "content": "Hi"}],
        system_prompt="override",
    )

    assert capture["messages"][0]["content"] == "override"


def test_chat_overrides_generation_parameters() -> None:
    capture: dict[str, Any] = {}
    stub = make_stub(capture, DummyResponse(HTTPStatus.OK))
    client = QwenClient(api_key="test", generation_call=stub)

    client.chat(
        [{"role": "user", "content": "Hi"}],
        temperature=0.2,
        top_p=0.5,
        max_tokens=10,
    )

    assert capture["temperature"] == 0.2
    assert capture["top_p"] == 0.5
    assert capture["max_tokens"] == 10


def test_ask_wraps_user_message() -> None:
    capture: dict[str, Any] = {}
    stub = make_stub(capture, DummyResponse(HTTPStatus.OK, content="ok"))
    client = QwenClient(api_key="test", generation_call=stub)

    result = client.ask("Hello")

    assert result == "ok"
    assert capture["messages"] == [{"role": "user", "content": "Hello"}]


def test_chat_raises_on_non_ok_status() -> None:
    capture: dict[str, Any] = {}
    stub = make_stub(
        capture,
        DummyResponse(
            HTTPStatus.BAD_REQUEST,
            code="Bad",
            message="oops",
        ),
    )
    client = QwenClient(api_key="test", generation_call=stub)

    with pytest.raises(QwenClientError) as exc_info:
        client.chat([{"role": "user", "content": "Hi"}])

    assert exc_info.value.code == "Bad"
    assert exc_info.value.message == "oops"
    assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
