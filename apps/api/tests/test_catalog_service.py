from __future__ import annotations

import uuid
from typing import Any, cast

import sqlalchemy as sa

from app.db.models.bibliography import Author, Edition, Work
from app.db.models.external_provider import ExternalId, SourceRecord
from app.services.catalog import (
    _get_external_id,
    _upsert_source_record,
    import_openlibrary_bundle,
)
from app.services.open_library import OpenLibraryWorkBundle


class FakeSession:
    def __init__(self) -> None:
        self.added: list[Any] = []
        self.source_record: SourceRecord | None = None
        self.scalar_values: list[Any] = []
        self.get_map: dict[tuple[type[Any], Any], Any] = {}
        self.committed = False

    def add(self, obj: Any) -> None:
        self.added.append(obj)
        if isinstance(obj, SourceRecord):
            self.source_record = obj

    def flush(self) -> None:
        for obj in self.added:
            if getattr(obj, "id", None) is None and hasattr(obj, "id"):
                obj.id = uuid.uuid4()

    def scalar(self, stmt: sa.Select[Any]) -> Any:
        if self.scalar_values:
            return self.scalar_values.pop(0)
        return None

    def get(self, model: type[Any], key: Any) -> Any:
        return self.get_map.get((model, key))

    def commit(self) -> None:
        self.committed = True


def _bundle() -> OpenLibraryWorkBundle:
    return OpenLibraryWorkBundle(
        work_key="/works/OL1W",
        title="Book",
        description="Desc",
        first_publish_year=2000,
        cover_url="https://covers.openlibrary.org/b/id/1-L.jpg",
        authors=[{"key": "/authors/OL2A", "name": "Author A"}],
        edition={
            "key": "/books/OL3M",
            "isbn10": "123",
            "isbn13": "456",
            "publisher": "Pub",
            "publish_date": None,
        },
        raw_work={"k": "v"},
        raw_edition={"ek": "ev"},
    )


def test_get_external_id_delegates_to_session_scalar() -> None:
    session = FakeSession()
    expected = ExternalId(
        entity_type="work",
        entity_id=uuid.uuid4(),
        provider="openlibrary",
        provider_id="/works/OL1W",
    )
    session.scalar_values = [expected]
    actual = _get_external_id(
        session=cast(Any, session),
        entity_type="work",
        provider="openlibrary",
        provider_id="/works/OL1W",
    )
    assert actual is expected


def test_upsert_source_record_creates_and_updates() -> None:
    session = FakeSession()
    _upsert_source_record(
        cast(Any, session),
        provider="openlibrary",
        entity_type="work",
        provider_id="/works/OL1W",
        raw={"a": 1},
    )
    assert session.source_record is not None

    existing = SourceRecord(
        provider="openlibrary",
        entity_type="work",
        provider_id="/works/OL1W",
        raw={"a": 1},
    )
    session.scalar_values = [existing]
    _upsert_source_record(
        cast(Any, session),
        provider="openlibrary",
        entity_type="work",
        provider_id="/works/OL1W",
        raw={"a": 2},
    )
    assert existing.raw == {"a": 2}


def test_import_openlibrary_bundle_creates_records() -> None:
    session = FakeSession()
    # one scalar call for existing work-author link -> none
    session.scalar_values = [None]

    result = import_openlibrary_bundle(cast(Any, session), bundle=_bundle())

    assert session.committed is True
    assert result["work"]["created"] is True
    assert result["authors_created"] == 1
    assert result["edition"]["created"] is True


def test_import_openlibrary_bundle_uses_existing_records() -> None:
    session = FakeSession()
    work_id = uuid.uuid4()
    author_id = uuid.uuid4()
    edition_id = uuid.uuid4()

    work_external = ExternalId(
        entity_type="work",
        entity_id=work_id,
        provider="openlibrary",
        provider_id="/works/OL1W",
    )
    author_external = ExternalId(
        entity_type="author",
        entity_id=author_id,
        provider="openlibrary",
        provider_id="/authors/OL2A",
    )
    edition_external = ExternalId(
        entity_type="edition",
        entity_id=edition_id,
        provider="openlibrary",
        provider_id="/books/OL3M",
    )

    # scalar sequence: source record exists (work), existing work-author link, source record exists (edition)
    session.scalar_values = [
        SourceRecord(
            provider="openlibrary",
            entity_type="work",
            provider_id="/works/OL1W",
            raw={},
        ),
        object(),
        SourceRecord(
            provider="openlibrary",
            entity_type="edition",
            provider_id="/books/OL3M",
            raw={},
        ),
    ]
    session.get_map = {
        (Work, work_id): Work(id=work_id, title="Book", description=None),
        (Author, author_id): Author(id=author_id, name="Author A"),
        (
            Edition,
            edition_id,
        ): Edition(
            id=edition_id,
            work_id=work_id,
            publisher=None,
            publish_date=None,
            language=None,
            format=None,
            cover_url=None,
        ),
    }

    def fake_get_external(
        _session: FakeSession,
        *,
        entity_type: str,
        provider: str,
        provider_id: str,
    ) -> ExternalId | None:
        assert provider == "openlibrary"
        mapping = {
            ("work", "/works/OL1W"): work_external,
            ("author", "/authors/OL2A"): author_external,
            ("edition", "/books/OL3M"): edition_external,
        }
        return mapping.get((entity_type, provider_id))

    import app.services.catalog as catalog

    original = catalog._get_external_id
    try:
        catalog._get_external_id = cast(Any, fake_get_external)
        result = import_openlibrary_bundle(cast(Any, session), bundle=_bundle())
    finally:
        catalog._get_external_id = original

    assert result["work"]["created"] is False
    assert result["authors_created"] == 0
    assert result["edition"]["created"] is False


def test_import_openlibrary_bundle_raises_when_external_missing_target() -> None:
    session = FakeSession()
    missing_work_external = ExternalId(
        entity_type="work",
        entity_id=uuid.uuid4(),
        provider="openlibrary",
        provider_id="/works/OL1W",
    )

    import app.services.catalog as catalog

    original = catalog._get_external_id
    try:
        catalog._get_external_id = cast(
            Any, lambda *_args, **_kwargs: missing_work_external
        )
        try:
            import_openlibrary_bundle(cast(Any, session), bundle=_bundle())
        except RuntimeError as exc:
            assert "missing work" in str(exc)
        else:
            raise AssertionError("expected RuntimeError")
    finally:
        catalog._get_external_id = original
