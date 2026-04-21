"""
schemas.py
──────────
Pydantic models that define the shape of every API request and response.

Using explicit schemas means:
- FastAPI auto-validates incoming data (bad requests fail with a clear 422 error)
- The auto-generated /docs page shows exactly what each endpoint expects
- Frontend / other services have a clear contract to code against
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Upload endpoint (/upload) ──────────────────────────────────────────────────

class IngestResponse(BaseModel):
    """Returned after a file is successfully ingested into the vector store."""

    tenant_id: str = Field(..., description="The tenant the file was ingested for.")
    document_id: Optional[str] = Field(
        default=None,
        description="Database ID of the created document record (UUID string).",
    )
    file_name: str = Field(..., description="The name of the uploaded file.")
    chunks_stored: int = Field(
        ..., description="Number of text chunks stored in the vector database."
    )
    message: str = Field(..., description="Human-readable success message.")


# ── Chat endpoint (/chat) ──────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    """A single message in a conversation (used for chat history)."""

    role: str = Field(..., description="'human' or 'ai'")
    content: str = Field(..., description="The message text.")


class ChatRequest(BaseModel):
    """Request body for the /chat endpoint."""

    tenant_id: str = Field(..., description="The tenant asking the question.")
    question: str = Field(..., description="The user's natural language question.")
    session_id: Optional[str] = Field(
        default=None,
        description=(
            "Existing chat session UUID. If omitted, a new session is created. "
            "Pass the session_id returned from previous /chat responses to "
            "maintain conversation history across calls."
        ),
    )
    chat_history: Optional[List[ChatMessage]] = Field(
        default=[],
        description="Previous messages in this session for multi-turn memory.",
    )


class ChatResponse(BaseModel):
    """Response from the /chat endpoint."""

    tenant_id: str
    question: str
    answer: str = Field(..., description="The AI Copilot's answer.")
    session_id: Optional[str] = Field(
        default=None,
        description="Chat session UUID — pass this in future /chat requests to continue the conversation.",
    )


# ── Tenant endpoints (/tenants) ───────────────────────────────────────────────

class TenantCreateRequest(BaseModel):
    """Request body for POST /tenants."""

    name: str = Field(..., description="Display name for the tenant (e.g. company name).")
    plan: str = Field(
        default="free",
        description="Subscription plan: free | pro | enterprise",
    )


class TenantCreateResponse(BaseModel):
    """Returned after a tenant is created. The api_key is shown exactly once."""

    id: str = Field(..., description="Tenant UUID — use this as tenant_id in all other endpoints.")
    name: str
    plan: str
    is_active: bool
    api_key: str = Field(
        ...,
        description="Your API key. Save this — it cannot be retrieved again.",
    )
    message: str


class TenantResponse(BaseModel):
    """Public tenant info (no API key)."""

    id: str
    name: str
    plan: str
    is_active: bool


# ── Error response ─────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Standard error shape returned for 4xx / 5xx responses."""

    detail: str
