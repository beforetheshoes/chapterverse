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
running `pnpm dev` here. If you used `make supabase-env`, copy or symlink the repo root `.env` into
`apps/web/.env` or export the variables in your shell.

```
NUXT_PUBLIC_SUPABASE_URL=
NUXT_PUBLIC_SUPABASE_ANON_KEY=
```

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
