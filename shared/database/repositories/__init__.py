"""
shared.database.repositories
─────────────────────────────
Re-exports all repository modules so services can import them concisely:

    from shared.database.repositories import document_repo, chat_repo
"""

from shared.database.repositories import (  # noqa: F401
    chat_repo,
    document_repo,
    ml_model_repo,
    prediction_repo,
    tenant_repo,
)
