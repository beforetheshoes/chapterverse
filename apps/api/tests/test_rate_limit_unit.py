from __future__ import annotations

import uuid

from fastapi import Request

from app.core.rate_limit import (
    InMemoryRateLimiter,
    RateLimitConfig,
    _parse_endpoint_limits,
    _parse_positive_int,
    _resolve_limit,
    enforce_client_user_rate_limit,
)
from app.core.security import AuthContext


def _request(method: str, path: str, client_host: str | None = "127.0.0.1") -> Request:
    client = (client_host, 12345) if client_host is not None else None
    return Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "headers": [],
            "client": client,
            "scheme": "http",
            "server": ("testserver", 80),
            "query_string": b"",
        }
    )


def test_parse_positive_int() -> None:
    assert _parse_positive_int(None, fallback=7) == 7
    assert _parse_positive_int("", fallback=7) == 7
    assert _parse_positive_int("abc", fallback=7) == 7
    assert _parse_positive_int("0", fallback=7) == 7
    assert _parse_positive_int("-1", fallback=7) == 7
    assert _parse_positive_int("12", fallback=7) == 12


def test_parse_endpoint_limits() -> None:
    assert _parse_endpoint_limits(None) == {}
    assert _parse_endpoint_limits("bad") == {}
    assert _parse_endpoint_limits("GET /x:5,/x:2,invalid:0,:9") == {
        "GET /x": 5,
        "/x": 2,
    }


def test_resolve_limit_prefers_method_path_then_path() -> None:
    config = RateLimitConfig(
        default_limit=50,
        window_seconds=60,
        endpoint_limits={"GET /api/v1/protected/ping": 2, "/api/v1/protected/ping": 3},
    )
    request = _request("GET", "/api/v1/protected/ping")
    assert _resolve_limit(config, request) == 2

    config2 = RateLimitConfig(
        default_limit=50,
        window_seconds=60,
        endpoint_limits={"/api/v1/protected/ping": 3},
    )
    assert _resolve_limit(config2, request) == 3

    config3 = RateLimitConfig(default_limit=50, window_seconds=60, endpoint_limits={})
    assert _resolve_limit(config3, request) == 50


def test_in_memory_rate_limiter_prunes_old_entries() -> None:
    limiter = InMemoryRateLimiter()
    key = (
        uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        uuid.UUID("11111111-1111-1111-1111-111111111111"),
        "GET /api/v1/protected/ping",
    )
    assert limiter.check(key=key, limit=1, window_seconds=60, now=100.0) is None
    assert limiter.check(key=key, limit=1, window_seconds=60, now=161.0) is None


def test_enforce_rate_limit_noop_when_default_limit_disabled() -> None:
    request = _request("GET", "/api/v1/protected/ping")
    auth = AuthContext(
        claims={},
        client_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
    )
    config = RateLimitConfig(default_limit=0, window_seconds=60, endpoint_limits={})

    enforce_client_user_rate_limit(request=request, auth=auth, config=config)
    assert not hasattr(request.state, "rate_limit_event")
