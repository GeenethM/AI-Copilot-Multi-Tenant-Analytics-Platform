"""
aggregator.py
─────────────
Computes KPIs (Key Performance Indicators) from a tenant's DataFrame.

KPIs produced per numeric column:
  - total      : sum of all values
  - mean       : average value
  - median     : middle value (more robust to outliers than mean)
  - min / max  : range of values
  - std_dev    : spread / volatility
  - count      : number of non-null data points

If a date/time column is present the aggregator also computes period-over-period
breakdowns (e.g. monthly totals) for each numeric column.
"""

from typing import Any, Dict, List, Optional

import pandas as pd


def compute_kpis(
    df: pd.DataFrame,
    numeric_columns: Optional[List[str]] = None,
    date_column: Optional[str] = None,
    group_by_column: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compute KPIs for a DataFrame.

    Args:
        df:               The tenant's data as a pandas DataFrame.
        numeric_columns:  Which columns to compute KPIs for. Uses all numeric
                          columns if not specified.
        date_column:      Optional. If provided, also compute monthly totals.
        group_by_column:  Optional. If provided, break KPIs down by this column
                          (e.g. "region", "product_category").

    Returns:
        Dict with keys:
          "overall_kpis"  — summary stats per numeric column
          "monthly"       — monthly totals per column (if date_column provided)
          "by_group"      — per-group breakdown (if group_by_column provided)
    """
    # Resolve which numeric columns to analyse
    if numeric_columns:
        cols = [c for c in numeric_columns if c in df.columns]
    else:
        cols = list(df.select_dtypes(include="number").columns)

    if not cols:
        return {"overall_kpis": {}, "monthly": None, "by_group": None}

    # ── Overall KPIs ──────────────────────────────────────────────────────────
    overall: Dict[str, Dict] = {}
    for col in cols:
        series = df[col].dropna()
        overall[col] = {
            "total":   round(float(series.sum()), 4),
            "mean":    round(float(series.mean()), 4),
            "median":  round(float(series.median()), 4),
            "min":     round(float(series.min()), 4),
            "max":     round(float(series.max()), 4),
            "std_dev": round(float(series.std()), 4),
            "count":   int(series.count()),
        }

    # ── Monthly breakdown ─────────────────────────────────────────────────────
    monthly = None
    if date_column and date_column in df.columns:
        try:
            df_copy = df.copy()
            df_copy[date_column] = pd.to_datetime(df_copy[date_column], errors="coerce")
            df_copy = df_copy.dropna(subset=[date_column])
            df_copy["_period"] = df_copy[date_column].dt.to_period("M").astype(str)
            monthly_df = (
                df_copy.groupby("_period")[cols].sum().reset_index()
            )
            monthly = monthly_df.to_dict(orient="records")
        except Exception:
            monthly = None

    # ── Group breakdown ───────────────────────────────────────────────────────
    by_group = None
    if group_by_column and group_by_column in df.columns:
        try:
            group_df = df.groupby(group_by_column)[cols].sum().reset_index()
            by_group = group_df.to_dict(orient="records")
        except Exception:
            by_group = None

    return {
        "overall_kpis": overall,
        "monthly":      monthly,
        "by_group":     by_group,
    }
