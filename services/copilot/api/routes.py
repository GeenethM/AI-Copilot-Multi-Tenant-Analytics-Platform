"""
routes.py
─────────
FastAPI route definitions for the Copilot service.

Endpoints:
    POST /upload  — Upload a business document; ingest it into ChromaDB.
    POST /chat    — Ask a question; get an AI answer grounded in uploaded docs.
    GET  /health  — Liveness check (used by Docker / load balancers).
"""

import os
import tempfile
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import ChatRequest, ChatResponse, ErrorResponse, IngestResponse
from chain.rag_chain import ask
from ingestor.document_loader import load_document
from ingestor.text_splitter import split_documents
from ingestor.embedder import embed_and_store
from shared.database.connection import get_db
from shared.database.repositories import document_repo, chat_repo

router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check():
    """Liveness check — returns 200 if the service is running."""
    return {"status": "ok", "service": "copilot"}


@router.post(
    "/upload",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Ingestion"],
    summary="Upload a business document",
    description=(
        "Upload a PDF, CSV, Excel, or TXT file. The file is split into chunks, "
        "converted to embeddings, and stored in the tenant's vector database. "
        "After ingestion the tenant can query the document via /chat."
    ),
)
async def upload_document(
    tenant_id: str = Form(..., description="Your tenant ID."),
    file: UploadFile = File(..., description="The file to upload."),
    db: AsyncSession = Depends(get_db),
):
    # Validate file extension before doing any work
    allowed_extensions = {".pdf", ".csv", ".xlsx", ".xls", ".txt"}
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Unsupported file type '{file_ext}'. "
                f"Allowed types: {', '.join(sorted(allowed_extensions))}"
            ),
        )

    # Save the uploaded file to a temp location for processing
    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file_ext
        ) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {exc}",
        )

    # Create a database record so we can track ingestion status
    try:
        tenant_uuid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="tenant_id must be a valid UUID.",
        )

    doc_record = await document_repo.create_document(
        db,
        tenant_id=tenant_uuid,
        file_name=file.filename or "unknown",
        file_type=file_ext.lstrip("."),
        file_size_bytes=len(contents),
        storage_path=tmp_path,
    )

    # Run the ingestion pipeline
    try:
        documents = load_document(tmp_path, tenant_id=tenant_id)
        # Preserve the original filename in metadata (tmp name is not helpful)
        for doc in documents:
            doc.metadata["source_file"] = file.filename
        chunks = split_documents(documents)
        if not chunks:
            raise ValueError(
                f"No text could be extracted from '{file.filename}'. "
                "If it is a PDF, ensure it contains selectable text (not a scanned image)."
            )
        embed_and_store(chunks, tenant_id=tenant_id)
    except ValueError as exc:
        await document_repo.mark_ingestion_failed(db, doc_record.id, str(exc))
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    except Exception as exc:
        await document_repo.mark_ingestion_failed(db, doc_record.id, str(exc))
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {exc}",
        )
    finally:
        # Always clean up the temp file
        os.unlink(tmp_path)

    await document_repo.mark_ingestion_complete(db, doc_record.id, chunks_stored=len(chunks))
    await db.commit()

    return IngestResponse(
        tenant_id=tenant_id,
        document_id=str(doc_record.id),
        file_name=file.filename or "unknown",
        chunks_stored=len(chunks),
        message=(
            f"Successfully ingested '{file.filename}' — "
            f"{len(chunks)} chunks stored. You can now query this document."
        ),
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
    tags=["Copilot"],
    summary="Ask a question about your uploaded data",
    description=(
        "Send a natural language question. The AI Copilot retrieves relevant "
        "sections from your uploaded documents and generates a grounded answer. "
        "Pass chat_history for multi-turn conversations. "
        "Pass session_id from a previous response to continue a conversation."
    ),
    responses={
        404: {"model": ErrorResponse, "description": "No documents found for tenant."},
        500: {"model": ErrorResponse, "description": "Internal server error."},
    },
)
async def chat(body: ChatRequest, db: AsyncSession = Depends(get_db)):
    # Validate tenant UUID
    try:
        tenant_uuid = uuid.UUID(body.tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="tenant_id must be a valid UUID.",
        )

    # Resolve or create the chat session in the database
    if body.session_id:
        try:
            session_uuid = uuid.UUID(body.session_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="session_id must be a valid UUID.",
            )
        db_session = await chat_repo.get_session_with_messages(db, session_uuid)
        if db_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{body.session_id}' not found.",
            )
    else:
        db_session = await chat_repo.create_session(db, tenant_id=tenant_uuid)

    # Convert ChatMessage list to the tuple format LangChain expects
    history = [
        (msg.role, msg.content)
        for msg in (body.chat_history or [])
    ]

    try:
        answer = ask(
            tenant_id=body.tenant_id,
            question=body.question,
            chat_history=history,
        )
    except RuntimeError as exc:
        # Raised by vector_store.py when no documents have been ingested yet
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Copilot error: {exc}",
        )

    # Persist the exchange to the database
    await chat_repo.add_message(db, db_session.id, tenant_uuid, role="human", content=body.question)
    await chat_repo.add_message(db, db_session.id, tenant_uuid, role="ai", content=answer)
    await db.commit()

    return ChatResponse(
        tenant_id=body.tenant_id,
        question=body.question,
        answer=answer,
        session_id=str(db_session.id),
    )
