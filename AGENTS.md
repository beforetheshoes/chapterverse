# AGENTS.md

Project instructions for Codex. These rules override any defaults.

## Working agreements (highest priority)
- Always create and work on a new branch for any change.
- NEVER commit or open a PR without explicit permission from the user.
- Always use the GitHub CLI to read issue descriptions before planning work on an issue.
- Always read current official documentation (Context7 when available) for any library, framework, or service you touch.
- Always run `make quality` and fix all failures before reporting a task as complete.
- Maintain high coverage gates; add useful tests/checks as needed and ensure `make quality` covers them.
- Use the Supabase CLI, Render CLI, and Vercel CLI for their respective services.
- NEVER expose secrets in code, configs, or logs.

## Repo context
- Monorepo layout: `apps/api` (FastAPI) and `apps/web` (Nuxt), `supabase` for local config, `docs` for project docs.
- Local dev uses Supabase CLI (`supabase start`, `make supabase-env`).
- Staging is the active deployment target unless told otherwise.
- There is no production auth UI yet; assume auth flows are dashboard/config driven for now unless a UI issue is explicitly assigned.
- Branch/deploy workflow (enforce staging-first):
  - Do day-to-day work via PRs targeting `development` (default branch).
  - `development` deploys to staging (`staging.theseedbed.app` + staging API).
  - Promote to prod by opening a release PR `development -> main` (prod is `theseedbed.app` + prod API).
  - Avoid direct merges to `main` except emergency hotfixes; if you do, immediately back-merge `main -> development`.

## Commands
- Quality gate: `make quality` (must pass before completion).
- API only: `make test-api`, `make lint-api`, `make format-check-api`, `make typecheck-api`, `make build-api`.
- Web only: `make test-web`, `make lint-web`, `make format-check-web`, `make build-web`.

## CLI usage reminders
- Supabase: use `supabase link --project-ref <ref>` + `supabase config push` for hosted config.
- Vercel: use `vercel link --cwd apps/web` and env vars via `vercel env add`.
- Render: create services in the UI once, then use CLI for deploys/logs.
