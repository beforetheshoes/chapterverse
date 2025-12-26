.PHONY: dev dev-api dev-web install install-api install-web \
	supabase-start supabase-env supabase-health \
	lint lint-api lint-web format format-api format-web \
	format-check format-check-api format-check-web \
	typecheck typecheck-api test test-api test-web test-unit test-e2e \
	build build-api build-web quality

# Run both API and web in development mode
dev:
	@echo "Starting API and web servers..."
	@make -j2 dev-api dev-web

# Run API server
dev-api:
	cd apps/api && uv run uvicorn main:app --reload --port 8000

# Run web server
dev-web:
	cd apps/web && pnpm dev

# Supabase local dev
supabase-start:
	supabase start

supabase-env: supabase-start
	@supabase status -o env | while IFS= read -r line; do \
		case "$$line" in \
			API_URL=*) \
				value="$${line#API_URL=}"; \
				echo "SUPABASE_URL=$$value"; \
				echo "NUXT_PUBLIC_SUPABASE_URL=$$value"; \
				;; \
			ANON_KEY=*) \
				value="$${line#ANON_KEY=}"; \
				echo "SUPABASE_ANON_KEY=$$value"; \
				echo "NUXT_PUBLIC_SUPABASE_ANON_KEY=$$value"; \
				;; \
			SERVICE_ROLE_KEY=*) \
				value="$${line#SERVICE_ROLE_KEY=}"; \
				echo "SUPABASE_SERVICE_ROLE_KEY=$$value"; \
				;; \
		esac; \
	done > .env
	@echo "Wrote .env from local Supabase status."

supabase-health:
	@scripts/supabase-health.sh

# Install all dependencies
install: install-api install-web

# Install API dependencies
install-api:
	cd apps/api && uv sync --extra dev

# Install web dependencies
install-web:
	cd apps/web && pnpm install

# Run all quality checks, tests, and builds
quality: format-check lint typecheck test build

# Linting
lint: lint-api lint-web

lint-api:
	cd apps/api && uv run ruff check .

lint-web:
	cd apps/web && pnpm lint

# Formatting
format: format-api format-web

format-api:
	cd apps/api && uv run black .

format-web:
	cd apps/web && pnpm format

format-check: format-check-api format-check-web

format-check-api:
	cd apps/api && uv run black --check .

format-check-web:
	cd apps/web && pnpm format:check

# Type checking
typecheck: typecheck-api

typecheck-api:
	cd apps/api && uv run mypy .

# Tests
test: test-api test-web

test-api:
	cd apps/api && uv run pytest

test-web: test-unit test-e2e

test-unit:
	cd apps/web && pnpm test:unit

test-e2e:
	cd apps/web && pnpm test:e2e

# Builds
build: build-api build-web

build-api:
	cd apps/api && uv run python -m build

build-web:
	cd apps/web && pnpm build
