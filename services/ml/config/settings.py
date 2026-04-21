from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All configuration is read from environment variables (or a .env file).
    Copy .env.example to .env and fill in your values.
    """

    # ── Model storage ─────────────────────────────────────────────────────────
    # Directory where trained models are persisted per tenant.
    # Each tenant gets a subdirectory: models_directory/{tenant_id}/
    models_directory: str = "./saved_models"

    # ── Training defaults ─────────────────────────────────────────────────────
    # Which algorithm to use: random_forest | linear_regression | gradient_boosting
    # random_forest is the default — handles non-linear patterns and noisy data well.
    default_model_type: str = "random_forest"

    # Fraction of data held back for evaluating the trained model (0.2 = 20%)
    test_size: float = 0.2

    # Ensures reproducible train/test splits across runs
    random_state: int = 42

    # ── SHAP explainability ───────────────────────────────────────────────────
    # Max number of data rows used when computing SHAP values.
    # Lower = faster; higher = more accurate explanations.
    shap_background_samples: int = 100

    # ── Database ──────────────────────────────────────────────────────────────
    # Shared PostgreSQL connection string (multi-tenant layer)
    database_url: str = (
        "postgresql+asyncpg://postgres:password@localhost:5432/analytics_platform"
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def models_path(self) -> Path:
        path = Path(self.models_directory)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    """Returns a cached Settings instance. The cache means .env is only read once."""
    return Settings()
