from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All configuration is read from environment variables (or a .env file).
    Copy .env.example to .env and fill in your values.
    """

    # ── LLM (for generating answers) ─────────────────────────────────────────
    # Which provider to use: openai | anthropic | google
    llm_provider: str = "openai"

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    # OpenAI:    gpt-4o | gpt-4o-mini
    # Anthropic: claude-3-5-sonnet-20241022 | claude-3-haiku-20240307
    # Google:    gemini-1.5-pro | gemini-1.5-flash
    model_name: str = "gpt-4o"

    # 0.0 = factual / grounded answers (recommended for RAG)
    temperature: float = 0.0

    # ── Embeddings (for converting text → vectors) ────────────────────────────
    # Provider for embeddings: openai | huggingface
    embedding_provider: str = "openai"

    # OpenAI embedding model — text-embedding-3-small is fast and cheap
    openai_embedding_model: str = "text-embedding-3-small"

    # HuggingFace embedding model (local, free — no API key needed)
    huggingface_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ── Vector store (ChromaDB) ───────────────────────────────────────────────
    # Where ChromaDB persists data on disk
    chroma_persist_directory: str = "./chroma_db"

    # ── Document ingestion ────────────────────────────────────────────────────
    # Characters per chunk when splitting documents
    chunk_size: int = 1000

    # Overlap between consecutive chunks (preserves context at boundaries)
    chunk_overlap: int = 200

    # How many chunks to retrieve for each user question
    retrieval_top_k: int = 5

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
