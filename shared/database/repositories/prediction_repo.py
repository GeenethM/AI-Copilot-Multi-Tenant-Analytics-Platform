"""
prediction_repo.py
──────────────────
Data access layer for the `prediction_logs` table.
"""

import uuid
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.models.prediction_log import PredictionLog


async def log_prediction(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    model_id: uuid.UUID,
    input_data: dict[str, Any],
    predicted_value: float,
    explanation: Optional[dict] = None,
) -> PredictionLog:
    """
    Record a prediction in the audit log.

    Args:
        tenant_id:       The tenant who made the prediction.
        model_id:        The MLModel record that produced the prediction.
        input_data:      The raw input feature dict.
        predicted_value: The model's output.
        explanation:     Optional SHAP explanation dict.
    """
    log = PredictionLog(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        model_id=model_id,
        input_data=input_data,
        predicted_value=predicted_value,
        explanation=explanation,
    )
    db.add(log)
    await db.flush()
    return log


async def list_predictions_for_tenant(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    limit: int = 100,
) -> list[PredictionLog]:
    """Return the most recent predictions for a tenant."""
    result = await db.execute(
        select(PredictionLog)
        .where(PredictionLog.tenant_id == tenant_id)
        .order_by(PredictionLog.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def list_predictions_for_model(
    db: AsyncSession,
    model_id: uuid.UUID,
    limit: int = 100,
) -> list[PredictionLog]:
    """Return the most recent predictions for a specific model."""
    result = await db.execute(
        select(PredictionLog)
        .where(PredictionLog.model_id == model_id)
        .order_by(PredictionLog.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
