from __future__ import annotations

import datetime as dt
import uuid
from collections.abc import Generator
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.rate_limit import enforce_client_user_rate_limit
from app.core.security import AuthContext, require_auth_context
from app.db.session import get_db_session
from app.routers.library import router as library_router
from app.routers.me import router as me_router


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> Generator[FastAPI, None, None]:
    app = FastAPI()
    app.include_router(me_router)
    app.include_router(library_router)

    user_id = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    app.dependency_overrides[require_auth_context] = lambda: AuthContext(
        claims={},
        client_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        user_id=user_id,
    )
    app.dependency_overrides[enforce_client_user_rate_limit] = lambda: None

    def _fake_session() -> Generator[object, None, None]:
        yield object()

    app.dependency_overrides[get_db_session] = _fake_session

    monkeypatch.setattr(
        "app.routers.me.get_or_create_profile",
        lambda session, *, user_id: SimpleNamespace(
            id=user_id, handle="seed", display_name="Seed", avatar_url=None
        ),
    )
    monkeypatch.setattr(
        "app.routers.me.update_profile",
        lambda session, *, user_id, handle, display_name, avatar_url: SimpleNamespace(
            id=user_id,
            handle=handle or "seed",
            display_name=display_name,
            avatar_url=avatar_url,
        ),
    )

    monkeypatch.setattr(
        "app.routers.library.list_library_items",
        lambda session, *, user_id, limit, cursor, status: {
            "items": [
                {
                    "id": str(uuid.uuid4()),
                    "work_id": str(uuid.uuid4()),
                    "work_title": "Book",
                    "status": status or "to_read",
                    "visibility": "private",
                    "rating": None,
                    "tags": [],
                    "created_at": dt.datetime.now(tz=dt.UTC).isoformat(),
                }
            ],
            "next_cursor": None,
        },
    )
    monkeypatch.setattr(
        "app.routers.library.create_or_get_library_item",
        lambda session, **_: (
            SimpleNamespace(
                id=uuid.uuid4(),
                work_id=uuid.uuid4(),
                status="to_read",
                visibility="private",
                rating=None,
                tags=None,
            ),
            True,
        ),
    )

    yield app


def test_get_me(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.get("/api/v1/me")
    assert response.status_code == 200
    assert response.json()["data"]["handle"] == "seed"


def test_patch_me(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.patch("/api/v1/me", json={"display_name": "Updated"})
    assert response.status_code == 200
    assert response.json()["data"]["display_name"] == "Updated"


def test_patch_me_returns_400_on_validation_error(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "app.routers.me.update_profile",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("bad")),
    )
    client = TestClient(app)
    response = client.patch("/api/v1/me", json={"handle": ""})
    assert response.status_code == 400


def test_list_library_items(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.get("/api/v1/library/items", params={"status": "reading"})
    assert response.status_code == 200
    assert response.json()["data"]["items"][0]["status"] == "reading"


def test_create_library_item(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/library/items",
        json={"work_id": str(uuid.uuid4())},
    )
    assert response.status_code == 200
    assert response.json()["data"]["created"] is True


def test_create_library_item_returns_404(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "app.routers.library.create_or_get_library_item",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(LookupError("missing work")),
    )
    client = TestClient(app)
    response = client.post(
        "/api/v1/library/items",
        json={"work_id": str(uuid.uuid4())},
    )
    assert response.status_code == 404


def test_list_library_items_returns_400_for_bad_cursor(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "app.routers.library.list_library_items",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("invalid cursor")),
    )
    client = TestClient(app)
    response = client.get("/api/v1/library/items", params={"cursor": "bad"})
    assert response.status_code == 400
