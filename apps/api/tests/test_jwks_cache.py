import asyncio

from app.core.jwks import JWKSCache


def test_jwks_cache_respects_ttl() -> None:
    calls = {"count": 0}

    async def fetcher() -> dict[str, object]:
        calls["count"] += 1
        return {"keys": [{"kid": "one"}]}

    class FakeClock:
        def __init__(self) -> None:
            self.now = 1000.0

        def monotonic(self) -> float:
            return self.now

        def advance(self, seconds: float) -> None:
            self.now += seconds

    clock = FakeClock()
    cache = JWKSCache(fetcher=fetcher, ttl_seconds=60, time_fn=clock.monotonic)

    async def run() -> None:
        first = await cache.get()
        second = await cache.get()
        assert first == second
        assert calls["count"] == 1

        clock.advance(61)
        await cache.get()
        assert calls["count"] == 2

    asyncio.run(run())


def test_jwks_cache_returns_after_concurrent_fetch() -> None:
    calls = {"count": 0}
    started = asyncio.Event()
    release = asyncio.Event()

    async def fetcher() -> dict[str, object]:
        calls["count"] += 1
        started.set()
        await release.wait()
        return {"keys": [{"kid": "one"}]}

    cache = JWKSCache(fetcher=fetcher, ttl_seconds=60)

    async def run() -> None:
        task_one = asyncio.create_task(cache.get())
        await started.wait()
        task_two = asyncio.create_task(cache.get())
        release.set()
        result_one = await task_one
        result_two = await task_two
        assert result_one == result_two
        assert calls["count"] == 1

    asyncio.run(run())
