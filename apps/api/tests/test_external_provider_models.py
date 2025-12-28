from typing import cast

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base
from app.db.models import ExternalId, SourceRecord


def _get_table(name: str) -> sa.Table:
    return Base.metadata.tables[name]


def test_external_provider_tables_registered() -> None:
    assert ExternalId.__tablename__ in Base.metadata.tables
    assert SourceRecord.__tablename__ in Base.metadata.tables


def test_external_ids_table_schema_and_indexes() -> None:
    table = _get_table("external_ids")
    assert set(table.columns.keys()) == {
        "id",
        "entity_type",
        "entity_id",
        "provider",
        "provider_id",
    }
    assert isinstance(table.columns["id"].type, sa.UUID)
    assert isinstance(table.columns["entity_type"].type, sa.String)
    assert table.columns["entity_type"].type.length == 32
    assert isinstance(table.columns["entity_id"].type, sa.UUID)
    assert isinstance(table.columns["provider"].type, sa.String)
    assert table.columns["provider"].type.length == 64
    assert isinstance(table.columns["provider_id"].type, sa.String)
    assert table.columns["provider_id"].type.length == 255

    unique_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, sa.UniqueConstraint)
    ]
    unique_sets = {
        tuple(constraint.columns.keys()) for constraint in unique_constraints
    }
    assert ("entity_type", "entity_id", "provider") in unique_sets
    assert ("provider", "provider_id", "entity_type") in unique_sets

    index_names = {index.name for index in table.indexes}
    assert "ix_external_ids_provider_lookup" in index_names
    assert "ix_external_ids_entity_lookup" in index_names


def test_source_records_table_schema_and_indexes() -> None:
    table = _get_table("source_records")
    assert set(table.columns.keys()) == {
        "id",
        "provider",
        "entity_type",
        "provider_id",
        "raw",
        "fetched_at",
    }
    assert isinstance(table.columns["id"].type, sa.UUID)
    assert isinstance(table.columns["provider"].type, sa.String)
    assert table.columns["provider"].type.length == 64
    assert isinstance(table.columns["entity_type"].type, sa.String)
    assert table.columns["entity_type"].type.length == 32
    assert isinstance(table.columns["provider_id"].type, sa.String)
    assert table.columns["provider_id"].type.length == 255
    assert isinstance(table.columns["raw"].type, JSONB)

    fetched_at_type = cast(sa.DateTime, table.columns["fetched_at"].type)
    assert fetched_at_type.timezone is True

    unique_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, sa.UniqueConstraint)
    ]
    unique_sets = {
        tuple(constraint.columns.keys()) for constraint in unique_constraints
    }
    assert ("provider", "entity_type", "provider_id") in unique_sets

    index_names = {index.name for index in table.indexes}
    assert "ix_source_records_provider_lookup" in index_names
    assert "ix_source_records_provider_entity_lookup" in index_names
