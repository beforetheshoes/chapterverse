.PHONY: dev dev-api dev-web install install-api install-web

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

# Install all dependencies
install: install-api install-web

# Install API dependencies
install-api:
	cd apps/api && uv sync

# Install web dependencies
install-web:
	cd apps/web && pnpm install
