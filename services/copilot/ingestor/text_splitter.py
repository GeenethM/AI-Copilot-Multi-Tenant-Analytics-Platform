"""
text_splitter.py
────────────────
Splits loaded Documents into smaller chunks that fit inside an LLM's context
window and can be retrieved precisely.

Why split?
- A 50-page PDF has too much text to pass to the LLM in one go.
- Smaller chunks mean more targeted retrieval — only the relevant paragraphs
  get sent, not the entire document.
- chunk_overlap preserves context at the boundaries of each chunk so sentences
  don't get cut off mid-thought.
"""

from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import get_settings


def split_documents(documents: List[Document]) -> List[Document]:
    """
    Split a list of Documents into smaller chunks.

    Uses RecursiveCharacterTextSplitter which tries to break on natural
    boundaries (paragraphs → sentences → words) before hard-cutting on
    character count.

    Args:
        documents: Raw documents from document_loader.load_document().

    Returns:
        List of smaller Document chunks, each with the original metadata
        preserved (tenant_id, source_file, etc.).
    """
    settings = get_settings()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        # Try to split on these boundaries before cutting by character count
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)
    return chunks
