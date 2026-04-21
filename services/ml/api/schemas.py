"""
schemas.py — ML Service
────────────────────────
Pydantic models for all ML API request/response shapes.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── /train ─────────────────────────────────────────────────────────────────────

class TrainResponse(BaseModel):
    tenant_id: str
    model_id: Optional[str] = Field(
        default=None,
        description="Database ID of the model record (UUID string).",
    )
    model_type: str
    target_column: str
    feature_columns: List[str]
    train_rows: int
    test_rows: int
    metrics: Dict[str, float] = Field(
        ...,
        description=(
            "Model accuracy on held-out test data. "
            "r2: 1.0 = perfect, 0.0 = no better than guessing the mean. "
            "mae: Mean Absolute Error (same units as target). "
            "rmse: Root Mean Squared Error."
        ),
    )
    message: str


# ── /predict ───────────────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    tenant_id: str = Field(..., description="Your tenant ID.")
    input_data: List[Dict[str, Any]] = Field(
        ...,
        description=(
            "List of rows to predict. Each row is a dict of feature name → value. "
            "Keys should match the columns used during training."
        ),
        min_length=1,
    )
    explain: bool = Field(
        default=False,
        description="Set to true to include SHAP-based explanations with each prediction.",
    )


class PredictionResult(BaseModel):
    prediction: float
    top_drivers: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Top 5 features that influenced this prediction (only when explain=true).",
    )
    summary: Optional[str] = Field(
        default=None,
        description="Plain-English explanation of the prediction (only when explain=true).",
    )


class PredictResponse(BaseModel):
    tenant_id: str
    target_column: str
    results: List[PredictionResult]


# ── /status ────────────────────────────────────────────────────────────────────

class ModelStatusResponse(BaseModel):
    tenant_id: str
    model_trained: bool
    model_type: Optional[str] = None
    target_column: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None


# ── Error ──────────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
