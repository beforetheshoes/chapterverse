"""Enable RLS policies for user-owned and shared tables.

Revision ID: 0007_rls_policies
Revises: 0006_platform_tables
Create Date: 2025-01-05 00:00:00
"""

from __future__ import annotations

from alembic import op

revision = "0007_rls_policies"
down_revision = "0006_platform_tables"
branch_labels = None
depends_on = None


USER_OWNED_TABLES = {
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


def _enable_rls(table: str) -> None:
    op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;")


def _disable_rls(table: str) -> None:
    op.execute(f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY;")


def _create_owner_policy(table: str, column: str) -> None:
    policy_name = f"{table}_owner"
    op.execute(
        f"""
        CREATE POLICY {policy_name}
        ON public.{table}
        FOR ALL
        TO authenticated
        USING ({column} = auth.uid())
        WITH CHECK ({column} = auth.uid());
        """
    )


def _drop_policy(table: str, policy_name: str) -> None:
    op.execute(f"DROP POLICY IF EXISTS {policy_name} ON public.{table};")


def _create_read_only_policy(table: str) -> None:
    policy_name = f"{table}_read"
    op.execute(
        f"""
        CREATE POLICY {policy_name}
        ON public.{table}
        FOR SELECT
        TO authenticated
        USING (true);
        """
    )


def upgrade() -> None:
    for table, column in USER_OWNED_TABLES.items():
        _enable_rls(table)
        _create_owner_policy(table, column)

    _enable_rls("api_audit_logs")
    op.execute(
        """
        CREATE POLICY api_audit_logs_read
        ON public.api_audit_logs
        FOR SELECT
        TO authenticated
        USING (
            EXISTS (
                SELECT 1
                FROM public.api_clients
                WHERE api_clients.client_id = api_audit_logs.client_id
                  AND api_clients.owner_user_id = auth.uid()
            )
        );
        """
    )

    for table in READ_ONLY_TABLES:
        _enable_rls(table)
        _create_read_only_policy(table)


def downgrade() -> None:
    for table in READ_ONLY_TABLES:
        _drop_policy(table, f"{table}_read")
        _disable_rls(table)

    _drop_policy("api_audit_logs", "api_audit_logs_read")
    _disable_rls("api_audit_logs")

    for table in USER_OWNED_TABLES:
        _drop_policy(table, f"{table}_owner")
        _disable_rls(table)
