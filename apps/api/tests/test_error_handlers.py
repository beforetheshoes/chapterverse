import json

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError

from app.core.errors import (
    auth_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.security import AuthError


def _request() -> Request:
    return Request({"type": "http", "method": "GET", "path": "/", "headers": []})


def _request_with_origin(origin: str) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [(b"origin", origin.encode("utf-8"))],
        }
    )


def test_auth_exception_handler() -> None:
    exc = AuthError(code="invalid_token", message="Invalid token")
    response = auth_exception_handler(_request(), exc)
    assert response.status_code == 401
    payload = json.loads(bytes(response.body))
    assert payload["data"] is None
    assert payload["error"]["code"] == "invalid_token"


def test_http_exception_handler_with_string_detail() -> None:
    exc = HTTPException(status_code=404, detail="Not found")
    response = http_exception_handler(_request(), exc)
    assert response.status_code == 404
    payload = json.loads(bytes(response.body))
    assert payload["error"]["code"] == "http_error"
    assert payload["error"]["message"] == "Not found"


def test_http_exception_handler_with_dict_detail() -> None:
    exc = HTTPException(
        status_code=400,
        detail={"code": "bad_request", "message": "Bad request"},
    )
    response = http_exception_handler(_request(), exc)
    assert response.status_code == 400
    payload = json.loads(bytes(response.body))
    assert payload["error"]["code"] == "bad_request"
    assert payload["error"]["message"] == "Bad request"


def test_http_exception_handler_preserves_headers() -> None:
    exc = HTTPException(
        status_code=429,
        detail={"code": "rate_limited", "message": "Rate limit exceeded."},
        headers={"Retry-After": "12"},
    )
    response = http_exception_handler(_request(), exc)
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "12"


def test_validation_exception_handler() -> None:
    exc = RequestValidationError(
        [{"loc": ("query", "q"), "msg": "field required", "type": "value_error"}]
    )
    response = validation_exception_handler(_request(), exc)
    assert response.status_code == 422
    payload = json.loads(bytes(response.body))
    assert payload["error"]["code"] == "validation_error"
    assert payload["error"]["details"]["errors"]


def test_unhandled_exception_handler() -> None:
    exc = Exception("boom")
    response = unhandled_exception_handler(_request(), exc)
    assert response.status_code == 500
    payload = json.loads(bytes(response.body))
    assert payload["error"]["code"] == "internal_error"


def test_unhandled_exception_handler_sets_cors_header_for_allowed_origin() -> None:
    exc = Exception("boom")
    response = unhandled_exception_handler(
        _request_with_origin("http://localhost:3000"),
        exc,
    )
    assert response.status_code == 500
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"


def test_unhandled_exception_handler_sets_cors_header_for_staging_origin() -> None:
    exc = Exception("boom")
    response = unhandled_exception_handler(
        _request_with_origin("https://staging.theseedbed.app"),
        exc,
    )
    assert response.status_code == 500
    assert (
        response.headers["Access-Control-Allow-Origin"]
        == "https://staging.theseedbed.app"
    )
