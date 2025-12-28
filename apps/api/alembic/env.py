from __future__ import annotations

import importlib
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.db.base import Base
from app.db.config import get_database_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

importlib.import_module("app.db.models")

target_metadata = Base.metadata


def _configure_database_url() -> None:
    database_url = get_database_url()
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    _configure_database_url()
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    _configure_database_url()
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
