"""
embedder.py
───────────
Converts document chunks into vector embeddings and stores them in ChromaDB.

What are embeddings?
- An embedding is a list of numbers (a vector) that represents the *meaning*
  of a piece of text.
- Texts with similar meanings have vectors that are close together in space.
- This is what allows semantic search: "What were Q3 profits?" will find
  chunks about revenue even if the word "profits" isn't in the document.

Multi-tenancy:
- Each tenant's documents are stored in their own ChromaDB collection
  (named by tenant_id) so one tenant can never see another tenant's data.
"""

from typing import List

from langchain_chroma import Chroma
from langchain_core.documents import Document

from config.llm_factory import get_embedding_model
from config.settings import get_settings


def embed_and_store(chunks: List[Document], tenant_id: str) -> Chroma:
    """
    Embed a list of document chunks and persist them to ChromaDB.

    Args:
        chunks:    Chunked Documents from text_splitter.split_documents().
        tenant_id: Used as the ChromaDB collection name — keeps tenants isolated.

    Returns:
        The Chroma vector store instance (useful for immediately querying
        after ingestion without re-loading from disk).
    """
    settings = get_settings()
    embedding_model = get_embedding_model()

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        collection_name=_collection_name(tenant_id),
        persist_directory=settings.chroma_persist_directory,
    )

    return vector_store


def _collection_name(tenant_id: str) -> str:
    """
    ChromaDB collection names must be 3-63 characters, alphanumeric + hyphens.
    Prefix with 'tenant-' to make it readable and safe.
    """
    safe_id = "".join(c if c.isalnum() or c == "-" else "-" for c in tenant_id)
    return f"tenant-{safe_id}"[:63]
