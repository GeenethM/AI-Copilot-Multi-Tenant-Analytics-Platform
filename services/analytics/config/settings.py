from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All configuration is read from environment variables (or a .env file).
    Copy .env.example to .env and fill in your values.
    """

    # ── Anomaly detection ─────────────────────────────────────────────────────
    # A data point is flagged as an anomaly if it falls more than
    # this many standard deviations from the column mean.
    # 2.0 = flag the outer ~5% of values  (more sensitive)
    # 3.0 = flag the outer ~0.3% of values (less sensitive, fewer false positives)
    anomaly_z_score_threshold: float = 2.5

    # ── Trend detection ───────────────────────────────────────────────────────
    # Number of periods used for rolling average calculations
    rolling_window: int = 3

    # ── Database ──────────────────────────────────────────────────────────────
    # Shared PostgreSQL connection string (multi-tenant layer)
    database_url: str = (
        "postgresql+asyncpg://postgres:password@localhost:5432/analytics_platform"
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
