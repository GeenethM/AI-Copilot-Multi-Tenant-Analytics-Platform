"""
schemas.py — Analytics Service
────────────────────────────────
Pydantic models for all analytics API request/response shapes.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Shared ─────────────────────────────────────────────────────────────────────

class DataPayload(BaseModel):
    """Inline data submission: a list of row dicts instead of a file upload."""
    tenant_id: str
    records: List[Dict[str, Any]] = Field(
        ...,
        min_length=1,
        description="List of data rows. Each row is a dict of column name → value.",
    )


# ── /analyse ───────────────────────────────────────────────────────────────────

class AnalyseRequest(DataPayload):
    numeric_columns: Optional[List[str]] = Field(
        default=None,
        description="Columns to analyse. Defaults to all numeric columns.",
    )
    date_column: Optional[str] = Field(
        default=None,
        description="Date/time column for time-based breakdowns.",
    )
    group_by_column: Optional[str] = Field(
        default=None,
        description="Column to group KPIs by (e.g. 'region', 'product_category').",
    )


class AnalyseResponse(BaseModel):
    tenant_id: str
    overall_kpis: Dict[str, Any]
    monthly: Optional[List[Dict]] = None
    by_group: Optional[List[Dict]] = None


# ── /trends ────────────────────────────────────────────────────────────────────

class TrendsRequest(DataPayload):
    value_column: str = Field(..., description="The numeric column to analyse for trends.")
    date_column: Optional[str] = Field(
        default=None,
        description="Date column for time-ordering the data.",
    )
    period: str = Field(
        default="M",
        description="Aggregation period: M=monthly, Q=quarterly, Y=yearly.",
    )


class TrendsResponse(BaseModel):
    tenant_id: str
    value_column: str
    direction: str = Field(..., description="GROWING | DECLINING | STABLE")
    latest_change_pct: Optional[float]
    rolling_average: List[float]
    period_over_period: List[Dict[str, Any]]


# ── /anomalies ─────────────────────────────────────────────────────────────────

class AnomaliesRequest(DataPayload):
    numeric_columns: Optional[List[str]] = Field(
        default=None,
        description="Columns to scan. Defaults to all numeric columns.",
    )
    date_column: Optional[str] = Field(
        default=None,
        description="Date column included in anomaly row output.",
    )


class AnomalyItem(BaseModel):
    row_index: int
    column: str
    value: float
    z_score: float
    direction: str = Field(..., description="HIGH or LOW")
    severity: str = Field(..., description="MEDIUM | HIGH | CRITICAL")
    date: Optional[str] = None


class AnomaliesResponse(BaseModel):
    tenant_id: str
    total_anomalies: int
    columns_scanned: List[str]
    anomalies: List[AnomalyItem]


# ── Error ──────────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
