"""
retriever.py
────────────
Given a tenant and a user's question, finds the most relevant document chunks
from that tenant's vector store using semantic similarity search.

How it works:
1. The user's question is converted to a vector (embedding).
2. ChromaDB compares that vector to all stored chunk vectors.
3. The top-K closest chunks (by cosine similarity) are returned.
4. These chunks are passed to the LLM as context in rag_chain.py.
"""

from typing import List

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

from config.settings import get_settings
from retriever.vector_store import get_vector_store


def get_retriever(tenant_id: str) -> VectorStoreRetriever:
    """
    Build a retriever for a specific tenant.

    The retriever is a thin wrapper around the vector store that has a
    standard .invoke(question) interface used by the RAG chain.

    Args:
        tenant_id: The tenant whose documents to search.

    Returns:
        A LangChain VectorStoreRetriever configured to return the top-K
        most relevant chunks (K is set in settings.retrieval_top_k).
    """
    settings = get_settings()
    vector_store = get_vector_store(tenant_id)

    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.retrieval_top_k},
    )


def retrieve_chunks(tenant_id: str, question: str) -> List[Document]:
    """
    Convenience function: retrieve the top-K relevant chunks for a question.

    Args:
        tenant_id: The tenant whose documents to search.
        question:  The user's natural language question.

    Returns:
        List of the most relevant Document chunks.
    """
    retriever = get_retriever(tenant_id)
    return retriever.invoke(question)
