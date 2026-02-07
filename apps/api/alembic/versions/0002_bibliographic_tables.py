"""Create bibliographic tables.

Revision ID: 0002_bibliographic_tables
Revises: 0001_initial
Create Date: 2025-01-02 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0002_bibliographic_tables"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "authors",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "works",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("first_publish_year", sa.SmallInteger),
        sa.Column("default_cover_url", sa.Text),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "editions",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "work_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("works.id"),
            nullable=False,
        ),
        sa.Column("isbn10", sa.String(10)),
        sa.Column("isbn13", sa.String(13)),
        sa.Column("publisher", sa.String(255)),
        sa.Column("publish_date", sa.Date),
        sa.Column("language", sa.String(32)),
        sa.Column("format", sa.String(64)),
        sa.Column("cover_url", sa.Text),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "work_authors",
        sa.Column(
            "work_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("works.id"),
            primary_key=True,
        ),
        sa.Column(
            "author_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("authors.id"),
            primary_key=True,
        ),
    )

    op.create_index("ix_editions_isbn10", "editions", ["isbn10"])
    op.create_index("ix_editions_isbn13", "editions", ["isbn13"])


def downgrade() -> None:
    op.drop_index("ix_editions_isbn13", table_name="editions")
    op.drop_index("ix_editions_isbn10", table_name="editions")
    op.drop_table("work_authors")
    op.drop_table("editions")
    op.drop_table("works")
    op.drop_table("authors")
