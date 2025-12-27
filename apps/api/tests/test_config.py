import os
from pathlib import Path

from app.core.config import _load_dotenv, get_settings, reset_settings_cache


def test_get_settings_blank_audience_and_reset_cache() -> None:
    original_env = os.environ.copy()
    try:
        os.environ["SUPABASE_URL"] = "https://example.supabase.co/"
        os.environ["SUPABASE_JWT_AUDIENCE"] = ""
        os.environ["SUPABASE_JWT_SECRET"] = "local-secret"
        os.environ["SUPABASE_JWKS_CACHE_TTL_SECONDS"] = "120"
        os.environ["API_VERSION"] = "9.9.9"
        reset_settings_cache()

        settings = get_settings()
        assert settings.supabase_url == "https://example.supabase.co"
        assert settings.supabase_jwt_audience is None
        assert settings.supabase_jwt_secret == "local-secret"
        assert settings.supabase_jwks_cache_ttl_seconds == 120
        assert settings.api_version == "9.9.9"
    finally:
        os.environ.clear()
        os.environ.update(original_env)
        reset_settings_cache()


def test_get_settings_invalid_ttl_defaults() -> None:
    original_env = os.environ.copy()
    try:
        os.environ["SUPABASE_URL"] = "https://example.supabase.co/"
        os.environ["SUPABASE_JWKS_CACHE_TTL_SECONDS"] = "not-a-number"
        reset_settings_cache()

        settings = get_settings()
        assert settings.supabase_jwks_cache_ttl_seconds == 300
    finally:
        os.environ.clear()
        os.environ.update(original_env)
        reset_settings_cache()


def test_get_settings_loads_dotenv(tmp_path: Path) -> None:
    original_env = os.environ.copy()
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        env_path = tmp_path / ".env"
        env_path.write_text(
            "\n".join(
                [
                    "# comment",
                    "",
                    "export SUPABASE_URL=https://env.example",
                    "SUPABASE_JWT_AUDIENCE=authenticated",
                    'SUPABASE_JWT_SECRET="from-dotenv"',
                    "NOEQUALS",
                    "SUPABASE_JWKS_CACHE_TTL_SECONDS=90",
                    'API_VERSION="1.2.3"',
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        for key in [
            "SUPABASE_URL",
            "SUPABASE_JWT_AUDIENCE",
            "SUPABASE_JWT_SECRET",
            "SUPABASE_JWKS_CACHE_TTL_SECONDS",
            "API_VERSION",
        ]:
            os.environ.pop(key, None)
        reset_settings_cache()
        settings = get_settings()
        assert settings.supabase_url == "https://env.example"
        assert settings.supabase_jwt_audience == "authenticated"
        assert settings.supabase_jwt_secret == "from-dotenv"
        assert settings.supabase_jwks_cache_ttl_seconds == 90
        assert settings.api_version == "1.2.3"
    finally:
        os.chdir(original_cwd)
        os.environ.clear()
        os.environ.update(original_env)
        reset_settings_cache()


def test_load_dotenv_idempotent(tmp_path: Path) -> None:
    original_env = os.environ.copy()
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        (tmp_path / ".env").write_text(
            "SUPABASE_URL=https://env.example\n",
            encoding="utf-8",
        )
        os.environ.pop("SUPABASE_URL", None)
        reset_settings_cache()
        _load_dotenv()
        _load_dotenv()
        assert os.environ.get("SUPABASE_URL") == "https://env.example"
    finally:
        os.chdir(original_cwd)
        os.environ.clear()
        os.environ.update(original_env)
        reset_settings_cache()
