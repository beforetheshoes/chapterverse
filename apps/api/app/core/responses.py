from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ResponseEnvelope(BaseModel):
    data: Any | None = None
    error: ErrorDetail | None = None


def ok(data: Any) -> dict[str, Any]:
    return ResponseEnvelope(data=data, error=None).model_dump()


def fail(
    code: str, message: str, details: dict[str, Any] | None = None
) -> dict[str, Any]:
    return ResponseEnvelope(
        data=None,
        error=ErrorDetail(code=code, message=message, details=details),
    ).model_dump()
