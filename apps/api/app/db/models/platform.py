from __future__ import annotations

import datetime as dt
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, INET
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

api_client_status_enum = ENUM(
    "active",
    "suspended",
    name="api_client_status",
    create_type=False,
)


class ApiClient(Base):
    __tablename__ = "api_clients"
    __table_args__ = (sa.Index("ix_api_clients_owner_user_id", "owner_user_id"),)

    client_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        api_client_status_enum,
        nullable=False,
        server_default=sa.text("'active'::api_client_status"),
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )


class ApiAuditLog(Base):
    __tablename__ = "api_audit_logs"
    __table_args__ = (
        sa.Index("ix_api_audit_logs_client_user", "client_id", "user_id"),
        sa.Index("ix_api_audit_logs_occurred_at", "occurred_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    occurred_at: Mapped[dt.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("api_clients.client_id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
    )
    method: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    path: Mapped[str] = mapped_column(sa.Text, nullable=False)
    status: Mapped[int] = mapped_column(sa.SmallInteger, nullable=False)
    latency_ms: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    ip: Mapped[str] = mapped_column(INET, nullable=False)
