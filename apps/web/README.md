# The Seedbed Web

Nuxt 4.2.2 frontend using PrimeVue v4 (Aura theme) and Tailwind CSS.

## Requirements

- Node 20
- pnpm 10

## Setup

From the repo root:

```bash
pnpm install
```

## Environment

The Supabase client reads the public runtime config values below. Nuxt loads `.env` from `apps/web` when
running `pnpm dev` here. If you start from repo root with `make dev` or `make dev-up`, the root `.env`
is automatically linked to `apps/web/.env`. If you run `pnpm dev` directly in `apps/web`, copy or symlink
the repo root `.env` into `apps/web/.env` (or export variables in your shell).

```
NUXT_PUBLIC_SUPABASE_URL=
NUXT_PUBLIC_SUPABASE_ANON_KEY=
NUXT_PUBLIC_API_BASE_URL=
```

`NUXT_PUBLIC_API_BASE_URL` defaults to `http://localhost:8000` if unset.

## Development

```bash
pnpm dev
```

## Tests

```bash
pnpm lint
pnpm test:unit
pnpm test:e2e
```

## Build

```bash
pnpm build
```
