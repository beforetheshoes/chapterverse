from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass
from typing import Any, cast

import httpx


@dataclass(frozen=True)
class OpenLibrarySearchResult:
    work_key: str
    title: str
    author_names: list[str]
    first_publish_year: int | None
    cover_url: str | None


@dataclass(frozen=True)
class OpenLibraryWorkBundle:
    work_key: str
    title: str
    description: str | None
    first_publish_year: int | None
    cover_url: str | None
    authors: list[dict[str, str]]
    edition: dict[str, Any] | None
    raw_work: dict[str, Any]
    raw_edition: dict[str, Any] | None


@dataclass
class OpenLibrarySearchResponse:
    items: list[OpenLibrarySearchResult]
    cache_hit: bool


class _TTLCache:
    def __init__(self, *, ttl_seconds: int, max_entries: int) -> None:
        self._ttl_seconds = max(ttl_seconds, 1)
        self._max_entries = max(max_entries, 1)
        self._items: dict[str, tuple[float, OpenLibrarySearchResponse]] = {}

    def get(self, key: str) -> OpenLibrarySearchResponse | None:
        cached = self._items.get(key)
        if cached is None:
            return None
        expires_at, value = cached
        if expires_at < time.time():
            self._items.pop(key, None)
            return None
        return value

    def set(self, key: str, value: OpenLibrarySearchResponse) -> None:
        if len(self._items) >= self._max_entries:
            oldest_key = min(self._items.items(), key=lambda item: item[1][0])[0]
            self._items.pop(oldest_key, None)
        self._items[key] = (time.time() + self._ttl_seconds, value)


def _normalize_work_key(work_key: str) -> str:
    value = work_key.strip()
    if value.startswith("/works/"):
        return value
    if value.startswith("OL"):
        return f"/works/{value}"
    raise ValueError("work_key must be an Open Library work key")


def _normalize_edition_key(edition_key: str) -> str:
    value = edition_key.strip()
    if value.startswith("/books/"):
        return value
    if value.startswith("OL"):
        return f"/books/{value}"
    raise ValueError("edition_key must be an Open Library edition key")


def _extract_description(payload: dict[str, Any]) -> str | None:
    description = payload.get("description")
    if isinstance(description, str):
        return description
    if isinstance(description, dict):
        value = description.get("value")
        if isinstance(value, str):
            return value
    return None


class OpenLibraryClient:
    def __init__(
        self,
        *,
        base_url: str = "https://openlibrary.org",
        user_agent: str | None = None,
        cache_ttl_seconds: int = 300,
        cache_max_entries: int = 256,
        max_retries: int = 3,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._user_agent = (
            user_agent
            or os.getenv(
                "OPENLIBRARY_USER_AGENT",
                "TheSeedbed/0.1 (contact@theseedbed.app)",
            )
            or "TheSeedbed/0.1 (contact@theseedbed.app)"
        )
        self._max_retries = max(max_retries, 1)
        self._cache = _TTLCache(
            ttl_seconds=cache_ttl_seconds,
            max_entries=cache_max_entries,
        )
        self._transport = transport

    async def _request_json(
        self,
        path: str,
        *,
        params: dict[str, str | int] | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        headers = {"User-Agent": self._user_agent}
        backoff = 0.2

        for attempt in range(1, self._max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=10.0, transport=self._transport
                ) as client:
                    response = await client.get(url, params=params, headers=headers)
                if (
                    response.status_code in {429, 500, 502, 503, 504}
                    and attempt < self._max_retries
                ):
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                response.raise_for_status()
                return cast(dict[str, Any], response.json())
            except httpx.HTTPError:
                if attempt >= self._max_retries:
                    raise
                await asyncio.sleep(backoff)
                backoff *= 2

        raise RuntimeError("open library request failed")

    async def search_books(
        self, *, query: str, limit: int = 10, page: int = 1
    ) -> OpenLibrarySearchResponse:
        normalized_query = query.strip()
        cache_key = f"{normalized_query.lower()}::{limit}::{page}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return OpenLibrarySearchResponse(items=cached.items, cache_hit=True)

        payload = await self._request_json(
            "/search.json",
            params={"q": normalized_query, "limit": limit, "page": page},
        )
        docs = payload.get("docs", [])
        items: list[OpenLibrarySearchResult] = []
        for doc in docs:
            if not isinstance(doc, dict):
                continue
            work_key = doc.get("key")
            title = doc.get("title")
            if not isinstance(work_key, str) or not isinstance(title, str):
                continue
            cover_id = doc.get("cover_i")
            cover_url = None
            if isinstance(cover_id, int):
                cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
            author_names = doc.get("author_name")
            normalized_authors = []
            if isinstance(author_names, list):
                normalized_authors = [
                    name for name in author_names if isinstance(name, str)
                ]
            first_publish_year = doc.get("first_publish_year")
            items.append(
                OpenLibrarySearchResult(
                    work_key=work_key,
                    title=title,
                    author_names=normalized_authors,
                    first_publish_year=(
                        first_publish_year
                        if isinstance(first_publish_year, int)
                        else None
                    ),
                    cover_url=cover_url,
                )
            )

        result = OpenLibrarySearchResponse(items=items, cache_hit=False)
        self._cache.set(cache_key, result)
        return result

    async def fetch_work_bundle(
        self,
        *,
        work_key: str,
        edition_key: str | None = None,
    ) -> OpenLibraryWorkBundle:
        normalized_work_key = _normalize_work_key(work_key)
        work_payload = await self._request_json(f"{normalized_work_key}.json")

        author_entries = work_payload.get("authors", [])
        authors: list[dict[str, str]] = []
        for author_entry in author_entries:
            if not isinstance(author_entry, dict):
                continue
            author_obj = author_entry.get("author")
            if not isinstance(author_obj, dict):
                continue
            author_key = author_obj.get("key")
            if isinstance(author_key, str):
                author_payload = await self._request_json(f"{author_key}.json")
                name = author_payload.get("name")
                if isinstance(name, str):
                    authors.append({"key": author_key, "name": name})

        normalized_edition_key: str | None = None
        raw_edition: dict[str, Any] | None = None
        if edition_key:
            normalized_edition_key = _normalize_edition_key(edition_key)
            raw_edition = await self._request_json(f"{normalized_edition_key}.json")
        else:
            editions_payload = await self._request_json(
                f"{normalized_work_key}/editions.json", params={"limit": 1}
            )
            entries = editions_payload.get("entries", [])
            if isinstance(entries, list) and entries and isinstance(entries[0], dict):
                maybe_key = entries[0].get("key")
                if isinstance(maybe_key, str):
                    normalized_edition_key = maybe_key
                    raw_edition = entries[0]

        cover_url = None
        covers = work_payload.get("covers")
        if isinstance(covers, list) and covers and isinstance(covers[0], int):
            cover_url = f"https://covers.openlibrary.org/b/id/{covers[0]}-L.jpg"

        edition: dict[str, Any] | None = None
        if raw_edition is not None and normalized_edition_key is not None:
            isbn10 = None
            isbn13 = None
            isbn_10_values = raw_edition.get("isbn_10")
            if isinstance(isbn_10_values, list):
                isbn10 = next((v for v in isbn_10_values if isinstance(v, str)), None)
            isbn_13_values = raw_edition.get("isbn_13")
            if isinstance(isbn_13_values, list):
                isbn13 = next((v for v in isbn_13_values if isinstance(v, str)), None)
            edition = {
                "key": normalized_edition_key,
                "isbn10": isbn10,
                "isbn13": isbn13,
                "publisher": next(
                    (
                        v
                        for v in raw_edition.get("publishers", [])
                        if isinstance(raw_edition.get("publishers"), list)
                        and isinstance(v, str)
                    ),
                    None,
                ),
                "publish_date": (
                    raw_edition.get("publish_date")
                    if isinstance(raw_edition.get("publish_date"), str)
                    else None
                ),
            }

        return OpenLibraryWorkBundle(
            work_key=normalized_work_key,
            title=str(work_payload.get("title") or "Untitled"),
            description=_extract_description(work_payload),
            first_publish_year=(
                work_payload.get("first_publish_date")
                if isinstance(work_payload.get("first_publish_date"), int)
                else (
                    work_payload.get("first_publish_year")
                    if isinstance(work_payload.get("first_publish_year"), int)
                    else None
                )
            ),
            cover_url=cover_url,
            authors=authors,
            edition=edition,
            raw_work=work_payload,
            raw_edition=raw_edition,
        )
