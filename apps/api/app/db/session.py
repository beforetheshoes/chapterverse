from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from app.db.config import get_database_url


@lru_cache
def _session_factory() -> sessionmaker[Session]:
    engine = sa.create_engine(get_database_url(), future=True, pool_pre_ping=True)
    return sessionmaker(bind=engine, expire_on_commit=False)


def reset_session_factory() -> None:
    _session_factory.cache_clear()


def get_db_session() -> Iterator[Session]:
    session = _session_factory()()
    try:
        yield session
    finally:
        session.close()
