from __future__ import annotations

import datetime as dt
import os
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import cast

import psycopg
import pytest
from psycopg import sql
from psycopg.types.json import Json

USER_SCOPED_TABLES = {
    "users": "id",
    "library_items": "user_id",
    "reading_sessions": "user_id",
    "reading_state_events": "user_id",
    "notes": "user_id",
    "highlights": "user_id",
    "reviews": "user_id",
    "api_clients": "owner_user_id",
}

READ_ONLY_TABLES = [
    "authors",
    "works",
    "editions",
    "work_authors",
    "external_ids",
    "source_records",
]


def _get_db_url() -> str:
    db_url = (
        os.getenv("SUPABASE_DB_URL") or os.getenv("POSTGRES_URL") or os.getenv("DB_URL")
    )
    if not db_url:
        pytest.skip("SUPABASE_DB_URL not set; requires local Supabase")
    if db_url.startswith("postgresql+psycopg://"):
        db_url = db_url.replace("postgresql+psycopg://", "postgresql://", 1)
    return db_url


def _auth_user_columns(conn: psycopg.Connection) -> set[str]:
    rows = conn.execute(
        """
        select column_name
        from information_schema.columns
        where table_schema = 'auth'
          and table_name = 'users';
        """
    ).fetchall()
    return {row[0] for row in rows}


def _ensure_auth_instance(conn: psycopg.Connection) -> uuid.UUID:
    row = conn.execute("select id from auth.instances limit 1;").fetchone()
    if row is not None:
        return cast(uuid.UUID, row[0])

    instance_id = uuid.uuid4()
    conn.execute(
        "insert into auth.instances (id, created_at, updated_at) values (%s, %s, %s);",
        (instance_id, dt.datetime.now(tz=dt.UTC), dt.datetime.now(tz=dt.UTC)),
    )
    return instance_id


def _insert_auth_user(conn: psycopg.Connection, user_id: uuid.UUID, email: str) -> None:
    columns = _auth_user_columns(conn)
    values: dict[str, object] = {"id": user_id}

    if "email" in columns:
        values["email"] = email
    if "aud" in columns:
        values["aud"] = "authenticated"
    if "role" in columns:
        values["role"] = "authenticated"
    if "instance_id" in columns:
        values["instance_id"] = _ensure_auth_instance(conn)
    if "raw_app_meta_data" in columns:
        values["raw_app_meta_data"] = Json({})
    if "raw_user_meta_data" in columns:
        values["raw_user_meta_data"] = Json({})
    if "created_at" in columns:
        values["created_at"] = dt.datetime.now(tz=dt.UTC)
    if "updated_at" in columns:
        values["updated_at"] = dt.datetime.now(tz=dt.UTC)
    if "is_sso_user" in columns:
        values["is_sso_user"] = False
    if "is_super_admin" in columns:
        values["is_super_admin"] = False

    query = sql.SQL("insert into auth.users ({fields}) values ({values})").format(
        fields=sql.SQL(", ").join(sql.Identifier(key) for key in values.keys()),
        values=sql.SQL(", ").join(sql.Placeholder(key) for key in values.keys()),
    )
    conn.execute(query, values)


@contextmanager
def _authenticated_conn(
    db_url: str, user_id: uuid.UUID
) -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(db_url, autocommit=True)
    try:
        conn.execute("set role authenticated;")
        conn.execute(
            "select set_config('request.jwt.claim.role', 'authenticated', false);"
        )
        conn.execute(
            "select set_config('request.jwt.claim.sub', %s, false);", (str(user_id),)
        )
        yield conn
    finally:
        conn.close()


def _assert_insert_and_delete(
    conn: psycopg.Connection,
    table: str,
    pk_column: str,
    insert_sql: str,
    own_params: tuple[object, ...],
    other_params: tuple[object, ...],
    own_id: uuid.UUID,
    other_id: uuid.UUID,
) -> None:
    conn.execute(insert_sql, own_params)
    row = conn.execute(
        sql.SQL("select count(*) from public.{table} where {pk} = %s;").format(
            table=sql.Identifier(table),
            pk=sql.Identifier(pk_column),
        ),
        (own_id,),
    ).fetchone()
    assert row is not None
    assert row[0] == 1

    with pytest.raises(psycopg.Error) as exc:
        conn.execute(insert_sql, other_params)
    assert exc.value.sqlstate == "42501"

    delete_count = conn.execute(
        sql.SQL("delete from public.{table} where {pk} = %s;").format(
            table=sql.Identifier(table),
            pk=sql.Identifier(pk_column),
        ),
        (own_id,),
    ).rowcount
    assert delete_count == 1

    blocked_delete = conn.execute(
        sql.SQL("delete from public.{table} where {pk} = %s;").format(
            table=sql.Identifier(table),
            pk=sql.Identifier(pk_column),
        ),
        (other_id,),
    ).rowcount
    assert blocked_delete == 0


@pytest.fixture(scope="session")
def db_url() -> str:
    return _get_db_url()


@pytest.fixture(scope="session")
def seed_data(db_url: str) -> Iterator[dict[str, uuid.UUID]]:
    user_1 = uuid.uuid4()
    user_2 = uuid.uuid4()
    now = dt.datetime.now(tz=dt.UTC)

    author_1 = uuid.uuid4()
    author_2 = uuid.uuid4()
    work_1 = uuid.uuid4()
    work_2 = uuid.uuid4()
    edition_1 = uuid.uuid4()
    external_id_1 = uuid.uuid4()
    source_record_1 = uuid.uuid4()

    library_item_1 = uuid.uuid4()
    library_item_2 = uuid.uuid4()
    reading_session_1 = uuid.uuid4()
    reading_session_2 = uuid.uuid4()
    reading_state_event_1 = uuid.uuid4()
    reading_state_event_2 = uuid.uuid4()
    note_1 = uuid.uuid4()
    note_2 = uuid.uuid4()
    highlight_1 = uuid.uuid4()
    highlight_2 = uuid.uuid4()
    review_1 = uuid.uuid4()
    review_2 = uuid.uuid4()
    api_client_1 = uuid.uuid4()
    api_client_2 = uuid.uuid4()
    api_audit_log_1 = uuid.uuid4()
    api_audit_log_2 = uuid.uuid4()

    with psycopg.connect(db_url, autocommit=True) as conn:
        conn.execute("set role postgres;")
        _insert_auth_user(conn, user_1, "user1@example.com")
        _insert_auth_user(conn, user_2, "user2@example.com")

        conn.execute(
            """
            insert into public.users (id, handle, display_name)
            values (%s, %s, %s), (%s, %s, %s);
            """,
            (
                user_1,
                f"user_{user_1.hex[:8]}",
                "User One",
                user_2,
                f"user_{user_2.hex[:8]}",
                "User Two",
            ),
        )

        conn.execute(
            "insert into public.authors (id, name) values (%s, %s), (%s, %s);",
            (author_1, "Author One", author_2, "Author Two"),
        )
        conn.execute(
            "insert into public.works (id, title) values (%s, %s), (%s, %s);",
            (work_1, "Work One", work_2, "Work Two"),
        )
        conn.execute(
            "insert into public.editions (id, work_id, isbn10) values (%s, %s, %s);",
            (edition_1, work_1, "1234567890"),
        )
        conn.execute(
            "insert into public.work_authors (work_id, author_id) values (%s, %s);",
            (work_1, author_1),
        )
        conn.execute(
            """
            insert into public.external_ids
                (id, entity_type, entity_id, provider, provider_id)
            values (%s, %s, %s, %s, %s);
            """,
            (external_id_1, "work", work_1, "openlibrary", "OL123"),
        )
        conn.execute(
            """
            insert into public.source_records
                (id, provider, entity_type, provider_id, raw, fetched_at)
            values (%s, %s, %s, %s, %s, %s);
            """,
            (
                source_record_1,
                "openlibrary",
                "work",
                "OL123",
                Json({"title": "Work One"}),
                now,
            ),
        )

        conn.execute(
            """
            insert into public.library_items
                (id, user_id, work_id, status, visibility)
            values (%s, %s, %s, %s, %s), (%s, %s, %s, %s, %s);
            """,
            (
                library_item_1,
                user_1,
                work_1,
                "to_read",
                "private",
                library_item_2,
                user_2,
                work_2,
                "reading",
                "private",
            ),
        )
        conn.execute(
            """
            insert into public.reading_sessions
                (id, user_id, library_item_id, started_at)
            values (%s, %s, %s, %s), (%s, %s, %s, %s);
            """,
            (
                reading_session_1,
                user_1,
                library_item_1,
                now,
                reading_session_2,
                user_2,
                library_item_2,
                now,
            ),
        )
        conn.execute(
            """
            insert into public.reading_state_events
                (id, user_id, library_item_id, event_type, occurred_at)
            values (%s, %s, %s, %s, %s), (%s, %s, %s, %s, %s);
            """,
            (
                reading_state_event_1,
                user_1,
                library_item_1,
                "started",
                now,
                reading_state_event_2,
                user_2,
                library_item_2,
                "started",
                now,
            ),
        )
        conn.execute(
            """
            insert into public.notes
                (id, user_id, library_item_id, title, body)
            values (%s, %s, %s, %s, %s), (%s, %s, %s, %s, %s);
            """,
            (
                note_1,
                user_1,
                library_item_1,
                "Note One",
                "Note body one",
                note_2,
                user_2,
                library_item_2,
                "Note Two",
                "Note body two",
            ),
        )
        conn.execute(
            """
            insert into public.highlights
                (id, user_id, library_item_id, quote)
            values (%s, %s, %s, %s), (%s, %s, %s, %s);
            """,
            (
                highlight_1,
                user_1,
                library_item_1,
                "Highlight one",
                highlight_2,
                user_2,
                library_item_2,
                "Highlight two",
            ),
        )
        conn.execute(
            """
            insert into public.reviews
                (id, user_id, library_item_id, title, body, rating)
            values (%s, %s, %s, %s, %s, %s), (%s, %s, %s, %s, %s, %s);
            """,
            (
                review_1,
                user_1,
                library_item_1,
                "Review One",
                "Review body one",
                7,
                review_2,
                user_2,
                library_item_2,
                "Review Two",
                "Review body two",
                8,
            ),
        )
        conn.execute(
            """
            insert into public.api_clients
                (client_id, name, owner_user_id)
            values (%s, %s, %s), (%s, %s, %s);
            """,
            (
                api_client_1,
                "Client One",
                user_1,
                api_client_2,
                "Client Two",
                user_2,
            ),
        )
        conn.execute(
            """
            insert into public.api_audit_logs
                (id, client_id, user_id, method, path, status, latency_ms, ip, occurred_at)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s),
                   (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                api_audit_log_1,
                api_client_1,
                user_1,
                "GET",
                "/v1/books",
                200,
                12,
                "127.0.0.1",
                now,
                api_audit_log_2,
                api_client_2,
                user_2,
                "POST",
                "/v1/books",
                201,
                18,
                "127.0.0.1",
                now,
            ),
        )

    data: dict[str, uuid.UUID] = {
        "user_1": user_1,
        "user_2": user_2,
        "author_1": author_1,
        "author_2": author_2,
        "work_1": work_1,
        "work_2": work_2,
        "edition_1": edition_1,
        "external_id_1": external_id_1,
        "source_record_1": source_record_1,
        "library_item_1": library_item_1,
        "library_item_2": library_item_2,
        "reading_session_1": reading_session_1,
        "reading_session_2": reading_session_2,
        "reading_state_event_1": reading_state_event_1,
        "reading_state_event_2": reading_state_event_2,
        "note_1": note_1,
        "note_2": note_2,
        "highlight_1": highlight_1,
        "highlight_2": highlight_2,
        "review_1": review_1,
        "review_2": review_2,
        "api_client_1": api_client_1,
        "api_client_2": api_client_2,
        "api_audit_log_1": api_audit_log_1,
        "api_audit_log_2": api_audit_log_2,
    }

    try:
        yield data
    finally:
        with psycopg.connect(db_url, autocommit=True) as conn:
            conn.execute("set role postgres;")
            conn.execute(
                "delete from public.api_audit_logs where id in (%s, %s);",
                (api_audit_log_1, api_audit_log_2),
            )
            conn.execute(
                "delete from public.api_clients where client_id in (%s, %s);",
                (api_client_1, api_client_2),
            )
            conn.execute(
                "delete from public.reviews where id in (%s, %s);",
                (review_1, review_2),
            )
            conn.execute(
                "delete from public.highlights where id in (%s, %s);",
                (highlight_1, highlight_2),
            )
            conn.execute(
                "delete from public.notes where id in (%s, %s);",
                (note_1, note_2),
            )
            conn.execute(
                "delete from public.reading_state_events where id in (%s, %s);",
                (reading_state_event_1, reading_state_event_2),
            )
            conn.execute(
                "delete from public.reading_sessions where id in (%s, %s);",
                (reading_session_1, reading_session_2),
            )
            conn.execute(
                "delete from public.library_items where id in (%s, %s);",
                (library_item_1, library_item_2),
            )
            conn.execute(
                "delete from public.work_authors where work_id = %s and author_id = %s;",
                (work_1, author_1),
            )
            conn.execute(
                "delete from public.editions where id = %s;",
                (edition_1,),
            )
            conn.execute(
                "delete from public.works where id in (%s, %s);",
                (work_1, work_2),
            )
            conn.execute(
                "delete from public.authors where id in (%s, %s);",
                (author_1, author_2),
            )
            conn.execute(
                "delete from public.external_ids where id = %s;",
                (external_id_1,),
            )
            conn.execute(
                "delete from public.source_records where id = %s;",
                (source_record_1,),
            )
            conn.execute(
                "delete from public.users where id in (%s, %s);", (user_1, user_2)
            )
            conn.execute(
                "delete from auth.users where id in (%s, %s);", (user_1, user_2)
            )


def test_policies_present(db_url: str) -> None:
    table_list = list(USER_SCOPED_TABLES.keys()) + READ_ONLY_TABLES + ["api_audit_logs"]
    with psycopg.connect(db_url, autocommit=True) as conn:
        rls_rows = conn.execute(
            """
            select relname, relrowsecurity
            from pg_class
            join pg_namespace on pg_namespace.oid = pg_class.relnamespace
            where nspname = 'public' and relname = any(%s);
            """,
            (table_list,),
        ).fetchall()
        rls_map = {row[0]: row[1] for row in rls_rows}
        assert all(rls_map.get(table) for table in table_list)

        policy_rows = conn.execute(
            """
            select tablename, policyname, cmd, roles, qual, with_check
            from pg_policies
            where schemaname = 'public';
            """
        ).fetchall()
        policies = {(row[0], row[1]): row for row in policy_rows}

        for table, column in USER_SCOPED_TABLES.items():
            key = (table, f"{table}_owner")
            assert key in policies
            _, _, cmd, roles, qual, with_check = policies[key]
            assert cmd == "ALL"
            assert roles and "authenticated" in roles
            assert qual and f"{column} = auth.uid()" in qual
            assert with_check and f"{column} = auth.uid()" in with_check

        for table in READ_ONLY_TABLES:
            key = (table, f"{table}_read")
            assert key in policies
            _, _, cmd, roles, qual, with_check = policies[key]
            assert cmd == "SELECT"
            assert roles and "authenticated" in roles
            assert qual and "true" in qual.lower()
            assert with_check is None

        audit_key = ("api_audit_logs", "api_audit_logs_read")
        assert audit_key in policies
        _, _, cmd, roles, qual, with_check = policies[audit_key]
        assert cmd == "SELECT"
        assert roles and "authenticated" in roles
        assert qual and "api_clients.owner_user_id" in qual and "auth.uid()" in qual
        assert with_check is None


@pytest.mark.parametrize(
    ("table", "owner_column", "pk_column", "row_key"),
    [
        ("users", "id", "id", "user_2"),
        ("library_items", "user_id", "id", "library_item_2"),
        ("reading_sessions", "user_id", "id", "reading_session_2"),
        ("reading_state_events", "user_id", "id", "reading_state_event_2"),
        ("notes", "user_id", "id", "note_2"),
        ("highlights", "user_id", "id", "highlight_2"),
        ("reviews", "user_id", "id", "review_2"),
        ("api_clients", "owner_user_id", "client_id", "api_client_2"),
    ],
)
def test_user_scoped_reads_and_updates(
    db_url: str,
    seed_data: dict[str, uuid.UUID],
    table: str,
    owner_column: str,
    pk_column: str,
    row_key: str,
) -> None:
    user_1 = seed_data["user_1"]
    user_2 = seed_data["user_2"]
    other_id = seed_data[row_key]

    with _authenticated_conn(db_url, user_1) as conn:
        count_row = conn.execute(
            sql.SQL("select count(*) from public.{};").format(sql.Identifier(table))
        ).fetchone()
        assert count_row is not None
        count = count_row[0]
        assert count == 1

        other_row = conn.execute(
            sql.SQL("select count(*) from public.{table} where {pk} = %s;").format(
                table=sql.Identifier(table),
                pk=sql.Identifier(pk_column),
            ),
            (other_id,),
        ).fetchone()
        assert other_row is not None
        other_count = other_row[0]
        assert other_count == 0

        update_count = conn.execute(
            sql.SQL(
                "update public.{table} set {owner} = {owner} where {owner} = %s;"
            ).format(
                table=sql.Identifier(table),
                owner=sql.Identifier(owner_column),
            ),
            (user_1,),
        ).rowcount
        assert update_count == 1

        blocked_update = conn.execute(
            sql.SQL(
                "update public.{table} set {owner} = {owner} where {owner} = %s;"
            ).format(
                table=sql.Identifier(table),
                owner=sql.Identifier(owner_column),
            ),
            (user_2,),
        ).rowcount
        assert blocked_update == 0


def test_api_audit_logs_scoped_read(
    db_url: str, seed_data: dict[str, uuid.UUID]
) -> None:
    user_1 = seed_data["user_1"]
    client_2 = seed_data["api_client_2"]
    with _authenticated_conn(db_url, user_1) as conn:
        count_row = conn.execute(
            "select count(*) from public.api_audit_logs;"
        ).fetchone()
        assert count_row is not None
        count = count_row[0]
        assert count == 1

        other_row = conn.execute(
            "select count(*) from public.api_audit_logs where client_id = %s;",
            (client_2,),
        ).fetchone()
        assert other_row is not None
        other_count = other_row[0]
        assert other_count == 0


@pytest.mark.parametrize(
    ("table", "insert_sql", "params_key"),
    [
        (
            "authors",
            "insert into public.authors (id, name) values (%s, %s);",
            "authors",
        ),
        (
            "works",
            "insert into public.works (id, title) values (%s, %s);",
            "works",
        ),
        (
            "editions",
            "insert into public.editions (id, work_id, isbn10) values (%s, %s, %s);",
            "editions",
        ),
        (
            "work_authors",
            "insert into public.work_authors (work_id, author_id) values (%s, %s);",
            "work_authors",
        ),
        (
            "external_ids",
            """
            insert into public.external_ids
                (id, entity_type, entity_id, provider, provider_id)
            values (%s, %s, %s, %s, %s);
            """,
            "external_ids",
        ),
        (
            "source_records",
            """
            insert into public.source_records
                (id, provider, entity_type, provider_id, raw)
            values (%s, %s, %s, %s, %s);
            """,
            "source_records",
        ),
    ],
)
def test_read_only_tables_block_writes(
    db_url: str,
    seed_data: dict[str, uuid.UUID],
    table: str,
    insert_sql: str,
    params_key: str,
) -> None:
    user_1 = seed_data["user_1"]
    params: dict[str, tuple[object, ...]] = {
        "authors": (uuid.uuid4(), "New Author"),
        "works": (uuid.uuid4(), "New Work"),
        "editions": (uuid.uuid4(), seed_data["work_2"], "0987654321"),
        "work_authors": (seed_data["work_2"], seed_data["author_2"]),
        "external_ids": (
            uuid.uuid4(),
            "work",
            seed_data["work_2"],
            "openlibrary",
            f"OL{uuid.uuid4().hex[:8]}",
        ),
        "source_records": (
            uuid.uuid4(),
            "openlibrary",
            "work",
            f"OL{uuid.uuid4().hex[:8]}",
            Json({"title": "New Work"}),
        ),
    }

    with _authenticated_conn(db_url, user_1) as conn:
        with pytest.raises(psycopg.Error) as exc:
            conn.execute(insert_sql, params[params_key])
        assert exc.value.sqlstate == "42501"


@pytest.mark.parametrize("table", READ_ONLY_TABLES)
def test_read_only_tables_allow_reads(
    db_url: str, seed_data: dict[str, uuid.UUID], table: str
) -> None:
    user_1 = seed_data["user_1"]
    with _authenticated_conn(db_url, user_1) as conn:
        row = conn.execute(
            sql.SQL("select count(*) from public.{};").format(sql.Identifier(table))
        ).fetchone()
        assert row is not None
        assert row[0] >= 1


def test_user_scoped_inserts_and_deletes(
    db_url: str, seed_data: dict[str, uuid.UUID]
) -> None:
    user_1 = seed_data["user_1"]
    user_2 = seed_data["user_2"]
    now = dt.datetime.now(tz=dt.UTC)

    with _authenticated_conn(db_url, user_1) as conn:
        library_item_id = uuid.uuid4()
        _assert_insert_and_delete(
            conn,
            table="library_items",
            pk_column="id",
            insert_sql="""
                insert into public.library_items
                    (id, user_id, work_id, status, visibility)
                values (%s, %s, %s, %s, %s);
            """,
            own_params=(
                library_item_id,
                user_1,
                seed_data["work_2"],
                "to_read",
                "private",
            ),
            other_params=(
                uuid.uuid4(),
                user_2,
                seed_data["work_1"],
                "reading",
                "private",
            ),
            own_id=library_item_id,
            other_id=seed_data["library_item_2"],
        )

        reading_session_id = uuid.uuid4()
        _assert_insert_and_delete(
            conn,
            table="reading_sessions",
            pk_column="id",
            insert_sql="""
                insert into public.reading_sessions
                    (id, user_id, library_item_id, started_at)
                values (%s, %s, %s, %s);
            """,
            own_params=(
                reading_session_id,
                user_1,
                seed_data["library_item_1"],
                now,
            ),
            other_params=(
                uuid.uuid4(),
                user_2,
                seed_data["library_item_2"],
                now,
            ),
            own_id=reading_session_id,
            other_id=seed_data["reading_session_2"],
        )

        reading_state_event_id = uuid.uuid4()
        _assert_insert_and_delete(
            conn,
            table="reading_state_events",
            pk_column="id",
            insert_sql="""
                insert into public.reading_state_events
                    (id, user_id, library_item_id, event_type, occurred_at)
                values (%s, %s, %s, %s, %s);
            """,
            own_params=(
                reading_state_event_id,
                user_1,
                seed_data["library_item_1"],
                "paused",
                now,
            ),
            other_params=(
                uuid.uuid4(),
                user_2,
                seed_data["library_item_2"],
                "paused",
                now,
            ),
            own_id=reading_state_event_id,
            other_id=seed_data["reading_state_event_2"],
        )

        note_id = uuid.uuid4()
        _assert_insert_and_delete(
            conn,
            table="notes",
            pk_column="id",
            insert_sql="""
                insert into public.notes
                    (id, user_id, library_item_id, title, body)
                values (%s, %s, %s, %s, %s);
            """,
            own_params=(
                note_id,
                user_1,
                seed_data["library_item_1"],
                "Temp note",
                "Temp body",
            ),
            other_params=(
                uuid.uuid4(),
                user_2,
                seed_data["library_item_2"],
                "Other note",
                "Other body",
            ),
            own_id=note_id,
            other_id=seed_data["note_2"],
        )

        highlight_id = uuid.uuid4()
        _assert_insert_and_delete(
            conn,
            table="highlights",
            pk_column="id",
            insert_sql="""
                insert into public.highlights
                    (id, user_id, library_item_id, quote)
                values (%s, %s, %s, %s);
            """,
            own_params=(
                highlight_id,
                user_1,
                seed_data["library_item_1"],
                "Temporary highlight",
            ),
            other_params=(
                uuid.uuid4(),
                user_2,
                seed_data["library_item_2"],
                "Other highlight",
            ),
            own_id=highlight_id,
            other_id=seed_data["highlight_2"],
        )

        review_item_id = uuid.uuid4()
        conn.execute(
            """
            insert into public.library_items
                (id, user_id, work_id, status, visibility)
            values (%s, %s, %s, %s, %s);
            """,
            (
                review_item_id,
                user_1,
                seed_data["work_2"],
                "to_read",
                "private",
            ),
        )
        review_id = uuid.uuid4()
        _assert_insert_and_delete(
            conn,
            table="reviews",
            pk_column="id",
            insert_sql="""
                insert into public.reviews
                    (id, user_id, library_item_id, title, body, rating)
                values (%s, %s, %s, %s, %s, %s);
            """,
            own_params=(
                review_id,
                user_1,
                review_item_id,
                "Temp review",
                "Temp body",
                6,
            ),
            other_params=(
                uuid.uuid4(),
                user_2,
                seed_data["library_item_1"],
                "Other review",
                "Other body",
                7,
            ),
            own_id=review_id,
            other_id=seed_data["review_2"],
        )
        conn.execute(
            "delete from public.library_items where id = %s;", (review_item_id,)
        )

        api_client_id = uuid.uuid4()
        _assert_insert_and_delete(
            conn,
            table="api_clients",
            pk_column="client_id",
            insert_sql="""
                insert into public.api_clients
                    (client_id, name, owner_user_id)
                values (%s, %s, %s);
            """,
            own_params=(
                api_client_id,
                "Temp Client",
                user_1,
            ),
            other_params=(
                uuid.uuid4(),
                "Other Client",
                user_2,
            ),
            own_id=api_client_id,
            other_id=seed_data["api_client_2"],
        )


def test_users_insert_enforces_owner(db_url: str) -> None:
    user_id = uuid.uuid4()
    with psycopg.connect(db_url, autocommit=True) as conn:
        conn.execute("set role postgres;")
        _insert_auth_user(conn, user_id, "user3@example.com")

    with _authenticated_conn(db_url, user_id) as conn:
        handle = f"user_{user_id.hex[:8]}"
        conn.execute(
            "insert into public.users (id, handle, display_name) values (%s, %s, %s);",
            (user_id, handle, "User Three"),
        )
        row = conn.execute(
            "select count(*) from public.users where id = %s;", (user_id,)
        ).fetchone()
        assert row is not None
        assert row[0] == 1

        with pytest.raises(psycopg.Error) as exc:
            conn.execute(
                "insert into public.users (id, handle) values (%s, %s);",
                (uuid.uuid4(), "user_blocked"),
            )
        assert exc.value.sqlstate == "42501"

        delete_count = conn.execute(
            "delete from public.users where id = %s;", (user_id,)
        ).rowcount
        assert delete_count == 1

    with psycopg.connect(db_url, autocommit=True) as conn:
        conn.execute("set role postgres;")
        conn.execute("delete from auth.users where id = %s;", (user_id,))


def test_api_audit_logs_block_writes(
    db_url: str, seed_data: dict[str, uuid.UUID]
) -> None:
    user_1 = seed_data["user_1"]
    with _authenticated_conn(db_url, user_1) as conn:
        with pytest.raises(psycopg.Error) as exc:
            conn.execute(
                """
                insert into public.api_audit_logs
                    (id, client_id, user_id, method, path, status, latency_ms, ip)
                values (%s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    uuid.uuid4(),
                    seed_data["api_client_1"],
                    user_1,
                    "GET",
                    "/v1/books",
                    200,
                    10,
                    "127.0.0.1",
                ),
            )
        assert exc.value.sqlstate == "42501"


def test_service_role_bypass(db_url: str, seed_data: dict[str, uuid.UUID]) -> None:
    with psycopg.connect(db_url, autocommit=True) as conn:
        conn.execute("set role service_role;")
        count_row = conn.execute(
            "select count(*) from public.library_items;"
        ).fetchone()
        assert count_row is not None
        count = count_row[0]
        assert count >= 2
