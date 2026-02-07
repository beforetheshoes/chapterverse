from __future__ import annotations

import uuid
from collections.abc import Generator
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.rate_limit import enforce_client_user_rate_limit
from app.core.security import AuthContext, require_auth_context
from app.db.session import get_db_session
from app.routers.books import get_open_library_client, router
from app.routers.library import router as library_router
from app.services.open_library import (
    OpenLibrarySearchResponse,
    OpenLibrarySearchResult,
    OpenLibraryWorkBundle,
)


class _FakeOpenLibrary:
    async def search_books(
        self, *, query: str, limit: int = 10, page: int = 1
    ) -> OpenLibrarySearchResponse:
        return OpenLibrarySearchResponse(
            items=[
                OpenLibrarySearchResult(
                    work_key="/works/OL1W",
                    title=f"{query}-title",
                    author_names=["Author A"],
                    first_publish_year=2000,
                    cover_url=None,
                )
            ],
            cache_hit=False,
        )

    async def fetch_work_bundle(
        self, *, work_key: str, edition_key: str | None = None
    ) -> OpenLibraryWorkBundle:
        if work_key == "bad":
            raise ValueError("work_key must be an Open Library work key")
        return OpenLibraryWorkBundle(
            work_key="/works/OL1W",
            title="Book",
            description=None,
            first_publish_year=2001,
            cover_url=None,
            authors=[{"key": "/authors/OL2A", "name": "Author A"}],
            edition={
                "key": "/books/OL3M",
                "isbn10": None,
                "isbn13": None,
                "publisher": None,
                "publish_date": None,
            },
            raw_work={},
            raw_edition={},
        )


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> Generator[FastAPI, None, None]:
    app = FastAPI()
    app.include_router(router)

    app.dependency_overrides[require_auth_context] = lambda: AuthContext(
        claims={},
        client_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        user_id=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
    )
    app.dependency_overrides[enforce_client_user_rate_limit] = lambda: None
    app.dependency_overrides[get_open_library_client] = lambda: _FakeOpenLibrary()

    def _fake_session() -> Generator[object, None, None]:
        yield object()

    app.dependency_overrides[get_db_session] = _fake_session

    monkeypatch.setattr(
        "app.routers.books.import_openlibrary_bundle",
        lambda session, *, bundle: {
            "work": {"id": "w1", "title": bundle.title, "created": True}
        },
    )
    yield app


def test_books_search_endpoint(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.get("/api/v1/books/search", params={"query": "hello"})
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["items"][0]["title"] == "hello-title"
    assert payload["cache_hit"] is False


def test_books_import_endpoint(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.post("/api/v1/books/import", json={"work_key": "OL1W"})
    assert response.status_code == 200
    assert response.json()["data"]["work"]["created"] is True


def test_books_import_returns_400_for_invalid_key(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.post("/api/v1/books/import", json={"work_key": "bad"})
    assert response.status_code == 400


def test_books_import_returns_404_when_catalog_lookup_fails(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "app.routers.books.import_openlibrary_bundle",
        lambda session, *, bundle: (_ for _ in ()).throw(LookupError("missing")),
    )
    client = TestClient(app)
    response = client.post("/api/v1/books/import", json={"work_key": "OL1W"})
    assert response.status_code == 404


def test_get_open_library_client_factory() -> None:
    client = get_open_library_client()
    assert client is not None


def test_books_search_returns_502_when_open_library_unavailable(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _raise_unavailable(
        *_args: object, **_kwargs: object
    ) -> OpenLibrarySearchResponse:
        raise httpx.HTTPError("upstream unavailable")

    monkeypatch.setattr(_FakeOpenLibrary, "search_books", _raise_unavailable)
    client = TestClient(app)
    response = client.get("/api/v1/books/search", params={"query": "hello"})
    assert response.status_code == 502
    payload = response.json()["detail"]
    assert payload["code"] == "open_library_unavailable"


def test_books_import_returns_502_when_open_library_unavailable(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _raise_unavailable(
        *_args: object, **_kwargs: object
    ) -> OpenLibraryWorkBundle:
        raise httpx.HTTPError("upstream unavailable")

    monkeypatch.setattr(_FakeOpenLibrary, "fetch_work_bundle", _raise_unavailable)
    client = TestClient(app)
    response = client.post("/api/v1/books/import", json={"work_key": "OL1W"})
    assert response.status_code == 502
    payload = response.json()["detail"]
    assert payload["code"] == "open_library_unavailable"


def test_import_then_add_library_item_happy_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = FastAPI()
    app.include_router(router)
    app.include_router(library_router)

    user_id = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    app.dependency_overrides[require_auth_context] = lambda: AuthContext(
        claims={},
        client_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        user_id=user_id,
    )
    app.dependency_overrides[enforce_client_user_rate_limit] = lambda: None
    app.dependency_overrides[get_open_library_client] = lambda: _FakeOpenLibrary()

    def _fake_session() -> Generator[object, None, None]:
        yield object()

    app.dependency_overrides[get_db_session] = _fake_session

    imported_work_id = uuid.uuid4()
    monkeypatch.setattr(
        "app.routers.books.import_openlibrary_bundle",
        lambda session, *, bundle: {
            "work": {
                "id": str(imported_work_id),
                "title": bundle.title,
                "created": True,
            }
        },
    )

    def _create_or_get_library_item(
        session: object, **kwargs: object
    ) -> tuple[SimpleNamespace, bool]:
        assert kwargs["work_id"] == imported_work_id
        return (
            SimpleNamespace(
                id=uuid.uuid4(),
                work_id=imported_work_id,
                status="to_read",
                visibility="private",
                rating=None,
                tags=[],
            ),
            True,
        )

    monkeypatch.setattr(
        "app.routers.library.create_or_get_library_item",
        _create_or_get_library_item,
    )

    client = TestClient(app)
    import_response = client.post("/api/v1/books/import", json={"work_key": "OL1W"})
    assert import_response.status_code == 200

    work_id = import_response.json()["data"]["work"]["id"]
    add_response = client.post("/api/v1/library/items", json={"work_id": work_id})
    assert add_response.status_code == 200
    assert add_response.json()["data"]["created"] is True
