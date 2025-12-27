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
