"""
explainer.py
────────────
Uses SHAP to explain *why* the model made a prediction.

What is SHAP?
  SHAP (SHapley Additive exPlanations) assigns each input feature a score
  that shows how much it pushed the prediction up or down from the baseline.

  Example output:
    "marketing_spend contributed +$12,400 to this prediction.
     headcount contributed -$3,200."

Why it matters for business:
  Without explanations, ML is a black box — users won't trust or act on
  predictions they can't understand. SHAP makes the model auditable.

Supported models: RandomForest, GradientBoosting (TreeExplainer — fast).
Linear regression falls back to a simpler coefficient-based explanation.
"""

from typing import Any, Dict, List

import numpy as np
import pandas as pd
import shap
from sklearn.pipeline import Pipeline

from config.settings import get_settings
from models.model_store import load_model


def explain_prediction(
    tenant_id: str,
    input_data: List[Dict[str, Any]],
    predictions: List[float],
) -> List[Dict]:
    """
    Generate a plain-language explanation for each predicted value.

    Args:
        tenant_id:   Load the correct model for this tenant.
        input_data:  The same rows passed to predictor.predict().
        predictions: The prediction values returned by predictor.predict().

    Returns:
        List of explanation dicts, one per input row:
        {
            "prediction":      float,
            "top_drivers":     [{"feature": str, "impact": float}, ...],
            "summary":         str   ← human-readable plain-English explanation
        }
    """
    settings = get_settings()
    model, metadata = load_model(tenant_id)
    training_columns: List[str] = metadata["feature_columns"]
    target_column: str = metadata["target_column"]

    # Build aligned input DataFrame (same as predictor does)
    df_input = pd.DataFrame(input_data)
    for col in df_input.columns:
        if df_input[col].dtype == object:
            df_input[col] = df_input[col].fillna("unknown")
        else:
            df_input[col] = df_input[col].fillna(df_input[col].median())

    df_encoded = pd.get_dummies(df_input, drop_first=True)
    for col in training_columns:
        if col not in df_encoded.columns:
            df_encoded[col] = 0
    df_aligned = df_encoded[training_columns]

    # Extract the underlying estimator from the sklearn Pipeline
    pipeline: Pipeline = model
    estimator = pipeline.named_steps["model"]
    scaler = pipeline.named_steps["scaler"]
    X_scaled = scaler.transform(df_aligned)
    X_scaled_df = pd.DataFrame(X_scaled, columns=training_columns)

    # Choose the right SHAP explainer based on model type
    model_type = metadata.get("model_type", "random_forest")
    if model_type in ("random_forest", "gradient_boosting"):
        explainer = shap.TreeExplainer(
            estimator,
            data=shap.sample(X_scaled_df, settings.shap_background_samples),
        )
    else:
        # Linear regression — use LinearExplainer
        explainer = shap.LinearExplainer(
            estimator,
            masker=shap.maskers.Independent(X_scaled_df),
        )

    shap_values = explainer(X_scaled_df)

    results = []
    for i, (row_shap, prediction) in enumerate(zip(shap_values, predictions)):
        # Build sorted list of feature impacts
        impacts = [
            {"feature": col, "impact": round(float(val), 4)}
            for col, val in zip(training_columns, row_shap.values)
        ]
        impacts.sort(key=lambda x: abs(x["impact"]), reverse=True)
        top_drivers = impacts[:5]

        # Build a plain-English summary
        summary = _build_summary(target_column, prediction, top_drivers)

        results.append({
            "prediction": prediction,
            "top_drivers": top_drivers,
            "summary": summary,
        })

    return results


def _build_summary(target_column: str, prediction: float, top_drivers: List[Dict]) -> str:
    """Format top SHAP drivers into a readable sentence."""
    parts = []
    for driver in top_drivers[:3]:
        direction = "increased" if driver["impact"] > 0 else "decreased"
        parts.append(
            f"'{driver['feature']}' {direction} the prediction "
            f"by {abs(driver['impact']):,.2f}"
        )

    drivers_text = "; ".join(parts) if parts else "no dominant features identified"
    return (
        f"Predicted {target_column}: {prediction:,.2f}. "
        f"Key factors: {drivers_text}."
    )
