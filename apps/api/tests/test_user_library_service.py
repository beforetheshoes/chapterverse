from __future__ import annotations

import datetime as dt
import uuid
from typing import Any, cast

import pytest

from app.db.models.users import LibraryItem, User
from app.services.user_library import (
    _decode_cursor,
    _default_handle,
    _encode_cursor,
    create_or_get_library_item,
    delete_library_item,
    get_or_create_profile,
    list_library_items,
    update_library_item,
    update_profile,
)


class FakeExecuteResult:
    def __init__(self, rows: list[tuple[Any, str]]) -> None:
        self._rows = rows

    def all(self) -> list[tuple[Any, str]]:
        return self._rows


class FakeSession:
    def __init__(self) -> None:
        self.get_map: dict[tuple[type[Any], Any], Any] = {}
        self.scalar_values: list[Any] = []
        self.added: list[Any] = []
        self.execute_rows: list[tuple[Any, str]] = []
        self.deleted: list[Any] = []
        self.committed = False

    def get(self, model: type[Any], key: Any) -> Any:
        return self.get_map.get((model, key))

    def scalar(self, _stmt: Any) -> Any:
        if self.scalar_values:
            return self.scalar_values.pop(0)
        return None

    def add(self, obj: Any) -> None:
        if getattr(obj, "id", None) is None and hasattr(obj, "id"):
            obj.id = uuid.uuid4()
        self.added.append(obj)
        if hasattr(obj, "id"):
            self.get_map[(type(obj), obj.id)] = obj

    def commit(self) -> None:
        self.committed = True

    def execute(self, _stmt: Any) -> FakeExecuteResult:
        return FakeExecuteResult(self.execute_rows)

    def delete(self, obj: Any) -> None:
        self.deleted.append(obj)


def test_cursor_encode_decode_roundtrip() -> None:
    created_at = dt.datetime.now(tz=dt.UTC).replace(microsecond=0)
    item_id = uuid.uuid4()
    cursor = _encode_cursor(created_at, item_id)
    decoded_created, decoded_id = _decode_cursor(cursor)
    assert decoded_created == created_at
    assert decoded_id == item_id


def test_cursor_decode_invalid_raises() -> None:
    with pytest.raises(ValueError):
        _decode_cursor("not-base64")


def test_default_handle() -> None:
    user_id = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert _default_handle(user_id) == "user_aaaaaaaa"


def test_get_or_create_profile_creates_when_missing() -> None:
    session = FakeSession()
    user_id = uuid.uuid4()
    profile = get_or_create_profile(cast(Any, session), user_id=user_id)
    assert profile.id == user_id
    assert session.committed is True


def test_update_profile_validates_handle() -> None:
    session = FakeSession()
    user_id = uuid.uuid4()
    get_or_create_profile(cast(Any, session), user_id=user_id)

    with pytest.raises(ValueError):
        update_profile(
            cast(Any, session),
            user_id=user_id,
            handle="   ",
            display_name=None,
            avatar_url=None,
        )


def test_update_profile_rejects_duplicate_handle() -> None:
    session = FakeSession()
    user_id = uuid.uuid4()
    get_or_create_profile(cast(Any, session), user_id=user_id)
    session.scalar_values = [object()]

    with pytest.raises(ValueError):
        update_profile(
            cast(Any, session),
            user_id=user_id,
            handle="taken",
            display_name=None,
            avatar_url=None,
        )


def test_update_profile_updates_fields() -> None:
    session = FakeSession()
    user_id = uuid.uuid4()
    profile = get_or_create_profile(cast(Any, session), user_id=user_id)
    session.scalar_values = [None]

    updated = update_profile(
        cast(Any, session),
        user_id=user_id,
        handle="fresh",
        display_name=" Name ",
        avatar_url=" https://example.com/avatar.png ",
    )
    assert updated is profile
    assert updated.handle == "fresh"
    assert updated.display_name == "Name"
    assert updated.avatar_url == "https://example.com/avatar.png"


def test_create_or_get_library_item_handles_missing_work() -> None:
    session = FakeSession()
    with pytest.raises(LookupError):
        create_or_get_library_item(
            cast(Any, session),
            user_id=uuid.uuid4(),
            work_id=uuid.uuid4(),
            status=None,
            visibility=None,
            rating=None,
            tags=None,
            preferred_edition_id=None,
        )


def test_create_or_get_library_item_returns_existing() -> None:
    session = FakeSession()
    existing = type(
        "Item",
        (),
        {
            "id": uuid.uuid4(),
            "work_id": uuid.uuid4(),
            "status": "to_read",
            "visibility": "private",
            "rating": None,
            "tags": None,
        },
    )()
    session.scalar_values = [uuid.uuid4(), existing]

    item, created = create_or_get_library_item(
        cast(Any, session),
        user_id=uuid.uuid4(),
        work_id=uuid.uuid4(),
        status=None,
        visibility=None,
        rating=None,
        tags=None,
        preferred_edition_id=None,
    )
    assert item is existing
    assert created is False


def test_create_or_get_library_item_creates_new() -> None:
    session = FakeSession()
    session.scalar_values = [uuid.uuid4(), None]

    item, created = create_or_get_library_item(
        cast(Any, session),
        user_id=uuid.uuid4(),
        work_id=uuid.uuid4(),
        status="reading",
        visibility="public",
        rating=8,
        tags=["tag"],
        preferred_edition_id=None,
    )
    assert created is True
    assert item.status == "reading"
    assert session.committed is True


def test_create_or_get_library_item_creates_profile_for_first_time_user() -> None:
    session = FakeSession()
    user_id = uuid.uuid4()
    work_id = uuid.uuid4()
    session.scalar_values = [work_id, None]

    item, created = create_or_get_library_item(
        cast(Any, session),
        user_id=user_id,
        work_id=work_id,
        status=None,
        visibility=None,
        rating=None,
        tags=None,
        preferred_edition_id=None,
    )

    assert created is True
    assert item.user_id == user_id
    assert isinstance(session.added[0], User)
    assert isinstance(session.added[1], LibraryItem)
    assert session.added[0].id == user_id


def test_list_library_items_invalid_cursor() -> None:
    session = FakeSession()
    with pytest.raises(ValueError):
        list_library_items(
            cast(Any, session),
            user_id=uuid.uuid4(),
            limit=10,
            cursor="bad",
            status=None,
            tag=None,
            visibility=None,
        )


def test_list_library_items_returns_cursor() -> None:
    session = FakeSession()
    now = dt.datetime.now(tz=dt.UTC).replace(microsecond=0)
    item1 = type(
        "Item",
        (),
        {
            "id": uuid.uuid4(),
            "work_id": uuid.uuid4(),
            "status": "reading",
            "visibility": "private",
            "rating": None,
            "tags": [],
            "created_at": now,
        },
    )()
    item2 = type(
        "Item",
        (),
        {
            "id": uuid.uuid4(),
            "work_id": uuid.uuid4(),
            "status": "reading",
            "visibility": "private",
            "rating": None,
            "tags": [],
            "created_at": now,
        },
    )()
    session.execute_rows = [(item1, "One"), (item2, "Two")]

    result = list_library_items(
        cast(Any, session),
        user_id=uuid.uuid4(),
        limit=1,
        cursor=None,
        status="reading",
        tag=None,
        visibility=None,
    )
    assert len(result["items"]) == 1
    assert result["next_cursor"] is not None


def test_update_library_item_requires_at_least_one_field() -> None:
    session = FakeSession()
    with pytest.raises(ValueError):
        update_library_item(
            cast(Any, session),
            user_id=uuid.uuid4(),
            item_id=uuid.uuid4(),
            updates={},
        )


def test_update_library_item_requires_ownership() -> None:
    session = FakeSession()
    session.scalar_values = [None]
    with pytest.raises(LookupError):
        update_library_item(
            cast(Any, session),
            user_id=uuid.uuid4(),
            item_id=uuid.uuid4(),
            updates={"status": "reading"},
        )


def test_update_library_item_applies_requested_fields() -> None:
    session = FakeSession()
    item = type(
        "Item",
        (),
        {
            "id": uuid.uuid4(),
            "work_id": uuid.uuid4(),
            "status": "to_read",
            "visibility": "private",
            "rating": None,
            "tags": [],
            "preferred_edition_id": None,
        },
    )()
    session.scalar_values = [item]

    updated = update_library_item(
        cast(Any, session),
        user_id=uuid.uuid4(),
        item_id=item.id,
        updates={"status": "reading", "rating": 9, "tags": ["memoir"]},
    )

    assert updated is item
    assert item.status == "reading"
    assert item.rating == 9
    assert item.tags == ["memoir"]
    assert session.committed is True


def test_delete_library_item_requires_ownership() -> None:
    session = FakeSession()
    session.scalar_values = [None]
    with pytest.raises(LookupError):
        delete_library_item(
            cast(Any, session),
            user_id=uuid.uuid4(),
            item_id=uuid.uuid4(),
        )


def test_delete_library_item_deletes_and_commits() -> None:
    session = FakeSession()
    item = object()
    session.scalar_values = [item]

    delete_library_item(
        cast(Any, session),
        user_id=uuid.uuid4(),
        item_id=uuid.uuid4(),
    )

    assert session.deleted == [item]
    assert session.committed is True
