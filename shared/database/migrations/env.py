"""
Alembic migration environment configuration.
─────────────────────────────────────────────
This file runs every time you call `alembic upgrade` or `alembic revision`.
It connects Alembic to your SQLAlchemy models so it can auto-detect
schema changes and generate migration scripts.

To use:
    cd shared/database
    cp .env.example .env            # add your DATABASE_URL
    alembic upgrade head            # apply all migrations
    alembic revision --autogenerate -m "describe your change"  # create new migration
"""

import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ── Make shared/ importable from here ─────────────────────────────────────────
# Alembic runs from shared/database/migrations/ so we need to add the
# project root to sys.path so `from shared.database...` imports work.
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# ── Import ALL models so Alembic can see them for autogenerate ─────────────────
from shared.database.base import Base  # noqa: E402
from shared.database.models import (  # noqa: E402, F401
    tenant,
    document,
    ml_model,
    chat_session,
    prediction_log,
)
from shared.database.config import get_db_settings  # noqa: E402

# ── Alembic config ─────────────────────────────────────────────────────────────
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Override sqlalchemy.url from settings (so we don't hardcode it in alembic.ini)
config.set_main_option("sqlalchemy.url", get_db_settings().database_url)


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generates SQL scripts)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using the async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
