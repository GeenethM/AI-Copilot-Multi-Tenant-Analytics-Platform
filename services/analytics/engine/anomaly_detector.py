"""
anomaly_detector.py
───────────────────
Flags data points that deviate significantly from the expected range.

Method: Z-score detection
  For each value in a numeric column, compute how many standard deviations
  it is from the column mean. Values beyond the threshold are flagged.

  z_score = (value - mean) / std_dev

  A z-score of ±2.5 means the value is in the outermost ~1.2% of the
  distribution — very likely an outlier worth investigating.

Why this matters:
  - A sudden spike in returns could indicate a product defect.
  - An unexpectedly low sales figure might mean a reporting error.
  - Anomaly alerts let business teams catch problems early.
"""

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from config.settings import get_settings


def detect_anomalies(
    df: pd.DataFrame,
    numeric_columns: Optional[List[str]] = None,
    date_column: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Detect anomalies across all (or specified) numeric columns.

    Args:
        df:              The tenant's DataFrame.
        numeric_columns: Which columns to scan. Defaults to all numeric columns.
        date_column:     If provided, included in the anomaly row output
                         so the caller knows *when* the anomaly occurred.

    Returns:
        Dict with:
          "anomalies"       — list of anomaly dicts (one per flagged data point)
          "total_anomalies" — integer count
          "columns_scanned" — list of column names that were checked
    """
    settings = get_settings()
    threshold = settings.anomaly_z_score_threshold

    if numeric_columns:
        cols = [c for c in numeric_columns if c in df.columns]
    else:
        cols = list(df.select_dtypes(include="number").columns)

    anomalies: List[Dict] = []

    for col in cols:
        series = df[col].dropna()

        if len(series) < 3:
            # Need at least 3 points to compute a meaningful z-score
            continue

        col_mean = series.mean()
        col_std = series.std()

        if col_std == 0:
            # All values are identical — no variation to flag
            continue

        z_scores = (df[col] - col_mean) / col_std

        flagged_indices = z_scores[z_scores.abs() > threshold].index

        for idx in flagged_indices:
            value = df.loc[idx, col]
            z = z_scores.loc[idx]
            row: Dict[str, Any] = {
                "row_index":   int(idx),
                "column":      col,
                "value":       round(float(value), 4),
                "z_score":     round(float(z), 4),
                "direction":   "HIGH" if z > 0 else "LOW",
                "severity":    _classify_severity(abs(float(z)), threshold),
            }
            if date_column and date_column in df.columns:
                row["date"] = str(df.loc[idx, date_column])
            anomalies.append(row)

    # Sort by severity (highest z-score first)
    anomalies.sort(key=lambda x: abs(x["z_score"]), reverse=True)

    return {
        "anomalies":       anomalies,
        "total_anomalies": len(anomalies),
        "columns_scanned": cols,
    }


def _classify_severity(abs_z: float, threshold: float) -> str:
    if abs_z >= threshold * 2:
        return "CRITICAL"
    if abs_z >= threshold * 1.5:
        return "HIGH"
    return "MEDIUM"
