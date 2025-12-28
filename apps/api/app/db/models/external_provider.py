from __future__ import annotations

import datetime as dt
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ExternalId(Base):
    __tablename__ = "external_ids"
    __table_args__ = (
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
        sa.Index("ix_external_ids_provider_lookup", "provider", "provider_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    entity_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(sa.UUID(as_uuid=True), nullable=False)
    provider: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    provider_id: Mapped[str] = mapped_column(sa.String(255), nullable=False)


class SourceRecord(Base):
    __tablename__ = "source_records"
    __table_args__ = (
        sa.UniqueConstraint(
            "provider",
            "entity_type",
            "provider_id",
            name="uq_source_records_provider_entity",
        ),
        sa.Index("ix_source_records_provider_lookup", "provider", "provider_id"),
        sa.Index("ix_source_records_provider_entity_lookup", "provider", "entity_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    provider: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    provider_id: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    raw: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    fetched_at: Mapped[dt.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )
