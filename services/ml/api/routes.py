"""
routes.py — ML Service
───────────────────────
FastAPI routes for the predictive ML service.

Endpoints:
    POST /train    — Upload a file and train a model on it.
    POST /predict  — Run predictions using the trained model.
    GET  /status   — Check whether a model exists for a tenant.
    GET  /health   — Liveness check.
"""

import os
import tempfile
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    ErrorResponse,
    ModelStatusResponse,
    PredictRequest,
    PredictResponse,
    PredictionResult,
    TrainResponse,
)
from insights.explainer import explain_prediction
from models.model_store import load_model, model_exists
from models.predictor import predict
from models.trainer import train
from shared.database.connection import get_db
from shared.database.repositories import ml_model_repo, prediction_repo

router = APIRouter()

_ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


@router.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "ml"}


@router.post(
    "/train",
    response_model=TrainResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Training"],
    summary="Train a predictive model on your data",
    description=(
        "Upload a CSV or Excel file. Specify which column to predict "
        "(e.g. 'revenue', 'roi', 'profit'). The service trains a regression "
        "model and returns accuracy metrics."
    ),
)
async def train_model(
    tenant_id: str = Form(..., description="Your tenant ID."),
    target_column: str = Form(
        ..., description="The column name to predict (e.g. 'revenue')."
    ),
    model_type: str = Form(
        default="random_forest",
        description="Model algorithm: random_forest | gradient_boosting | linear_regression",
    ),
    file: UploadFile = File(..., description="CSV or Excel file with your training data."),
    db: AsyncSession = Depends(get_db),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(_ALLOWED_EXTENSIONS))}",
        )

    # Validate tenant UUID
    try:
        tenant_uuid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="tenant_id must be a valid UUID.",
        )

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {exc}",
        )

    # Create a DB record before training so we track status
    model_record = await ml_model_repo.create_model_record(
        db,
        tenant_id=tenant_uuid,
        model_type=model_type,
        target_column=target_column,
        feature_columns=[],  # updated after training when we know which columns were used
    )

    try:
        result = train(
            tenant_id=tenant_id,
            file_path=tmp_path,
            target_column=target_column,
            model_type=model_type,
        )
    except ValueError as exc:
        await ml_model_repo.mark_model_failed(db, model_record.id, str(exc))
        await db.commit()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        await ml_model_repo.mark_model_failed(db, model_record.id, str(exc))
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Training failed: {exc}",
        )
    finally:
        os.unlink(tmp_path)

    # Update the record with the trained model's path and metrics
    model_record.feature_columns = result["feature_columns"]
    await ml_model_repo.mark_model_ready(
        db,
        model_id=model_record.id,
        model_path=result.get("model_path", ""),
        metrics=result["metrics"],
        train_rows=result["train_rows"],
        test_rows=result["test_rows"],
    )
    await db.commit()

    return TrainResponse(
        tenant_id=tenant_id,
        model_id=str(model_record.id),
        model_type=result["model_type"],
        target_column=result["target_column"],
        feature_columns=result["feature_columns"],
        train_rows=result["train_rows"],
        test_rows=result["test_rows"],
        metrics=result["metrics"],
        message=(
            f"Model trained successfully. "
            f"R² = {result['metrics']['r2']} on {result['test_rows']} test rows."
        ),
    )


@router.post(
    "/predict",
    response_model=PredictResponse,
    tags=["Prediction"],
    summary="Run predictions with your trained model",
    description=(
        "Pass one or more rows of feature values. Returns predicted values. "
        "Set explain=true to include SHAP-based explanations of each prediction."
    ),
    responses={
        404: {"model": ErrorResponse, "description": "No trained model found for tenant."},
    },
)
async def run_prediction(body: PredictRequest, db: AsyncSession = Depends(get_db)):
    # Validate tenant UUID
    try:
        tenant_uuid = uuid.UUID(body.tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="tenant_id must be a valid UUID.",
        )

    if not model_exists(body.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No trained model found for tenant '{body.tenant_id}'. Call POST /train first.",
        )

    try:
        predictions = predict(body.tenant_id, body.input_data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {exc}",
        )

    explanations = None
    if body.explain:
        try:
            explanations = explain_prediction(body.tenant_id, body.input_data, predictions)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Explanation failed: {exc}",
            )

    _, metadata = load_model(body.tenant_id)

    # Fetch the latest ready model record for this tenant (for the audit log FK)
    model_record = await ml_model_repo.get_latest_ready_model(db, tenant_uuid)

    results = []
    for i, pred_value in enumerate(predictions):
        exp = explanations[i] if explanations else None

        # Log every prediction to the audit table
        await prediction_repo.log_prediction(
            db,
            tenant_id=tenant_uuid,
            model_id=model_record.id if model_record else None,
            input_data=body.input_data[i],
            predicted_value=pred_value,
            explanation=exp,
        )

        if exp:
            results.append(PredictionResult(
                prediction=pred_value,
                top_drivers=exp["top_drivers"],
                summary=exp["summary"],
            ))
        else:
            results.append(PredictionResult(prediction=pred_value))

    await db.commit()

    return PredictResponse(
        tenant_id=body.tenant_id,
        target_column=metadata["target_column"],
        results=results,
    )


@router.get(
    "/status/{tenant_id}",
    response_model=ModelStatusResponse,
    tags=["Training"],
    summary="Check whether a model exists for a tenant",
)
def model_status(tenant_id: str):
    if not model_exists(tenant_id):
        return ModelStatusResponse(tenant_id=tenant_id, model_trained=False)

    _, metadata = load_model(tenant_id)
    return ModelStatusResponse(
        tenant_id=tenant_id,
        model_trained=True,
        model_type=metadata.get("model_type"),
        target_column=metadata.get("target_column"),
        metrics=metadata.get("metrics"),
    )
