from __future__ import annotations

import os
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, Request

from app.core.security import AuthContext, require_auth_context


@dataclass(frozen=True)
class RateLimitConfig:
    default_limit: int
    window_seconds: int
    endpoint_limits: dict[str, int]


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._events: dict[tuple[uuid.UUID, uuid.UUID, str], deque[float]] = (
            defaultdict(deque)
        )
        self._lock = threading.Lock()

    def check(
        self,
        *,
        key: tuple[uuid.UUID, uuid.UUID, str],
        limit: int,
        window_seconds: int,
        now: float | None = None,
    ) -> int | None:
        current = now if now is not None else time.time()
        cutoff = current - window_seconds

        with self._lock:
            bucket = self._events[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= limit:
                retry_after = max(1, int(bucket[0] + window_seconds - current))
                return retry_after

            bucket.append(current)
            return None


_rate_limiter = InMemoryRateLimiter()


def _parse_positive_int(value: str | None, *, fallback: int) -> int:
    if value is None:
        return fallback
    raw = value.strip()
    if not raw:
        return fallback
    try:
        parsed = int(raw)
    except ValueError:
        return fallback
    if parsed <= 0:
        return fallback
    return parsed


def _parse_endpoint_limits(raw: str | None) -> dict[str, int]:
    if raw is None:
        return {}
    limits: dict[str, int] = {}
    for part in raw.split(","):
        item = part.strip()
        if not item or ":" not in item:
            continue
        key, value = item.rsplit(":", 1)
        key = key.strip()
        if not key:
            continue
        parsed = _parse_positive_int(value, fallback=-1)
        if parsed > 0:
            limits[key] = parsed
    return limits


@lru_cache
def get_rate_limit_config() -> RateLimitConfig:
    default_limit = _parse_positive_int(
        os.getenv("API_RATE_LIMIT_DEFAULT_MAX"), fallback=120
    )
    window_seconds = _parse_positive_int(
        os.getenv("API_RATE_LIMIT_WINDOW_SECONDS"), fallback=60
    )
    endpoint_limits = _parse_endpoint_limits(os.getenv("API_RATE_LIMIT_OVERRIDES"))
    return RateLimitConfig(
        default_limit=default_limit,
        window_seconds=window_seconds,
        endpoint_limits=endpoint_limits,
    )


def reset_rate_limit_config_cache() -> None:
    get_rate_limit_config.cache_clear()


def _resolve_limit(config: RateLimitConfig, request: Request) -> int:
    method_path = f"{request.method.upper()} {request.url.path}"
    if method_path in config.endpoint_limits:
        return config.endpoint_limits[method_path]
    if request.url.path in config.endpoint_limits:
        return config.endpoint_limits[request.url.path]
    return config.default_limit


def enforce_client_user_rate_limit(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    config: Annotated[RateLimitConfig, Depends(get_rate_limit_config)],
) -> None:
    if config.default_limit <= 0:
        return

    endpoint_key = f"{request.method.upper()} {request.url.path}"
    limit = _resolve_limit(config, request)
    effective_client_id = auth.client_id or auth.user_id
    retry_after = _rate_limiter.check(
        key=(effective_client_id, auth.user_id, endpoint_key),
        limit=limit,
        window_seconds=config.window_seconds,
    )
    if retry_after is None:
        return

    request.state.rate_limit_event = {
        "client_id": effective_client_id,
        "user_id": auth.user_id,
        "method": request.method.upper(),
        "path": request.url.path,
        "status": 429,
        "latency_ms": 0,
        "ip": request.client.host if request.client else "0.0.0.0",
    }

    raise HTTPException(
        status_code=429,
        detail={
            "code": "rate_limited",
            "message": "Rate limit exceeded.",
            "details": {
                "client_id": str(effective_client_id),
                "user_id": str(auth.user_id),
                "limit": limit,
                "window_seconds": config.window_seconds,
            },
        },
        headers={"Retry-After": str(retry_after)},
    )
