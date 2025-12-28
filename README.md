# Chapterverse

Monorepo for Chapterverse services.

## Structure

- `apps/api` - FastAPI backend
- `apps/web` - Nuxt frontend
- `supabase` - Local Supabase config
- `docs` - Project documentation

## Requirements

- Docker (for local Supabase)
- Supabase CLI
- `uv` (Python tooling)
- `pnpm` (frontend tooling)

## Setup

```bash
make install
make supabase-env
```

## Development

```bash
make dev
```

This starts:
- API on `http://localhost:8000`
- Web on `http://localhost:3000`

All-in-one setup (install deps, generate Supabase env, link web `.env`, start dev servers):

```bash
make dev-up
```

Health check:

```bash
make supabase-health
```

## Environments

Local development uses a local Supabase instance (`supabase start`). Staging and production use hosted Supabase projects with environment variables set in those environments. See `docs/supabase.md` for how local vs hosted are handled and when to use `supabase link`.

## Docs

- `docs/supabase.md` - Supabase environments and local setup
