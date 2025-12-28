# The Seedbed API

## Migrations (Alembic)

Local development uses a local Supabase instance. Populate `.env` with
`SUPABASE_DB_URL` (run `make supabase-env` from the repo root).

For staging or production, set:
- `SUPABASE_ENV=staging` and `SUPABASE_DB_URL_STAGING`
- `SUPABASE_ENV=prod` and `SUPABASE_DB_URL_PROD`
Hosted URLs should be provided by hosting/CI (see Issue #44).

Common commands (run from `apps/api`):

```bash
uv run alembic revision --autogenerate -m "add new table"
uv run alembic upgrade head
```
