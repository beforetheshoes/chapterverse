from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_jwt_audience: str | None
    supabase_jwt_secret: str | None
    supabase_jwks_cache_ttl_seconds: int
    api_version: str


_dotenv_loaded = False


def _find_repo_root() -> Path:
    env_dir = os.getenv("APP_CONFIG_DIR")
    if env_dir:
        config_path = Path(env_dir).expanduser()
        if config_path.is_dir():
            return config_path

    start_dir = Path(__file__).resolve().parent
    for parent in (start_dir, *start_dir.parents):
        if (parent / ".git").exists():
            return parent

    markers = ("pyproject.toml", "setup.cfg")
    for parent in (start_dir, *start_dir.parents):
        for marker in markers:
            if (parent / marker).exists():
                return parent

    parents = start_dir.parents
    if not parents:
        return start_dir
    return parents[min(4, len(parents) - 1)]


def _load_dotenv() -> None:
    global _dotenv_loaded
    if _dotenv_loaded:
        return
    _dotenv_loaded = True

    repo_root = _find_repo_root()
    candidates = [Path.cwd() / ".env", repo_root / ".env"]

    for path in candidates:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            value = line.strip()
            if not value or value.startswith("#"):
                continue
            if value.startswith("export "):
                value = value[len("export ") :].strip()
            if "=" not in value:
                continue
            key, raw_value = value.split("=", 1)
            key = key.strip()
            raw_value = raw_value.strip()
            if (
                len(raw_value) >= 2
                and raw_value[0] == raw_value[-1]
                and raw_value[0] in {'"', "'"}
            ):
                raw_value = raw_value[1:-1]
            os.environ.setdefault(key, raw_value)
        break


def _normalize_supabase_url(value: str) -> str:
    return value.rstrip("/")


def _parse_ttl_seconds() -> int:
    default_ttl = 300
    raw_ttl = os.getenv("SUPABASE_JWKS_CACHE_TTL_SECONDS")
    if raw_ttl is None or not raw_ttl.strip():
        return default_ttl
    try:
        return int(raw_ttl)
    except ValueError:
        return default_ttl


@lru_cache
def get_settings() -> Settings:
    """Settings are cached; call reset_settings_cache when env values change."""
    _load_dotenv()
    supabase_url = _normalize_supabase_url(os.getenv("SUPABASE_URL", "").strip())
    audience: str | None = os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated").strip()
    if not audience:
        audience = None
    jwt_secret: str | None = os.getenv("SUPABASE_JWT_SECRET", "").strip()
    if not jwt_secret:
        jwt_secret = None
    ttl_seconds = _parse_ttl_seconds()
    api_version = os.getenv("API_VERSION", "0.1.0").strip()
    return Settings(
        supabase_url=supabase_url,
        supabase_jwt_audience=audience,
        supabase_jwt_secret=jwt_secret,
        supabase_jwks_cache_ttl_seconds=ttl_seconds,
        api_version=api_version,
    )


def reset_settings_cache() -> None:
    global _dotenv_loaded
    get_settings.cache_clear()
    _dotenv_loaded = False
