"""
tenant_routes.py
────────────────
API endpoints for tenant management.

Endpoints:
    POST /tenants          — Create a new tenant; returns their API key (shown once).
    GET  /tenants/{id}     — Look up a tenant by UUID.
    DELETE /tenants/{id}   — Deactivate a tenant (soft delete — data is kept).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    TenantCreateRequest,
    TenantCreateResponse,
    TenantResponse,
)
from shared.database.connection import get_db
from shared.database.repositories import tenant_repo

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.post(
    "",
    response_model=TenantCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tenant",
    description=(
        "Creates a tenant account and generates a unique API key. "
        "**The API key is only shown once — save it immediately.** "
        "It is stored hashed and cannot be retrieved again."
    ),
)
async def create_tenant(
    body: TenantCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    tenant, plaintext_key = await tenant_repo.create_tenant(
        db,
        name=body.name,
        plan=body.plan,
    )
    await db.commit()

    return TenantCreateResponse(
        id=str(tenant.id),
        name=tenant.name,
        plan=tenant.plan,
        is_active=tenant.is_active,
        api_key=plaintext_key,
        message=(
            "Tenant created. Save your api_key — it will NOT be shown again. "
            "Use it as your tenant_id when calling /upload and /chat."
        ),
    )


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Get tenant details",
    responses={404: {"description": "Tenant not found."}},
)
async def get_tenant(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="tenant_id must be a valid UUID.",
        )

    tenant = await tenant_repo.get_tenant_by_id(db, tid)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_id}' not found.",
        )

    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        plan=tenant.plan,
        is_active=tenant.is_active,
    )


@router.delete(
    "/{tenant_id}",
    status_code=status.HTTP_200_OK,
    summary="Deactivate a tenant",
    description="Soft-deletes the tenant — their data is kept but they can no longer use the API.",
    responses={404: {"description": "Tenant not found."}},
)
async def deactivate_tenant(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        tid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="tenant_id must be a valid UUID.",
        )

    deactivated = await tenant_repo.deactivate_tenant(db, tid)
    if not deactivated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_id}' not found.",
        )

    await db.commit()
    return {"message": f"Tenant '{tenant_id}' has been deactivated."}
