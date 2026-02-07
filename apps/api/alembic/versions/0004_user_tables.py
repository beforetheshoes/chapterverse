"""Create user and library tables.

Revision ID: 0004_user_tables
Revises: 0003_external_provider_tables
Create Date: 2025-01-04 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0004_user_tables"
down_revision = "0003_external_provider_tables"
branch_labels = None
depends_on = None

library_item_status_enum = postgresql.ENUM(
    "to_read",
    "reading",
    "completed",
    "abandoned",
    name="library_item_status",
    create_type=False,
)
library_item_visibility_enum = postgresql.ENUM(
    "private",
    "public",
    name="library_item_visibility",
    create_type=False,
)


def upgrade() -> None:
    library_item_status_enum.create(op.get_bind(), checkfirst=True)
    library_item_visibility_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("handle", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(255)),
        sa.Column("avatar_url", sa.Text),
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
        sa.UniqueConstraint("handle", name="uq_users_handle"),
    )

    op.create_table(
        "library_items",
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
            "work_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("works.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "preferred_edition_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("editions.id", ondelete="SET NULL"),
        ),
        sa.Column("status", library_item_status_enum, nullable=False),
        sa.Column("visibility", library_item_visibility_enum, nullable=False),
        sa.Column("rating", sa.SmallInteger),
        sa.Column("tags", sa.dialects.postgresql.ARRAY(sa.String(64))),
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
            "work_id",
            name="uq_library_items_user_work",
        ),
        sa.CheckConstraint(
            "rating >= 0 AND rating <= 10",
            name="ck_library_items_rating_range",
        ),
    )
    op.create_index("ix_library_items_user_id", "library_items", ["user_id"])
    op.create_index("ix_library_items_status", "library_items", ["status"])
    op.create_index(
        "ix_library_items_visibility",
        "library_items",
        ["visibility"],
    )
    op.create_index(
        "ix_library_items_tags",
        "library_items",
        ["tags"],
        postgresql_using="gin",
    )

    op.create_table(
        "reading_sessions",
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
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("pages_read", sa.Integer),
        sa.Column("progress_percent", sa.Numeric(5, 2)),
        sa.Column("note", sa.Text),
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
        sa.CheckConstraint(
            "pages_read >= 0",
            name="ck_reading_sessions_pages_read_nonnegative",
        ),
        sa.CheckConstraint(
            "progress_percent >= 0 AND progress_percent <= 100",
            name="ck_reading_sessions_progress_percent_range",
        ),
        sa.CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="ck_reading_sessions_ended_after_start",
        ),
    )
    op.create_index(
        "ix_reading_sessions_user_id",
        "reading_sessions",
        ["user_id"],
    )
    op.create_index(
        "ix_reading_sessions_library_item_id",
        "reading_sessions",
        ["library_item_id"],
    )

    op.create_table(
        "reading_state_events",
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
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_reading_state_events_user_id",
        "reading_state_events",
        ["user_id"],
    )
    op.create_index(
        "ix_reading_state_events_library_item_id",
        "reading_state_events",
        ["library_item_id"],
    )
    op.create_index(
        "ix_reading_state_events_occurred_at",
        "reading_state_events",
        ["occurred_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_reading_state_events_occurred_at",
        table_name="reading_state_events",
    )
    op.drop_index(
        "ix_reading_state_events_library_item_id",
        table_name="reading_state_events",
    )
    op.drop_index(
        "ix_reading_state_events_user_id",
        table_name="reading_state_events",
    )
    op.drop_table("reading_state_events")
    op.drop_index(
        "ix_reading_sessions_library_item_id",
        table_name="reading_sessions",
    )
    op.drop_index(
        "ix_reading_sessions_user_id",
        table_name="reading_sessions",
    )
    op.drop_table("reading_sessions")
    op.drop_index("ix_library_items_tags", table_name="library_items")
    op.drop_index("ix_library_items_visibility", table_name="library_items")
    op.drop_index("ix_library_items_status", table_name="library_items")
    op.drop_index("ix_library_items_user_id", table_name="library_items")
    op.drop_table("library_items")
    op.drop_table("users")
    library_item_visibility_enum.drop(op.get_bind(), checkfirst=True)
    library_item_status_enum.drop(op.get_bind(), checkfirst=True)
