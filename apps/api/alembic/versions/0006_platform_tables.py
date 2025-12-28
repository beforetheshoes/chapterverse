"""Create platform tables.

Revision ID: 0006_platform_tables
Revises: 0005_content_tables
Create Date: 2025-01-04 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0006_platform_tables"
down_revision = "0005_content_tables"
branch_labels = None
depends_on = None

api_client_status_enum = postgresql.ENUM(
    "active",
    "suspended",
    name="api_client_status",
    create_type=False,
)


def upgrade() -> None:
    api_client_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "api_clients",
        sa.Column(
            "client_id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "owner_user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            api_client_status_enum,
            nullable=False,
            server_default=sa.text("'active'::api_client_status"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_api_clients_owner_user_id",
        "api_clients",
        ["owner_user_id"],
    )

    op.create_table(
        "api_audit_logs",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "client_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("api_clients.client_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("method", sa.String(16), nullable=False),
        sa.Column("path", sa.Text, nullable=False),
        sa.Column("status", sa.SmallInteger, nullable=False),
        sa.Column("latency_ms", sa.Integer, nullable=False),
        sa.Column("ip", postgresql.INET, nullable=False),
    )
    op.create_index(
        "ix_api_audit_logs_client_user",
        "api_audit_logs",
        ["client_id", "user_id"],
    )
    op.create_index(
        "ix_api_audit_logs_occurred_at",
        "api_audit_logs",
        ["occurred_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_api_audit_logs_occurred_at",
        table_name="api_audit_logs",
    )
    op.drop_index(
        "ix_api_audit_logs_client_user",
        table_name="api_audit_logs",
    )
    op.drop_table("api_audit_logs")
    op.drop_index(
        "ix_api_clients_owner_user_id",
        table_name="api_clients",
    )
    op.drop_table("api_clients")
    api_client_status_enum.drop(op.get_bind(), checkfirst=True)
