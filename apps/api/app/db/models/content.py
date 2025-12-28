from __future__ import annotations

import datetime as dt
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

content_visibility_enum = ENUM(
    "private",
    "public",
    name="content_visibility",
    create_type=False,
)
highlight_location_type_enum = ENUM(
    "page",
    "percent",
    "location",
    "cfi",
    name="highlight_location_type",
    create_type=False,
)


class Note(Base):
    __tablename__ = "notes"
    __table_args__ = (
        sa.Index("ix_notes_user_id", "user_id"),
        sa.Index("ix_notes_library_item_id", "library_item_id"),
        sa.Index("ix_notes_visibility", "visibility"),
        sa.Index("ix_notes_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    library_item_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("library_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(sa.String(255))
    body: Mapped[str] = mapped_column(sa.Text, nullable=False)
    visibility: Mapped[str] = mapped_column(
        content_visibility_enum,
        nullable=False,
        server_default=sa.text("'private'::content_visibility"),
    )
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


class Highlight(Base):
    __tablename__ = "highlights"
    __table_args__ = (
        sa.Index("ix_highlights_user_id", "user_id"),
        sa.Index("ix_highlights_library_item_id", "library_item_id"),
        sa.Index("ix_highlights_visibility", "visibility"),
        sa.Index("ix_highlights_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    library_item_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("library_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    quote: Mapped[str] = mapped_column(sa.Text, nullable=False)
    location: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    location_type: Mapped[str | None] = mapped_column(highlight_location_type_enum)
    location_sort: Mapped[float | None] = mapped_column(sa.Numeric(10, 2))
    visibility: Mapped[str] = mapped_column(
        content_visibility_enum,
        nullable=False,
        server_default=sa.text("'private'::content_visibility"),
    )
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


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        sa.UniqueConstraint(
            "user_id",
            "library_item_id",
            name="uq_reviews_user_library_item",
        ),
        sa.CheckConstraint(
            "rating >= 0 AND rating <= 10",
            name="ck_reviews_rating_range",
        ),
        sa.Index("ix_reviews_user_id", "user_id"),
        sa.Index("ix_reviews_library_item_id", "library_item_id"),
        sa.Index("ix_reviews_visibility", "visibility"),
        sa.Index("ix_reviews_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    library_item_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("library_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(sa.String(255))
    body: Mapped[str] = mapped_column(sa.Text, nullable=False)
    rating: Mapped[int | None] = mapped_column(sa.SmallInteger)
    visibility: Mapped[str] = mapped_column(
        content_visibility_enum,
        nullable=False,
        server_default=sa.text("'private'::content_visibility"),
    )
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
