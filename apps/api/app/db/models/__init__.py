from __future__ import annotations

from app.db.models.bibliography import Author, Edition, Work, WorkAuthor
from app.db.models.external_provider import ExternalId, SourceRecord

__all__ = [
    "Author",
    "Edition",
    "ExternalId",
    "SourceRecord",
    "Work",
    "WorkAuthor",
]
