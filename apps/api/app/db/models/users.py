from __future__ import annotations

import datetime as dt
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

library_item_status_enum = ENUM(
    "to_read",
    "reading",
    "completed",
    "abandoned",
    name="library_item_status",
    create_type=False,
)
library_item_visibility_enum = ENUM(
    "private",
    "public",
    name="library_item_visibility",
    create_type=False,
)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (sa.UniqueConstraint("handle", name="uq_users_handle"),)

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("auth.users.id"),
        primary_key=True,
    )
    handle: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    display_name: Mapped[str | None] = mapped_column(sa.String(255))
    avatar_url: Mapped[str | None] = mapped_column(sa.Text)
    created_at: Mapped[dt.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )


class LibraryItem(Base):
    __tablename__ = "library_items"
    __table_args__ = (
        sa.UniqueConstraint(
            "user_id",
            "work_id",
            name="uq_library_items_user_work",
        ),
        sa.Index("ix_library_items_user_id", "user_id"),
        sa.Index("ix_library_items_status", "status"),
        sa.Index("ix_library_items_visibility", "visibility"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id"),
        nullable=False,
    )
    work_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("works.id"),
        nullable=False,
    )
    preferred_edition_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("editions.id"),
    )
    status: Mapped[str] = mapped_column(library_item_status_enum, nullable=False)
    visibility: Mapped[str] = mapped_column(
        library_item_visibility_enum,
        nullable=False,
    )
    rating: Mapped[int | None] = mapped_column(sa.SmallInteger)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(sa.String(64)))
    created_at: Mapped[dt.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )


class ReadingSession(Base):
    __tablename__ = "reading_sessions"
    __table_args__ = (
        sa.Index("ix_reading_sessions_user_id", "user_id"),
        sa.Index("ix_reading_sessions_library_item_id", "library_item_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id"),
        nullable=False,
    )
    library_item_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("library_items.id"),
        nullable=False,
    )
    started_at: Mapped[dt.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
    )
    ended_at: Mapped[dt.datetime | None] = mapped_column(sa.DateTime(timezone=True))
    pages_read: Mapped[int | None] = mapped_column(sa.Integer)
    progress_percent: Mapped[float | None] = mapped_column(sa.Numeric(5, 2))
    note: Mapped[str | None] = mapped_column(sa.Text)
    created_at: Mapped[dt.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )


class ReadingStateEvent(Base):
    __tablename__ = "reading_state_events"
    __table_args__ = (
        sa.Index("ix_reading_state_events_user_id", "user_id"),
        sa.Index("ix_reading_state_events_library_item_id", "library_item_id"),
        sa.Index("ix_reading_state_events_occurred_at", "occurred_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id"),
        nullable=False,
    )
    library_item_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("library_items.id"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    occurred_at: Mapped[dt.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )
