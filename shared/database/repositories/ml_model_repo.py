"""
ml_model_repo.py
────────────────
Data access layer for the `ml_models` table.
"""

import uuid
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.models.ml_model import MLModel


async def create_model_record(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    model_type: str,
    target_column: str,
    feature_columns: list[str],
) -> MLModel:
    """Insert a new model record with status 'training'."""
    record = MLModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        model_type=model_type,
        target_column=target_column,
        feature_columns=feature_columns,
        training_status="training",
    )
    db.add(record)
    await db.flush()
    return record


async def get_model_by_id(
    db: AsyncSession, model_id: uuid.UUID
) -> Optional[MLModel]:
    result = await db.execute(select(MLModel).where(MLModel.id == model_id))
    return result.scalar_one_or_none()


async def get_latest_ready_model(
    db: AsyncSession, tenant_id: uuid.UUID
) -> Optional[MLModel]:
    """Return the most recently trained 'ready' model for a tenant."""
    result = await db.execute(
        select(MLModel)
        .where(
            MLModel.tenant_id == tenant_id,
            MLModel.training_status == "ready",
        )
        .order_by(MLModel.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def mark_model_ready(
    db: AsyncSession,
    model_id: uuid.UUID,
    model_path: str,
    metrics: dict[str, float],
    train_rows: int,
    test_rows: int,
) -> Optional[MLModel]:
    """Update a model record to 'ready' after successful training."""
    record = await get_model_by_id(db, model_id)
    if not record:
        return None
    record.training_status = "ready"
    record.model_path = model_path
    record.r2_score = metrics.get("r2")
    record.mae = metrics.get("mae")
    record.rmse = metrics.get("rmse")
    record.train_rows = train_rows
    record.test_rows = test_rows
    await db.flush()
    return record


async def mark_model_failed(
    db: AsyncSession, model_id: uuid.UUID, error_message: str
) -> Optional[MLModel]:
    """Update a model record to 'failed' with an error message."""
    record = await get_model_by_id(db, model_id)
    if not record:
        return None
    record.training_status = "failed"
    record.error_message = error_message
    await db.flush()
    return record
