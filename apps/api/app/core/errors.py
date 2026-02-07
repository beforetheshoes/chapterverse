from __future__ import annotations

import logging
from typing import Any, cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.responses import fail
from app.core.security import AuthError

logger = logging.getLogger(__name__)


def _cors_headers_for_request(request: Request) -> dict[str, str]:
    origin = request.headers.get("origin")
    if not origin:
        return {}

    settings = get_settings()
    if origin not in settings.cors_allowed_origins:
        return {}

    return {
        "Access-Control-Allow-Origin": origin,
        "Vary": "Origin",
    }


def auth_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    auth_exc = cast(AuthError, exc)
    return JSONResponse(
        status_code=auth_exc.status_code,
        content=fail(
            code=auth_exc.code,
            message=auth_exc.message,
            details=auth_exc.details,
        ),
        headers=_cors_headers_for_request(request),
    )


def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    http_exc = cast(HTTPException, exc)
    details: dict[str, Any] | None = None
    code = "http_error"
    message = str(http_exc.detail)
    if isinstance(http_exc.detail, dict):
        code = http_exc.detail.get("code", code)
        message = http_exc.detail.get("message", message)
        details = http_exc.detail.get("details")
    headers: dict[str, str] = {}
    if http_exc.headers:
        headers.update(http_exc.headers)
    headers.update(_cors_headers_for_request(request))
    return JSONResponse(
        status_code=http_exc.status_code,
        content=fail(code=code, message=message, details=details),
        headers=headers,
    )


def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    validation_exc = cast(RequestValidationError, exc)
    return JSONResponse(
        status_code=422,
        content=fail(
            code="validation_error",
            message="Request validation failed.",
            details={"errors": validation_exc.errors()},
        ),
        headers=_cors_headers_for_request(request),
    )


def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=fail(code="internal_error", message="Internal server error."),
        headers=_cors_headers_for_request(request),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AuthError, auth_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
