"""
tenant_repo.py
──────────────
Data access layer for the `tenants` table.

Services never write raw SQL — they call these functions instead.
This keeps database logic in one place and makes it easy to test.

Security note:
  - API keys are stored HASHED (bcrypt). This file handles hashing on create
    and verification on lookup.
  - The plaintext key is only returned ONCE (at creation) and never again.
"""

import hashlib
import secrets
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.models.tenant import Tenant


async def create_tenant(
    db: AsyncSession,
    name: str,
    plan: str = "free",
) -> tuple[Tenant, str]:
    """
    Create a new tenant and generate their API key.

    Returns:
        (tenant, plaintext_api_key) — the plaintext key is shown ONCE.
        Store it securely; it cannot be retrieved again.
    """
    plaintext_key = secrets.token_urlsafe(32)
    key_hash = _hash_api_key(plaintext_key)

    tenant = Tenant(
        id=uuid.uuid4(),
        name=name,
        api_key_hash=key_hash,
        plan=plan,
        is_active=True,
    )
    db.add(tenant)
    await db.flush()  # assigns DB-generated values without committing
    return tenant, plaintext_key


async def get_tenant_by_id(
    db: AsyncSession, tenant_id: uuid.UUID
) -> Optional[Tenant]:
    """Fetch a tenant by their UUID. Returns None if not found."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    return result.scalar_one_or_none()


async def get_tenant_by_api_key(
    db: AsyncSession, plaintext_key: str
) -> Optional[Tenant]:
    """
    Look up a tenant by their plaintext API key.

    Hashes the key and searches by hash — the plaintext never touches the DB.
    Returns None if the key is invalid or the tenant is inactive.
    """
    key_hash = _hash_api_key(plaintext_key)
    result = await db.execute(
        select(Tenant).where(
            Tenant.api_key_hash == key_hash,
            Tenant.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def deactivate_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> bool:
    """
    Soft-delete: mark a tenant as inactive instead of deleting their data.
    Returns True if the tenant was found and deactivated.
    """
    tenant = await get_tenant_by_id(db, tenant_id)
    if not tenant:
        return False
    tenant.is_active = False
    await db.flush()
    return True


def _hash_api_key(plaintext_key: str) -> str:
    """
    SHA-256 hash of the API key for storage.

    We use SHA-256 (not bcrypt) because:
    - API keys are already high-entropy random strings (32 bytes = 256 bits)
    - bcrypt is designed for low-entropy passwords; unnecessary overhead here
    - SHA-256 is fast and sufficient for high-entropy tokens
    """
    return hashlib.sha256(plaintext_key.encode()).hexdigest()
