"""
config.py
─────────
Database-specific settings, kept separate so each service can import
just the DB config without pulling in unrelated service settings.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """
    Database connection settings read from environment variables.

    Required:
        DATABASE_URL — full async connection string, e.g.:
            postgresql+asyncpg://postgres:password@localhost:5432/analytics_platform

    Optional:
        DATABASE_ECHO — set to true to log all SQL to stdout (dev only)
    """

    database_url: str = (
        "postgresql+asyncpg://postgres:password@localhost:5432/analytics_platform"
    )

    # Set to true to print all SQL statements (useful when debugging queries)
    database_echo: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Allow extra fields so services can share a single .env file
        # without this config class complaining about unknown keys
        extra="ignore",
    )


@lru_cache
def get_db_settings() -> DatabaseSettings:
    return DatabaseSettings()
