from typing import cast

import sqlalchemy as sa

from app.db.base import Base
from app.db.models import Author, Edition, Work, WorkAuthor


def _get_table(name: str) -> sa.Table:
    return Base.metadata.tables[name]


def test_bibliography_tables_registered() -> None:
    assert Author.__tablename__ in Base.metadata.tables
    assert Work.__tablename__ in Base.metadata.tables
    assert Edition.__tablename__ in Base.metadata.tables
    assert WorkAuthor.__tablename__ in Base.metadata.tables


def test_author_table_schema() -> None:
    table = _get_table("authors")
    assert set(table.columns.keys()) == {"id", "name", "created_at", "updated_at"}
    assert isinstance(table.columns["id"].type, sa.UUID)
    assert isinstance(table.columns["name"].type, sa.String)
    assert table.columns["name"].type.length == 255
    created_at_type = cast(sa.DateTime, table.columns["created_at"].type)
    updated_at_type = cast(sa.DateTime, table.columns["updated_at"].type)
    assert created_at_type.timezone is True
    assert updated_at_type.timezone is True


def test_work_table_schema() -> None:
    table = _get_table("works")
    assert set(table.columns.keys()) == {
        "id",
        "title",
        "description",
        "first_publish_year",
        "default_cover_url",
        "created_at",
        "updated_at",
    }
    assert isinstance(table.columns["title"].type, sa.String)
    assert table.columns["title"].type.length == 512
    assert isinstance(table.columns["first_publish_year"].type, sa.SmallInteger)


def test_edition_table_schema_and_indexes() -> None:
    table = _get_table("editions")
    assert set(table.columns.keys()) == {
        "id",
        "work_id",
        "isbn10",
        "isbn13",
        "publisher",
        "publish_date",
        "language",
        "format",
        "cover_url",
        "created_at",
        "updated_at",
    }
    assert isinstance(table.columns["isbn10"].type, sa.String)
    assert table.columns["isbn10"].type.length == 10
    assert isinstance(table.columns["isbn13"].type, sa.String)
    assert table.columns["isbn13"].type.length == 13
    assert isinstance(table.columns["publisher"].type, sa.String)
    assert isinstance(table.columns["publish_date"].type, sa.Date)
    assert isinstance(table.columns["language"].type, sa.String)
    assert isinstance(table.columns["format"].type, sa.String)
    assert isinstance(table.columns["cover_url"].type, sa.Text)

    fk_targets = {fk.column.table.name for fk in table.foreign_keys}
    assert fk_targets == {"works"}

    index_names = {index.name for index in table.indexes}
    assert "ix_editions_isbn10" in index_names
    assert "ix_editions_isbn13" in index_names


def test_work_authors_composite_key() -> None:
    table = _get_table("work_authors")
    assert set(table.columns.keys()) == {"work_id", "author_id"}
    pk_columns = {col.name for col in table.primary_key.columns}
    assert pk_columns == {"work_id", "author_id"}
    fk_targets = {fk.column.table.name for fk in table.foreign_keys}
    assert fk_targets == {"works", "authors"}
