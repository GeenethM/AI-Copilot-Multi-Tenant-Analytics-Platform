from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All configuration is read from environment variables (or a .env file).
    Copy .env.example to .env and fill in the values you need.
    """

    # Which LLM provider to use: openai | anthropic | google
    llm_provider: str = "openai"

    # API keys — only the key for your chosen provider is required
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    # Model name — must match your chosen provider
    # OpenAI:    gpt-4o | gpt-4o-mini | gpt-4-turbo
    # Anthropic: claude-3-5-sonnet-20241022 | claude-3-haiku-20240307
    # Google:    gemini-1.5-pro | gemini-1.5-flash
    model_name: str = "gpt-4o"

    # 0.0 = deterministic / consistent answers (recommended for business agents)
    temperature: float = 0.0

    # ── Database ──────────────────────────────────────────────────────────────
    # Shared PostgreSQL connection string (multi-tenant layer)
    database_url: str = (
        "postgresql+asyncpg://postgres:password@localhost:5432/analytics_platform"
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Returns a cached Settings instance. The cache means .env is only read once."""
    return Settings()
