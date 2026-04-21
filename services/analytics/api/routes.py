"""
routes.py — Analytics Service
──────────────────────────────
FastAPI routes for the analytics (KPIs, trends, anomalies) service.

Endpoints:
    POST /analyse    — Compute KPI summaries for uploaded data.
    POST /trends     — Detect growth/decline trends in a time-series column.
    POST /anomalies  — Flag statistical outliers in numeric columns.
    GET  /health     — Liveness check.

All endpoints accept inline JSON records (no file upload needed here —
the data has already been loaded from the tenant's uploaded files by
the ingestor in the copilot service, or can be sent directly).
"""

import pandas as pd
from fastapi import APIRouter, HTTPException, status

from api.schemas import (
    AnalyseRequest,
    AnalyseResponse,
    AnomaliesRequest,
    AnomaliesResponse,
    TrendsRequest,
    TrendsResponse,
)
from engine.aggregator import compute_kpis
from engine.anomaly_detector import detect_anomalies
from engine.trend_detector import detect_trends

router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "analytics"}


@router.post(
    "/analyse",
    response_model=AnalyseResponse,
    tags=["Analytics"],
    summary="Compute KPI summaries",
    description=(
        "Pass your data as a list of JSON records. "
        "Returns totals, averages, min/max, std deviation per numeric column, "
        "plus optional monthly and group breakdowns."
    ),
)
def analyse(body: AnalyseRequest):
    try:
        df = pd.DataFrame(body.records)
        result = compute_kpis(
            df,
            numeric_columns=body.numeric_columns,
            date_column=body.date_column,
            group_by_column=body.group_by_column,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {exc}",
        )

    return AnalyseResponse(
        tenant_id=body.tenant_id,
        overall_kpis=result["overall_kpis"],
        monthly=result["monthly"],
        by_group=result["by_group"],
    )


@router.post(
    "/trends",
    response_model=TrendsResponse,
    tags=["Analytics"],
    summary="Detect trends in a numeric column",
    description=(
        "Analyses a numeric column over time (or row order if no date column). "
        "Returns rolling averages, period-over-period % changes, "
        "and a direction label: GROWING, DECLINING, or STABLE."
    ),
)
def trends(body: TrendsRequest):
    try:
        df = pd.DataFrame(body.records)
        result = detect_trends(
            df,
            value_column=body.value_column,
            date_column=body.date_column,
            period=body.period,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trend detection failed: {exc}",
        )

    return TrendsResponse(
        tenant_id=body.tenant_id,
        value_column=body.value_column,
        **result,
    )


@router.post(
    "/anomalies",
    response_model=AnomaliesResponse,
    tags=["Analytics"],
    summary="Detect anomalies / outliers in numeric data",
    description=(
        "Scans numeric columns using Z-score analysis. "
        "Flags values that deviate significantly from the column mean. "
        "Severity levels: MEDIUM | HIGH | CRITICAL."
    ),
)
def anomalies(body: AnomaliesRequest):
    try:
        df = pd.DataFrame(body.records)
        result = detect_anomalies(
            df,
            numeric_columns=body.numeric_columns,
            date_column=body.date_column,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anomaly detection failed: {exc}",
        )

    return AnomaliesResponse(
        tenant_id=body.tenant_id,
        total_anomalies=result["total_anomalies"],
        columns_scanned=result["columns_scanned"],
        anomalies=result["anomalies"],
    )
