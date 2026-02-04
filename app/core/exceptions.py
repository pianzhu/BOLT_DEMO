from __future__ import annotations


class QwenClientError(Exception):
    def __init__(
        self,
        *,
        code: str | None,
        message: str | None,
        status_code: int | None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        detail = f"DashScope error {code}: {message} (status {status_code})"
        super().__init__(detail)
