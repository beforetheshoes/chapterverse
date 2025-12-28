"""Create external provider tracking tables.

Revision ID: 0003_external_provider_tables
Revises: 0002_bibliographic_tables
Create Date: 2025-01-03 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0003_external_provider_tables"
down_revision = "0002_bibliographic_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "external_ids",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("provider_id", sa.String(255), nullable=False),
        sa.UniqueConstraint(
            "entity_type",
            "entity_id",
            "provider",
            name="uq_external_ids_entity_provider",
        ),
        sa.UniqueConstraint(
            "provider",
            "provider_id",
            "entity_type",
            name="uq_external_ids_provider_id",
        ),
    )
    op.create_index(
        "ix_external_ids_provider_lookup",
        "external_ids",
        ["provider", "provider_id"],
    )
    op.create_index(
        "ix_external_ids_entity_lookup",
        "external_ids",
        ["entity_type", "entity_id"],
    )

    op.create_table(
        "source_records",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("provider_id", sa.String(255), nullable=False),
        sa.Column("raw", sa.dialects.postgresql.JSONB, nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "provider",
            "entity_type",
            "provider_id",
            name="uq_source_records_provider_entity",
        ),
    )
    op.create_index(
        "ix_source_records_provider_lookup",
        "source_records",
        ["provider", "provider_id"],
    )
    op.create_index(
        "ix_source_records_provider_entity_lookup",
        "source_records",
        ["provider", "entity_type"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_source_records_provider_entity_lookup",
        table_name="source_records",
    )
    op.drop_index("ix_source_records_provider_lookup", table_name="source_records")
    op.drop_table("source_records")
    op.drop_index("ix_external_ids_entity_lookup", table_name="external_ids")
    op.drop_index("ix_external_ids_provider_lookup", table_name="external_ids")
    op.drop_table("external_ids")
