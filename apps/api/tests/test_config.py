import os
from pathlib import Path

import pytest

import app.core.config as config_module


def test_get_settings_blank_audience_and_reset_cache() -> None:
    original_env = os.environ.copy()
    try:
        os.environ["SUPABASE_URL"] = "https://example.supabase.co/"
        os.environ["SUPABASE_JWT_AUDIENCE"] = ""
        os.environ["SUPABASE_JWT_SECRET"] = "local-secret"
        os.environ["SUPABASE_JWKS_CACHE_TTL_SECONDS"] = "120"
        os.environ["API_VERSION"] = "9.9.9"
        config_module.reset_settings_cache()

        settings = config_module.get_settings()
        assert settings.supabase_url == "https://example.supabase.co"
        assert settings.supabase_jwt_audience is None
        assert settings.supabase_jwt_secret == "local-secret"
        assert settings.supabase_jwks_cache_ttl_seconds == 120
        assert settings.cors_allowed_origins == (
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
            "https://staging.theseedbed.app",
            "https://theseedbed.app",
            "https://www.theseedbed.app",
        )
        assert settings.api_version == "9.9.9"
    finally:
        os.environ.clear()
        os.environ.update(original_env)
        config_module.reset_settings_cache()


def test_get_settings_invalid_ttl_defaults() -> None:
    original_env = os.environ.copy()
    try:
        os.environ["SUPABASE_URL"] = "https://example.supabase.co/"
        os.environ["SUPABASE_JWKS_CACHE_TTL_SECONDS"] = "not-a-number"
        config_module.reset_settings_cache()

        settings = config_module.get_settings()
        assert settings.supabase_jwks_cache_ttl_seconds == 300
    finally:
        os.environ.clear()
        os.environ.update(original_env)
        config_module.reset_settings_cache()


def test_get_settings_custom_cors_origins() -> None:
    original_env = os.environ.copy()
    try:
        os.environ["SUPABASE_URL"] = "https://example.supabase.co/"
        os.environ["CORS_ALLOW_ORIGINS"] = (
            "https://app.example.com, https://admin.example.com "
        )
        config_module.reset_settings_cache()

        settings = config_module.get_settings()
        assert settings.cors_allowed_origins == (
            "https://app.example.com",
            "https://admin.example.com",
        )
    finally:
        os.environ.clear()
        os.environ.update(original_env)
        config_module.reset_settings_cache()


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
        config_module.reset_settings_cache()
        settings = config_module.get_settings()
        assert settings.supabase_url == "https://env.example"
        assert settings.supabase_jwt_audience == "authenticated"
        assert settings.supabase_jwt_secret == "from-dotenv"
        assert settings.supabase_jwks_cache_ttl_seconds == 90
        assert settings.api_version == "1.2.3"
    finally:
        os.chdir(original_cwd)
        os.environ.clear()
        os.environ.update(original_env)
        config_module.reset_settings_cache()


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
        config_module.reset_settings_cache()
        config_module._load_dotenv()
        config_module._load_dotenv()
        assert os.environ.get("SUPABASE_URL") == "https://env.example"
    finally:
        os.chdir(original_cwd)
        os.environ.clear()
        os.environ.update(original_env)
        config_module.reset_settings_cache()


def test_get_settings_blank_jwt_secret() -> None:
    original_env = os.environ.copy()
    try:
        os.environ["SUPABASE_URL"] = "https://example.supabase.co/"
        os.environ["SUPABASE_JWT_SECRET"] = "   "
        os.environ["SUPABASE_JWT_AUDIENCE"] = "authenticated"
        config_module.reset_settings_cache()

        settings = config_module.get_settings()
        assert settings.supabase_jwt_secret is None
    finally:
        os.environ.clear()
        os.environ.update(original_env)
        config_module.reset_settings_cache()


def test_find_repo_root_prefers_pyproject_when_git_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_exists = Path.exists

    def fake_exists(self: Path) -> bool:
        if self.name == ".git":
            return False
        return original_exists(self)

    monkeypatch.setattr(Path, "exists", fake_exists)
    repo_root = config_module._find_repo_root()
    assert (repo_root / "pyproject.toml").exists()


def test_find_repo_root_fallback_when_no_markers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_exists = Path.exists
    blocked = {".git", "pyproject.toml", "setup.cfg"}

    def fake_exists(self: Path) -> bool:
        if self.name in blocked:
            return False
        return original_exists(self)

    monkeypatch.setattr(Path, "exists", fake_exists)
    start_dir = Path(config_module.__file__).resolve().parent
    parents = start_dir.parents
    expected = start_dir if not parents else parents[min(4, len(parents) - 1)]
    assert config_module._find_repo_root() == expected
