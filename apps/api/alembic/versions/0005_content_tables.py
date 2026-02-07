"""Create content tables.

Revision ID: 0005_content_tables
Revises: 0004_user_tables
Create Date: 2025-01-04 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0005_content_tables"
down_revision = "0004_user_tables"
branch_labels = None
depends_on = None

content_visibility_enum = postgresql.ENUM(
    "private",
    "public",
    name="content_visibility",
    create_type=False,
)
highlight_location_type_enum = postgresql.ENUM(
    "page",
    "percent",
    "location",
    "cfi",
    name="highlight_location_type",
    create_type=False,
)


def upgrade() -> None:
    content_visibility_enum.create(op.get_bind(), checkfirst=True)
    highlight_location_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "notes",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "library_item_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("library_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255)),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column(
            "visibility",
            content_visibility_enum,
            nullable=False,
            server_default=sa.text("'private'::content_visibility"),
        ),
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
    op.create_index("ix_notes_user_id", "notes", ["user_id"])
    op.create_index("ix_notes_library_item_id", "notes", ["library_item_id"])
    op.create_index("ix_notes_visibility", "notes", ["visibility"])
    op.create_index("ix_notes_created_at", "notes", ["created_at"])

    op.create_table(
        "highlights",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "library_item_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("library_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quote", sa.Text, nullable=False),
        sa.Column("location", postgresql.JSONB),
        sa.Column("location_type", highlight_location_type_enum),
        sa.Column("location_sort", sa.Numeric(10, 2)),
        sa.Column(
            "visibility",
            content_visibility_enum,
            nullable=False,
            server_default=sa.text("'private'::content_visibility"),
        ),
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
    op.create_index("ix_highlights_user_id", "highlights", ["user_id"])
    op.create_index(
        "ix_highlights_library_item_id",
        "highlights",
        ["library_item_id"],
    )
    op.create_index("ix_highlights_visibility", "highlights", ["visibility"])
    op.create_index("ix_highlights_created_at", "highlights", ["created_at"])

    op.create_table(
        "reviews",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "library_item_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("library_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255)),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("rating", sa.SmallInteger),
        sa.Column(
            "visibility",
            content_visibility_enum,
            nullable=False,
            server_default=sa.text("'private'::content_visibility"),
        ),
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
        sa.UniqueConstraint(
            "user_id",
            "library_item_id",
            name="uq_reviews_user_library_item",
        ),
        sa.CheckConstraint(
            "rating >= 0 AND rating <= 10",
            name="ck_reviews_rating_range",
        ),
    )
    op.create_index("ix_reviews_user_id", "reviews", ["user_id"])
    op.create_index("ix_reviews_library_item_id", "reviews", ["library_item_id"])
    op.create_index("ix_reviews_visibility", "reviews", ["visibility"])
    op.create_index("ix_reviews_created_at", "reviews", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_reviews_created_at", table_name="reviews")
    op.drop_index("ix_reviews_visibility", table_name="reviews")
    op.drop_index("ix_reviews_library_item_id", table_name="reviews")
    op.drop_index("ix_reviews_user_id", table_name="reviews")
    op.drop_table("reviews")
    op.drop_index("ix_highlights_created_at", table_name="highlights")
    op.drop_index("ix_highlights_visibility", table_name="highlights")
    op.drop_index("ix_highlights_library_item_id", table_name="highlights")
    op.drop_index("ix_highlights_user_id", table_name="highlights")
    op.drop_table("highlights")
    op.drop_index("ix_notes_created_at", table_name="notes")
    op.drop_index("ix_notes_visibility", table_name="notes")
    op.drop_index("ix_notes_library_item_id", table_name="notes")
    op.drop_index("ix_notes_user_id", table_name="notes")
    op.drop_table("notes")
    highlight_location_type_enum.drop(op.get_bind(), checkfirst=True)
    content_visibility_enum.drop(op.get_bind(), checkfirst=True)
