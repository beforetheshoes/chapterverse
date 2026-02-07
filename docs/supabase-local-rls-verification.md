# Local Supabase RLS Verification

Use this when you want to confirm RLS policies are created locally in Supabase
Studio and via SQL.

## Start local Supabase and apply migrations

From the repo root:

```bash
make supabase-start
make supabase-env
cd apps/api && uv run alembic upgrade head
```

If you are in `apps/api`, you can call the root Makefile directly:

```bash
make -f ../../Makefile supabase-start
make -f ../../Makefile supabase-env
```

## Verify in Supabase Studio

Open: `http://localhost:54323`

Then:
- Go to `Database` -> `Table editor`
- Select a table, e.g. `notes`
- Confirm RLS is enabled and policies exist for
  SELECT/INSERT/UPDATE/DELETE with `user_id = auth.uid()`

## Verify in SQL editor

Run:

```sql
select schemaname,
       tablename,
       policyname,
       cmd,
       permissive,
       roles,
       qual,
       with_check
from pg_policies
where schemaname = 'public'
  and tablename in (
    'users',
    'library_items',
    'reading_sessions',
    'reading_state_events',
    'notes',
    'highlights',
    'reviews',
    'api_clients',
    'api_audit_logs',
    'authors',
    'works',
    'editions',
    'work_authors',
    'external_ids',
    'source_records'
  )
order by tablename, policyname;
```
