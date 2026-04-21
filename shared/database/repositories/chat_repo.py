"""
chat_repo.py
────────────
Data access layer for `chat_sessions` and `chat_messages`.

The copilot service uses these to persist and reload conversation history
so multi-turn memory works across API calls.
"""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.database.models.chat_session import ChatMessage, ChatSession


# ── Sessions ───────────────────────────────────────────────────────────────────

async def create_session(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    document_id: Optional[uuid.UUID] = None,
    title: Optional[str] = None,
) -> ChatSession:
    """Start a new chat session for a tenant."""
    session = ChatSession(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        document_id=document_id,
        title=title,
    )
    db.add(session)
    await db.flush()
    return session


async def get_session_with_messages(
    db: AsyncSession, session_id: uuid.UUID
) -> Optional[ChatSession]:
    """Load a session and all its messages in a single query."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == session_id)
        .options(selectinload(ChatSession.messages))
    )
    return result.scalar_one_or_none()


async def list_sessions_for_tenant(
    db: AsyncSession, tenant_id: uuid.UUID
) -> list[ChatSession]:
    """Return all sessions for a tenant, newest first (messages not loaded)."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.tenant_id == tenant_id)
        .order_by(ChatSession.updated_at.desc())
    )
    return list(result.scalars().all())


# ── Messages ───────────────────────────────────────────────────────────────────

async def add_message(
    db: AsyncSession,
    session_id: uuid.UUID,
    tenant_id: uuid.UUID,
    role: str,
    content: str,
) -> ChatMessage:
    """
    Append a message to a session.

    Automatically assigns the next sequence_number.
    Role must be one of: 'human', 'ai', 'system'.
    """
    # Count existing messages to assign correct sequence number
    from sqlalchemy import func as sqlfunc
    count_result = await db.execute(
        select(sqlfunc.count()).where(ChatMessage.session_id == session_id)
    )
    next_seq = (count_result.scalar() or 0) + 1

    message = ChatMessage(
        id=uuid.uuid4(),
        session_id=session_id,
        tenant_id=tenant_id,
        role=role,
        content=content,
        sequence_number=next_seq,
    )
    db.add(message)
    await db.flush()
    return message


async def get_messages_for_session(
    db: AsyncSession, session_id: uuid.UUID
) -> list[ChatMessage]:
    """Return all messages for a session ordered by sequence number."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.sequence_number)
    )
    return list(result.scalars().all())
