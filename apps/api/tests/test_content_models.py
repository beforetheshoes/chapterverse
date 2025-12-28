from typing import cast

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base
from app.db.models import Highlight, Note, Review


def _get_table(name: str) -> sa.Table:
    return Base.metadata.tables[name]


def test_content_tables_registered() -> None:
    assert Note.__tablename__ in Base.metadata.tables
    assert Highlight.__tablename__ in Base.metadata.tables
    assert Review.__tablename__ in Base.metadata.tables


def test_notes_table_schema() -> None:
    table = _get_table("notes")
    assert set(table.columns.keys()) == {
        "id",
        "user_id",
        "library_item_id",
        "title",
        "body",
        "visibility",
        "created_at",
        "updated_at",
    }
    assert isinstance(table.columns["id"].type, sa.UUID)
    assert isinstance(table.columns["user_id"].type, sa.UUID)
    assert isinstance(table.columns["library_item_id"].type, sa.UUID)
    assert isinstance(table.columns["title"].type, sa.String)
    assert table.columns["title"].type.length == 255
    assert isinstance(table.columns["body"].type, sa.Text)
    assert isinstance(table.columns["visibility"].type, sa.Enum)
    assert table.columns["visibility"].type.enums == ["private", "public"]
    assert table.columns["visibility"].server_default is not None

    created_at_type = cast(sa.DateTime, table.columns["created_at"].type)
    updated_at_type = cast(sa.DateTime, table.columns["updated_at"].type)
    assert created_at_type.timezone is True
    assert updated_at_type.timezone is True

    fk_targets = {fk.target_fullname for fk in table.foreign_keys}
    assert "users.id" in fk_targets
    assert "library_items.id" in fk_targets
    user_fk = next(fk for fk in table.foreign_keys if fk.target_fullname == "users.id")
    library_item_fk = next(
        fk for fk in table.foreign_keys if fk.target_fullname == "library_items.id"
    )
    assert user_fk.ondelete == "CASCADE"
    assert library_item_fk.ondelete == "CASCADE"

    index_names = {index.name for index in table.indexes}
    assert "ix_notes_user_id" in index_names
    assert "ix_notes_library_item_id" in index_names
    assert "ix_notes_visibility" in index_names
    assert "ix_notes_created_at" in index_names


def test_highlights_table_schema() -> None:
    table = _get_table("highlights")
    assert set(table.columns.keys()) == {
        "id",
        "user_id",
        "library_item_id",
        "quote",
        "location",
        "location_type",
        "location_sort",
        "visibility",
        "created_at",
        "updated_at",
    }
    assert isinstance(table.columns["id"].type, sa.UUID)
    assert isinstance(table.columns["user_id"].type, sa.UUID)
    assert isinstance(table.columns["library_item_id"].type, sa.UUID)
    assert isinstance(table.columns["quote"].type, sa.Text)
    assert isinstance(table.columns["location"].type, JSONB)
    assert isinstance(table.columns["location_type"].type, sa.Enum)
    assert table.columns["location_type"].type.enums == [
        "page",
        "percent",
        "location",
        "cfi",
    ]
    assert isinstance(table.columns["location_sort"].type, sa.Numeric)
    assert isinstance(table.columns["visibility"].type, sa.Enum)
    assert table.columns["visibility"].type.enums == ["private", "public"]
    assert table.columns["visibility"].server_default is not None

    created_at_type = cast(sa.DateTime, table.columns["created_at"].type)
    updated_at_type = cast(sa.DateTime, table.columns["updated_at"].type)
    assert created_at_type.timezone is True
    assert updated_at_type.timezone is True

    fk_targets = {fk.target_fullname for fk in table.foreign_keys}
    assert "users.id" in fk_targets
    assert "library_items.id" in fk_targets
    user_fk = next(fk for fk in table.foreign_keys if fk.target_fullname == "users.id")
    library_item_fk = next(
        fk for fk in table.foreign_keys if fk.target_fullname == "library_items.id"
    )
    assert user_fk.ondelete == "CASCADE"
    assert library_item_fk.ondelete == "CASCADE"

    index_names = {index.name for index in table.indexes}
    assert "ix_highlights_user_id" in index_names
    assert "ix_highlights_library_item_id" in index_names
    assert "ix_highlights_visibility" in index_names
    assert "ix_highlights_created_at" in index_names


def test_reviews_table_schema_and_constraints() -> None:
    table = _get_table("reviews")
    assert set(table.columns.keys()) == {
        "id",
        "user_id",
        "library_item_id",
        "title",
        "body",
        "rating",
        "visibility",
        "created_at",
        "updated_at",
    }
    assert isinstance(table.columns["id"].type, sa.UUID)
    assert isinstance(table.columns["user_id"].type, sa.UUID)
    assert isinstance(table.columns["library_item_id"].type, sa.UUID)
    assert isinstance(table.columns["title"].type, sa.String)
    assert table.columns["title"].type.length == 255
    assert isinstance(table.columns["body"].type, sa.Text)
    assert isinstance(table.columns["rating"].type, sa.SmallInteger)
    assert isinstance(table.columns["visibility"].type, sa.Enum)
    assert table.columns["visibility"].type.enums == ["private", "public"]
    assert table.columns["visibility"].server_default is not None

    created_at_type = cast(sa.DateTime, table.columns["created_at"].type)
    updated_at_type = cast(sa.DateTime, table.columns["updated_at"].type)
    assert created_at_type.timezone is True
    assert updated_at_type.timezone is True

    fk_targets = {fk.target_fullname for fk in table.foreign_keys}
    assert "users.id" in fk_targets
    assert "library_items.id" in fk_targets
    user_fk = next(fk for fk in table.foreign_keys if fk.target_fullname == "users.id")
    library_item_fk = next(
        fk for fk in table.foreign_keys if fk.target_fullname == "library_items.id"
    )
    assert user_fk.ondelete == "CASCADE"
    assert library_item_fk.ondelete == "CASCADE"

    unique_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, sa.UniqueConstraint)
    ]
    unique_sets = {
        tuple(constraint.columns.keys()) for constraint in unique_constraints
    }
    assert ("user_id", "library_item_id") in unique_sets

    check_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, sa.CheckConstraint)
    ]
    check_names = {constraint.name for constraint in check_constraints}
    assert "ck_reviews_rating_range" in check_names

    index_names = {index.name for index in table.indexes}
    assert "ix_reviews_user_id" in index_names
    assert "ix_reviews_library_item_id" in index_names
    assert "ix_reviews_visibility" in index_names
    assert "ix_reviews_created_at" in index_names
