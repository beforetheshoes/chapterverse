from __future__ import annotations

from collections.abc import Generator
from typing import Any, cast

import pytest

from app.db.session import get_db_session, reset_session_factory


class _FakeSession:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class _FakeFactory:
    def __init__(self) -> None:
        self.session = _FakeSession()

    def __call__(self) -> _FakeSession:
        return self.session


@pytest.fixture(autouse=True)
def reset_cache() -> Generator[None, None, None]:
    reset_session_factory()
    yield
    reset_session_factory()


def test_get_db_session_yields_and_closes(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_factory = _FakeFactory()
    monkeypatch.setattr("app.db.session._session_factory", lambda: fake_factory)

    gen = get_db_session()
    session = next(gen)
    assert session is cast(Any, fake_factory.session)

    with pytest.raises(StopIteration):
        next(gen)
    assert fake_factory.session.closed is True


def test_reset_session_factory_clears_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.db.session.get_database_url", lambda: "postgresql+psycopg://local/db"
    )

    class _Engine:
        pass

    monkeypatch.setattr(
        "app.db.session.sa.create_engine", lambda *args, **kwargs: _Engine()
    )

    from app.db.session import _session_factory

    _session_factory()
    reset_session_factory()
    _session_factory()
