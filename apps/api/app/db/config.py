from __future__ import annotations

import os
from urllib.parse import urlparse, urlunparse

from app.core.config import _load_dotenv

_DEFAULT_ENV_LABELS = {"local", "development", "dev"}
_STAGING_ENV_LABELS = {"staging", "stage"}
_PROD_ENV_LABELS = {"prod", "production"}


def _normalize_env(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if not normalized:
        return None
    return normalized


def _normalize_database_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme in {"postgresql", "postgres"}:
        parsed = parsed._replace(scheme="postgresql+psycopg")
        return urlunparse(parsed)
    return url


def _select_db_env_var(env_label: str | None) -> str:
    if env_label is None or env_label in _DEFAULT_ENV_LABELS:
        return "SUPABASE_DB_URL"
    if env_label in _STAGING_ENV_LABELS:
        return "SUPABASE_DB_URL_STAGING"
    if env_label in _PROD_ENV_LABELS:
        return "SUPABASE_DB_URL_PROD"
    raise RuntimeError(
        f"Unsupported SUPABASE_ENV value: {env_label!r}."
        " Expected one of: local, staging, prod."
    )


def get_database_url() -> str:
    _load_dotenv()
    env_label = _normalize_env(os.getenv("SUPABASE_ENV"))
    env_var = _select_db_env_var(env_label)
    url = os.getenv(env_var, "").strip()
    if url:
        return _normalize_database_url(url)
    if env_label is None or env_label in _DEFAULT_ENV_LABELS:
        raise RuntimeError("SUPABASE_DB_URL is not configured.")
    raise RuntimeError(f"{env_var} is not configured for SUPABASE_ENV={env_label!r}.")
