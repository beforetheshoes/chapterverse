import os
from pathlib import Path

import pytest

from app.core.config import reset_settings_cache
from app.db.base import Base
from app.db.config import get_database_url


def _restore_env(original_env: dict[str, str]) -> None:
    os.environ.clear()
    os.environ.update(original_env)
    reset_settings_cache()


def test_base_metadata_is_available() -> None:
    assert Base.metadata is not None


def test_get_database_url_default_env(tmp_path: Path) -> None:
    original_env = os.environ.copy()
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        os.environ["APP_CONFIG_DIR"] = str(tmp_path)
        os.environ["SUPABASE_DB_URL"] = "postgresql://local/db"
        os.environ.pop("SUPABASE_ENV", None)
        reset_settings_cache()
        assert get_database_url() == "postgresql+psycopg://local/db"
    finally:
        os.chdir(original_cwd)
        _restore_env(original_env)


def test_get_database_url_local_label() -> None:
    original_env = os.environ.copy()
    try:
        os.environ["SUPABASE_DB_URL"] = "postgresql://local/db"
        os.environ["SUPABASE_ENV"] = "local"
        reset_settings_cache()
        assert get_database_url() == "postgresql+psycopg://local/db"
    finally:
        _restore_env(original_env)


def test_get_database_url_blank_label() -> None:
    original_env = os.environ.copy()
    try:
        os.environ["SUPABASE_DB_URL"] = "postgresql://local/db"
        os.environ["SUPABASE_ENV"] = "   "
        reset_settings_cache()
        assert get_database_url() == "postgresql+psycopg://local/db"
    finally:
        _restore_env(original_env)


def test_get_database_url_preserves_driver_scheme() -> None:
    original_env = os.environ.copy()
    try:
        os.environ["SUPABASE_DB_URL"] = "postgresql+psycopg://local/db"
        os.environ["SUPABASE_ENV"] = ""
        reset_settings_cache()
        assert get_database_url() == "postgresql+psycopg://local/db"
    finally:
        _restore_env(original_env)


def test_get_database_url_staging_label() -> None:
    original_env = os.environ.copy()
    try:
        os.environ["SUPABASE_DB_URL_STAGING"] = "postgresql://staging/db"
        os.environ["SUPABASE_ENV"] = "staging"
        reset_settings_cache()
        assert get_database_url() == "postgresql+psycopg://staging/db"
    finally:
        _restore_env(original_env)


def test_get_database_url_prod_label() -> None:
    original_env = os.environ.copy()
    try:
        os.environ["SUPABASE_DB_URL_PROD"] = "postgresql://prod/db"
        os.environ["SUPABASE_ENV"] = "production"
        reset_settings_cache()
        assert get_database_url() == "postgresql+psycopg://prod/db"
    finally:
        _restore_env(original_env)


def test_get_database_url_missing_default() -> None:
    original_env = os.environ.copy()
    try:
        os.environ["SUPABASE_DB_URL"] = ""
        os.environ["SUPABASE_ENV"] = ""
        reset_settings_cache()
        with pytest.raises(RuntimeError, match="SUPABASE_DB_URL is not configured"):
            get_database_url()
    finally:
        _restore_env(original_env)


def test_get_database_url_missing_env_specific() -> None:
    original_env = os.environ.copy()
    try:
        os.environ["SUPABASE_ENV"] = "staging"
        os.environ["SUPABASE_DB_URL_STAGING"] = ""
        reset_settings_cache()
        with pytest.raises(RuntimeError, match="SUPABASE_DB_URL_STAGING"):
            get_database_url()
    finally:
        _restore_env(original_env)


def test_get_database_url_unsupported_env() -> None:
    original_env = os.environ.copy()
    try:
        os.environ["SUPABASE_ENV"] = "qa"
        os.environ["SUPABASE_DB_URL"] = "postgresql://local/db"
        reset_settings_cache()
        with pytest.raises(RuntimeError, match="Unsupported SUPABASE_ENV"):
            get_database_url()
    finally:
        _restore_env(original_env)


def test_get_database_url_loads_dotenv(tmp_path: Path) -> None:
    original_env = os.environ.copy()
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        (tmp_path / ".env").write_text(
            "SUPABASE_DB_URL=postgresql://env/db\n",
            encoding="utf-8",
        )
        os.environ.pop("SUPABASE_DB_URL", None)
        os.environ["SUPABASE_ENV"] = ""
        reset_settings_cache()
        assert get_database_url() == "postgresql+psycopg://env/db"
    finally:
        os.chdir(original_cwd)
        _restore_env(original_env)
