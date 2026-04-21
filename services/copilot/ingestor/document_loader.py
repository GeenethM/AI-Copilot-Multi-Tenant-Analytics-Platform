"""
document_loader.py
──────────────────
Loads files uploaded by a tenant into a list of LangChain Document objects.
Each Document carries the text content + metadata (source file, tenant ID, etc.)

Supported formats: PDF, CSV, Excel (.xlsx/.xls), plain text (.txt)
"""

import os
from pathlib import Path
from typing import List

from langchain_core.documents import Document


def load_document(file_path: str, tenant_id: str) -> List[Document]:
    """
    Load a single file and return a list of LangChain Document objects.

    Args:
        file_path: Absolute or relative path to the uploaded file.
        tenant_id: The tenant this file belongs to. Stored in metadata so
                   retrieval can be scoped per tenant later.

    Returns:
        List of Document objects. Most loaders return one Document per page
        (PDF) or one per row (CSV), so the list can be long.

    Raises:
        ValueError: If the file extension is not supported.
        FileNotFoundError: If the file does not exist at the given path.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = path.suffix.lower()
    documents: List[Document] = []

    if ext == ".pdf":
        documents = _load_pdf(path)
    elif ext == ".csv":
        documents = _load_csv(path)
    elif ext in (".xlsx", ".xls"):
        documents = _load_excel(path)
    elif ext == ".txt":
        documents = _load_text(path)
    else:
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            "Supported types: .pdf, .csv, .xlsx, .xls, .txt"
        )

    # Attach tenant_id to every document's metadata so retrieval stays
    # isolated per tenant (multi-tenancy safety).
    for doc in documents:
        doc.metadata["tenant_id"] = tenant_id
        doc.metadata["source_file"] = path.name

    return documents


# ── Private helpers ────────────────────────────────────────────────────────────

def _load_pdf(path: Path) -> List[Document]:
    from langchain_community.document_loaders import PyPDFLoader

    loader = PyPDFLoader(str(path))
    return loader.load()


def _load_csv(path: Path) -> List[Document]:
    from langchain_community.document_loaders.csv_loader import CSVLoader

    loader = CSVLoader(file_path=str(path))
    return loader.load()


def _load_excel(path: Path) -> List[Document]:
    """
    Excel files are loaded by reading each sheet into a CSV-like text block,
    one Document per row.
    """
    import pandas as pd

    documents: List[Document] = []
    xl = pd.ExcelFile(str(path))

    for sheet_name in xl.sheet_names:
        df = xl.parse(sheet_name)
        for idx, row in df.iterrows():
            content = "\n".join(f"{col}: {val}" for col, val in row.items())
            documents.append(
                Document(
                    page_content=content,
                    metadata={"sheet": sheet_name, "row": idx},
                )
            )

    return documents


def _load_text(path: Path) -> List[Document]:
    from langchain_community.document_loaders import TextLoader

    loader = TextLoader(str(path), encoding="utf-8")
    return loader.load()
