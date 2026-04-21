"""
vector_store.py
───────────────
Manages connections to ChromaDB — loading existing collections so the
retriever can search them without re-ingesting documents.

Each tenant has their own isolated collection (named tenant-{tenant_id}).
"""

from langchain_chroma import Chroma
from langchain_core.vectorstores import VectorStore

from config.llm_factory import get_embedding_model
from config.settings import get_settings
from ingestor.embedder import _collection_name


def get_vector_store(tenant_id: str) -> VectorStore:
    """
    Load an existing ChromaDB collection for a tenant.

    This does NOT ingest any new documents — it just opens the persisted
    collection so the retriever can run similarity searches against it.

    Args:
        tenant_id: The tenant whose collection to load.

    Returns:
        A LangChain VectorStore wrapping the tenant's ChromaDB collection.

    Raises:
        RuntimeError: If no documents have been ingested for this tenant yet.
    """
    settings = get_settings()
    embedding_model = get_embedding_model()

    collection = _collection_name(tenant_id)

    vector_store = Chroma(
        collection_name=collection,
        embedding_function=embedding_model,
        persist_directory=settings.chroma_persist_directory,
    )

    # Guard: if the collection is empty the tenant hasn't uploaded anything yet
    if vector_store._collection.count() == 0:
        raise RuntimeError(
            f"No documents found for tenant '{tenant_id}'. "
            "Please upload and ingest documents before querying."
        )

    return vector_store
