from typing import cast

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INET

from app.db.base import Base
from app.db.models import ApiAuditLog, ApiClient


def _get_table(name: str) -> sa.Table:
    return Base.metadata.tables[name]


def test_platform_tables_registered() -> None:
    assert ApiClient.__tablename__ in Base.metadata.tables
    assert ApiAuditLog.__tablename__ in Base.metadata.tables


def test_api_clients_table_schema() -> None:
    table = _get_table("api_clients")
    assert set(table.columns.keys()) == {
        "client_id",
        "name",
        "owner_user_id",
        "status",
        "created_at",
    }
    assert isinstance(table.columns["client_id"].type, sa.UUID)
    assert isinstance(table.columns["name"].type, sa.String)
    assert table.columns["name"].type.length == 255
    assert isinstance(table.columns["owner_user_id"].type, sa.UUID)
    assert isinstance(table.columns["status"].type, sa.Enum)
    assert table.columns["status"].type.enums == ["active", "suspended"]
    assert table.columns["status"].server_default is not None

    created_at_type = cast(sa.DateTime, table.columns["created_at"].type)
    assert created_at_type.timezone is True

    fk_targets = {fk.target_fullname for fk in table.foreign_keys}
    assert "users.id" in fk_targets
    owner_fk = next(fk for fk in table.foreign_keys if fk.target_fullname == "users.id")
    assert owner_fk.ondelete == "CASCADE"

    index_names = {index.name for index in table.indexes}
    assert "ix_api_clients_owner_user_id" in index_names


def test_api_audit_logs_table_schema() -> None:
    table = _get_table("api_audit_logs")
    assert set(table.columns.keys()) == {
        "id",
        "occurred_at",
        "client_id",
        "user_id",
        "method",
        "path",
        "status",
        "latency_ms",
        "ip",
    }
    assert isinstance(table.columns["id"].type, sa.UUID)
    occurred_at_type = table.columns["occurred_at"].type
    assert isinstance(occurred_at_type, sa.DateTime)
    assert isinstance(table.columns["client_id"].type, sa.UUID)
    assert isinstance(table.columns["user_id"].type, sa.UUID)
    assert isinstance(table.columns["method"].type, sa.String)
    assert table.columns["method"].type.length == 16
    assert isinstance(table.columns["path"].type, sa.Text)
    assert isinstance(table.columns["status"].type, sa.SmallInteger)
    assert isinstance(table.columns["latency_ms"].type, sa.Integer)
    assert isinstance(table.columns["ip"].type, INET)

    assert occurred_at_type.timezone is True

    fk_targets = {fk.target_fullname for fk in table.foreign_keys}
    assert "api_clients.client_id" in fk_targets
    assert "users.id" in fk_targets
    client_fk = next(
        fk for fk in table.foreign_keys if fk.target_fullname == "api_clients.client_id"
    )
    user_fk = next(fk for fk in table.foreign_keys if fk.target_fullname == "users.id")
    assert client_fk.ondelete == "CASCADE"
    assert user_fk.ondelete == "SET NULL"

    index_names = {index.name for index in table.indexes}
    assert "ix_api_audit_logs_client_user" in index_names
    assert "ix_api_audit_logs_occurred_at" in index_names
