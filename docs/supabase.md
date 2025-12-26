# Supabase environments

## Projects

Staging
- Project name: chapterverse-staging
- Region: us-east-1
- Project ref: kypwcksvicrbrrwscdze

Production
- Project name: chapterverse-production
- Region: us-east-1
- Project ref: aaohmjvcsgyqqlxomegu

## Auth URLs (local dev for now)

- Site URL: http://localhost:3000
- Redirect URLs:
  - http://localhost:3000/**
  - http://127.0.0.1:3000/**

## Local development (no shared secrets)

Each developer runs a local Supabase instance and uses local keys. This avoids passing secrets around.

```bash
make supabase-env

# or manually:
supabase start
supabase status -o env

# then map:
# API_URL -> SUPABASE_URL / NUXT_PUBLIC_SUPABASE_URL
# ANON_KEY -> SUPABASE_ANON_KEY / NUXT_PUBLIC_SUPABASE_ANON_KEY
# SERVICE_ROLE_KEY -> SUPABASE_SERVICE_ROLE_KEY
```

Use the output to populate your local `.env` (not committed). The `service_role` key is server-only.

Local development is fully independent of hosting. You can build and run the app with local Supabase even if staging/production hosting is not set up yet.

## Quick health check

```bash
make supabase-health
```

## When to use `supabase link`

Think of `supabase link` as "point the CLI at a hosted project." It is **not** used for local dev.

**Mental model (5 lines)**
1) Local dev: `supabase start` runs everything on your machine.
2) Local keys: `supabase status` prints your local URL + keys.
3) Hosted envs: staging/prod live on Supabase servers.
4) `supabase link`: aim the CLI at a hosted project.
5) `supabase config/db push`: apply changes to that hosted project.

Use it when you want to change or inspect a hosted project:
- Push config changes (e.g., auth site URL/redirects)
- Push database migrations to staging/production
- Manage secrets, functions, or other hosted settings

Do not use it for local development:
- Local dev runs with `supabase start`
- Local URLs/keys come from `supabase status`

Tip: you can avoid a persistent link by passing `--project-ref` to a command, or run `supabase unlink` after you're done with a hosted project.

## Environment variables (shared policy)

We do not share staging/production secrets via files. Only public values (anon key + URL) should be used in frontend configs. Server secrets live in hosting/CI.

## CLI notes

After projects are created, link/push config:

```bash
supabase link --project-ref <staging-ref>
supabase config push

supabase link --project-ref <production-ref>
supabase config push
```

## Deployment

Hosting platform and env var wiring is pending (no domains yet).
