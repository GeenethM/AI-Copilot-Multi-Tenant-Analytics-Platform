"""
document_repo.py
────────────────
Data access layer for the `uploaded_documents` table.
"""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.models.document import UploadedDocument


async def create_document(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    file_name: str,
    file_type: str,
    file_size_bytes: Optional[int] = None,
    storage_path: Optional[str] = None,
) -> UploadedDocument:
    """Insert a new document record with status 'pending'."""
    doc = UploadedDocument(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        file_name=file_name,
        file_type=file_type,
        file_size_bytes=file_size_bytes,
        storage_path=storage_path,
        ingestion_status="pending",
    )
    db.add(doc)
    await db.flush()
    return doc


async def get_document_by_id(
    db: AsyncSession, document_id: uuid.UUID
) -> Optional[UploadedDocument]:
    result = await db.execute(
        select(UploadedDocument).where(UploadedDocument.id == document_id)
    )
    return result.scalar_one_or_none()


async def list_documents_for_tenant(
    db: AsyncSession, tenant_id: uuid.UUID
) -> list[UploadedDocument]:
    """Return all documents for a tenant, newest first."""
    result = await db.execute(
        select(UploadedDocument)
        .where(UploadedDocument.tenant_id == tenant_id)
        .order_by(UploadedDocument.created_at.desc())
    )
    return list(result.scalars().all())


async def mark_ingestion_complete(
    db: AsyncSession, document_id: uuid.UUID, chunks_stored: int
) -> Optional[UploadedDocument]:
    """Update status to 'completed' after successful ChromaDB ingestion."""
    doc = await get_document_by_id(db, document_id)
    if not doc:
        return None
    doc.ingestion_status = "completed"
    doc.chunks_stored = chunks_stored
    doc.error_message = None
    await db.flush()
    return doc


async def mark_ingestion_failed(
    db: AsyncSession, document_id: uuid.UUID, error_message: str
) -> Optional[UploadedDocument]:
    """Update status to 'failed' with an error message."""
    doc = await get_document_by_id(db, document_id)
    if not doc:
        return None
    doc.ingestion_status = "failed"
    doc.error_message = error_message
    await db.flush()
    return doc
