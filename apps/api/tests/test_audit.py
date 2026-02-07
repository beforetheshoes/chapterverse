from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, cast

import pytest

from app.core import audit


def test_write_api_audit_log_skips_when_db_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_runtime_error() -> None:
        raise RuntimeError("missing db")

    monkeypatch.setattr(audit, "_get_engine", raise_runtime_error)

    audit.write_api_audit_log(
        client_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        method="GET",
        path="/api/v1/protected/ping",
        status=429,
        latency_ms=1,
        ip="127.0.0.1",
    )


def test_write_api_audit_log_handles_write_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BrokenEngine:
        @contextmanager
        def begin(self) -> Iterator[None]:
            raise RuntimeError("boom")
            yield

    monkeypatch.setattr(audit, "_get_engine", lambda: BrokenEngine())

    audit.write_api_audit_log(
        client_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        method="GET",
        path="/api/v1/protected/ping",
        status=429,
        latency_ms=1,
        ip="127.0.0.1",
    )


def test_write_api_audit_log_handles_engine_init_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_generic_error() -> None:
        raise ValueError("boom")

    monkeypatch.setattr(audit, "_get_engine", raise_generic_error)

    audit.write_api_audit_log(
        client_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        method="GET",
        path="/api/v1/protected/ping",
        status=429,
        latency_ms=1,
        ip="127.0.0.1",
    )


def test_write_api_audit_log_executes_insert(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeConnection:
        def execute(self, statement: object, params: dict[str, Any]) -> None:
            captured["statement"] = str(statement)
            captured["params"] = params

    class FakeEngine:
        @contextmanager
        def begin(self) -> Iterator[FakeConnection]:
            yield FakeConnection()

    monkeypatch.setattr(audit, "_get_engine", lambda: FakeEngine())

    audit.write_api_audit_log(
        client_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        method="GET",
        path="/api/v1/protected/ping",
        status=429,
        latency_ms=1,
        ip="127.0.0.1",
    )

    statement = cast(str, captured["statement"])
    assert "insert into public.api_audit_logs" in statement
    params = cast(dict[str, Any], captured["params"])
    assert isinstance(params, dict)
    assert params["status"] == 429
