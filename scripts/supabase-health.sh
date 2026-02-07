#!/usr/bin/env bash
set -euo pipefail

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required but not installed." >&2
  exit 1
fi

# Load local env if present (no-op if missing).
if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  . ".env"
  set +a
fi

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required env var: ${name}" >&2
    exit 1
  fi
}

if [[ -z "${SUPABASE_URL:-}" && -n "${API_URL:-}" ]]; then
  SUPABASE_URL="${API_URL}"
fi

if [[ -z "${SUPABASE_ANON_KEY:-}" && -n "${ANON_KEY:-}" ]]; then
  SUPABASE_ANON_KEY="${ANON_KEY}"
fi

require_env SUPABASE_URL
require_env SUPABASE_ANON_KEY

base_url="${SUPABASE_URL%/}"
health_url="${base_url}/auth/v1/health"

curl -sf "${health_url}" >/dev/null

echo "Supabase auth health check passed: ${health_url}"
