from __future__ import annotations

import asyncio
from collections.abc import Generator

import httpx
import pytest

from app.services.open_library import (
    OpenLibraryClient,
    _normalize_edition_key,
    _normalize_work_key,
)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    async def _fake_sleep(_: float) -> None:
        return None

    monkeypatch.setattr("app.services.open_library.asyncio.sleep", _fake_sleep)
    yield


def test_search_books_uses_user_agent_and_cache() -> None:
    seen_user_agents: list[str] = []
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        ua = request.headers.get("User-Agent")
        if ua:
            seen_user_agents.append(ua)
        return httpx.Response(
            200,
            json={
                "docs": [
                    {
                        "key": "/works/OL1W",
                        "title": "Book A",
                        "author_name": ["Author A"],
                        "first_publish_year": 1999,
                        "cover_i": 100,
                    }
                ]
            },
        )

    client = OpenLibraryClient(
        user_agent="SeedbedTest/1.0 (dev@example.com)",
        transport=httpx.MockTransport(handler),
    )

    first = asyncio.run(client.search_books(query="book", limit=5, page=1))
    second = asyncio.run(client.search_books(query="book", limit=5, page=1))

    assert calls["count"] == 1
    assert seen_user_agents == ["SeedbedTest/1.0 (dev@example.com)"]
    assert first.cache_hit is False
    assert second.cache_hit is True
    assert first.items[0].title == "Book A"


def test_fetch_work_bundle_collects_author_and_first_edition() -> None:
    responses = {
        "/works/OL1W.json": {
            "title": "Book A",
            "authors": [{"author": {"key": "/authors/OL2A"}}],
            "covers": [12],
        },
        "/authors/OL2A.json": {"name": "Author A"},
        "/works/OL1W/editions.json": {
            "entries": [
                {"key": "/books/OL3M", "isbn_10": ["1234567890"], "publishers": ["Pub"]}
            ]
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        payload = responses.get(request.url.path)
        if payload is None:
            return httpx.Response(404, json={"error": "missing"})
        return httpx.Response(200, json=payload)

    client = OpenLibraryClient(transport=httpx.MockTransport(handler))
    bundle = asyncio.run(client.fetch_work_bundle(work_key="OL1W"))

    assert bundle.work_key == "/works/OL1W"
    assert bundle.title == "Book A"
    assert bundle.authors == [{"key": "/authors/OL2A", "name": "Author A"}]
    assert bundle.edition is not None
    assert bundle.edition["key"] == "/books/OL3M"
    assert bundle.cover_url == "https://covers.openlibrary.org/b/id/12-L.jpg"


def test_request_retries_on_5xx() -> None:
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(503, json={"message": "retry"})
        return httpx.Response(200, json={"docs": []})

    client = OpenLibraryClient(transport=httpx.MockTransport(handler), max_retries=2)
    result = asyncio.run(client.search_books(query="retry"))

    assert calls["count"] == 2
    assert result.items == []


def test_normalize_keys() -> None:
    assert _normalize_work_key("OL1W") == "/works/OL1W"
    assert _normalize_work_key("/works/OL1W") == "/works/OL1W"
    assert _normalize_edition_key("OL1M") == "/books/OL1M"
    with pytest.raises(ValueError):
        _normalize_work_key("bad-key")
    with pytest.raises(ValueError):
        _normalize_edition_key("bad-key")


def test_fetch_work_bundle_with_explicit_edition_and_description_object() -> None:
    responses = {
        "/works/OL1W.json": {
            "title": "Book A",
            "description": {"value": "Desc"},
            "authors": [],
            "covers": [],
        },
        "/books/OL3M.json": {
            "isbn_13": ["9999999999999"],
            "publish_date": "2020",
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        payload = responses.get(request.url.path)
        if payload is None:
            return httpx.Response(404, json={"error": "missing"})
        return httpx.Response(200, json=payload)

    client = OpenLibraryClient(transport=httpx.MockTransport(handler))
    bundle = asyncio.run(
        client.fetch_work_bundle(work_key="/works/OL1W", edition_key="OL3M")
    )
    assert bundle.description == "Desc"
    assert bundle.edition is not None
    assert bundle.edition["key"] == "/books/OL3M"
    assert bundle.edition["isbn13"] == "9999999999999"


def test_request_raises_after_retry_exhausted() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"message": "still failing"})

    client = OpenLibraryClient(transport=httpx.MockTransport(handler), max_retries=2)
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(client.search_books(query="boom"))
