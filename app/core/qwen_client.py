from __future__ import annotations

import os
from http import HTTPStatus
from typing import Any, Callable

from app.core.exceptions import QwenClientError

Message = dict[str, str]
GenerationCall = Callable[..., Any]


class QwenClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "qwen-flash",
        system_prompt: str | None = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 2000,
        generation_call: GenerationCall | None = None,
    ) -> None:
        resolved_api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not resolved_api_key:
            raise ValueError("DASHSCOPE_API_KEY is required")

        if generation_call is None:
            import dashscope

            dashscope.api_key = resolved_api_key
            generation_call = dashscope.Generation.call

        self._api_key = resolved_api_key
        self._model = model
        self._system_prompt = system_prompt
        self._temperature = temperature
        self._top_p = top_p
        self._max_tokens = max_tokens
        self._generation_call = generation_call

    def chat(
        self,
        messages: list[Message],
        *,
        system_prompt: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        payload_messages = list(messages)
        prompt = system_prompt if system_prompt is not None else self._system_prompt
        if prompt is not None:
            payload_messages = [{"role": "system", "content": prompt}, *payload_messages]

        response = self._generation_call(
            model=self._model,
            messages=payload_messages,
            result_format="message",
            temperature=self._temperature if temperature is None else temperature,
            top_p=self._top_p if top_p is None else top_p,
            max_tokens=self._max_tokens if max_tokens is None else max_tokens,
        )

        if response.status_code != HTTPStatus.OK:
            raise QwenClientError(
                code=response.code,
                message=response.message,
                status_code=response.status_code,
            )

        return response.output.choices[0].message.content

    def ask(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        return self.chat(
            [{"role": "user", "content": prompt}],
            system_prompt=system_prompt,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )
