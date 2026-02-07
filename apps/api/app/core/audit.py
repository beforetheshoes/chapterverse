from __future__ import annotations

import logging
import threading
import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.engine import Engine

from app.db.config import get_database_url

logger = logging.getLogger(__name__)

_engine_lock = threading.Lock()
_engine: Engine | None = None
_engine_key: str | None = None


def _get_engine() -> Engine:
    global _engine, _engine_key

    db_url = get_database_url()
    with _engine_lock:
        if _engine is None or _engine_key != db_url:
            _engine = sa.create_engine(db_url, future=True, pool_pre_ping=True)
            _engine_key = db_url
        return _engine


def write_api_audit_log(
    *,
    client_id: uuid.UUID,
    user_id: uuid.UUID | None,
    method: str,
    path: str,
    status: int,
    latency_ms: int,
    ip: str,
) -> None:
    try:
        engine = _get_engine()
    except RuntimeError:
        # DB env is not configured in all local/unit test contexts.
        return
    except Exception:
        logger.exception("Failed to initialize API audit log engine.")
        return

    statement = sa.text(
        """
        insert into public.api_audit_logs
            (client_id, user_id, method, path, status, latency_ms, ip)
        values
            (:client_id, :user_id, :method, :path, :status, :latency_ms, cast(:ip as inet))
        """
    )
    params: dict[str, Any] = {
        "client_id": client_id,
        "user_id": user_id,
        "method": method,
        "path": path,
        "status": status,
        "latency_ms": latency_ms,
        "ip": ip,
    }

    try:
        with engine.begin() as conn:
            conn.execute(statement, params)
    except Exception:
        logger.exception("Failed to write api_audit_logs record.")
