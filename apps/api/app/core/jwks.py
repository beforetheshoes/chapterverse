from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

FetchJWKS = Callable[[], Awaitable[dict[str, Any]]]
TimeFn = Callable[[], float]


@dataclass
class JWKSCache:
    fetcher: FetchJWKS
    ttl_seconds: int
    time_fn: TimeFn = time.monotonic
    _jwks: dict[str, Any] | None = None
    _fetched_at: float = 0.0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def get(self) -> dict[str, Any]:
        now = self.time_fn()
        if self._jwks is not None and (now - self._fetched_at) < self.ttl_seconds:
            return self._jwks
        async with self._lock:
            now = self.time_fn()
            if self._jwks is not None and (now - self._fetched_at) < self.ttl_seconds:
                return self._jwks
            jwks = await self.fetcher()
            self._jwks = jwks
            self._fetched_at = self.time_fn()
            return jwks
