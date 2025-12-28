# CLI usage

Quick notes for the three CLIs we use in this repo.

## Supabase CLI

Local dev:

```bash
supabase start
supabase status -o env
make supabase-env
make supabase-health
```

Hosted projects (staging/prod):

```bash
supabase link --project-ref kypwcksvicrbrrwscdze
supabase config push

supabase link --project-ref aaohmjvcsgyqqlxomegu
supabase config push
```

Tips:
- `supabase link` is only for hosted projects, not local dev.
- You can avoid linking by using `--project-ref` on individual commands.

## Vercel CLI (web)

Link the Nuxt app:

```bash
vercel link --project theseedbed --yes --cwd apps/web
```

Set env vars (Preview = staging, Production = prod):

```bash
printf "%s" "https://kypwcksvicrbrrwscdze.supabase.co" | vercel env add NUXT_PUBLIC_SUPABASE_URL preview --cwd apps/web
printf "%s" "https://aaohmjvcsgyqqlxomegu.supabase.co" | vercel env add NUXT_PUBLIC_SUPABASE_URL production --cwd apps/web

printf "%s" "<staging-publishable-key>" | vercel env add NUXT_PUBLIC_SUPABASE_ANON_KEY preview --cwd apps/web
printf "%s" "<prod-publishable-key>" | vercel env add NUXT_PUBLIC_SUPABASE_ANON_KEY production --cwd apps/web
```

Deploy a preview build and alias staging:

```bash
vercel deploy --target=preview --yes
vercel alias set <preview-url> staging.theseedbed.app
```

## Render CLI (API)

The Render CLI can manage services and deploys, but it does not create new
services/projects yet. Create the API service once in the Render dashboard,
then use the CLI to deploy and inspect.

Service settings (API):
- Root directory: `apps/api`
- Build command: `pip install uv && uv sync --frozen --no-dev`
- Start command: `uv run uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/api/v1/health`
- Env vars (staging/prod): `SUPABASE_URL`, `SUPABASE_JWT_AUDIENCE=authenticated`

CLI examples:

```bash
render workspace current
render services --output text
render deploys create srv-d58pjpre5dus73e3ghl0 --wait
render deploys create srv-d58poa3e5dus73e3it8g --wait
render logs --resources srv-d58pjpre5dus73e3ghl0
render logs --resources srv-d58poa3e5dus73e3it8g
```
