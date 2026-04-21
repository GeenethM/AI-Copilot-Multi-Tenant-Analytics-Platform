"""
trend_detector.py
─────────────────
Detects trends in a time-series numeric column:
  - Rolling averages (smoothed trend line)
  - Period-over-period % change (MoM, QoQ, YoY)
  - Direction classification: GROWING / DECLINING / STABLE

These are the numbers that power dashboard trend charts and decision
support narratives ("Revenue is up +14.2% month-over-month").
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from config.settings import get_settings


def detect_trends(
    df: pd.DataFrame,
    value_column: str,
    date_column: Optional[str] = None,
    period: str = "M",
) -> Dict[str, Any]:
    """
    Detect trends for a numeric column.

    Args:
        df:           The tenant's DataFrame.
        value_column: The numeric column to analyse (e.g. "revenue").
        date_column:  Optional date column. If provided, the analysis is
                      time-ordered and period-aggregated before analysis.
        period:       Aggregation period when date_column is provided.
                      "M" = monthly, "Q" = quarterly, "Y" = yearly.

    Returns:
        Dict with:
          "rolling_average"    — smoothed values list
          "period_over_period" — list of {period, value, change_pct} dicts
          "direction"          — "GROWING" | "DECLINING" | "STABLE"
          "latest_change_pct"  — most recent period-over-period % change
    """
    settings = get_settings()

    if value_column not in df.columns:
        raise ValueError(f"Column '{value_column}' not found in data.")

    # ── Time-order and aggregate if a date column is available ────────────────
    if date_column and date_column in df.columns:
        df_copy = df[[date_column, value_column]].copy()
        df_copy[date_column] = pd.to_datetime(df_copy[date_column], errors="coerce")
        df_copy = df_copy.dropna(subset=[date_column])
        df_copy["_period"] = df_copy[date_column].dt.to_period(period).astype(str)
        series = (
            df_copy.groupby("_period")[value_column]
            .sum()
            .reset_index(name=value_column)
        )
        labels = series["_period"].tolist()
        values = series[value_column].tolist()
    else:
        # No date column — treat rows as ordered observations
        values = df[value_column].dropna().tolist()
        labels = list(range(len(values)))

    if len(values) < 2:
        return {
            "rolling_average": values,
            "period_over_period": [],
            "direction": "STABLE",
            "latest_change_pct": None,
        }

    # ── Rolling average ───────────────────────────────────────────────────────
    s = pd.Series(values)
    rolling = (
        s.rolling(window=min(settings.rolling_window, len(values)), min_periods=1)
        .mean()
        .round(4)
        .tolist()
    )

    # ── Period-over-period % change ───────────────────────────────────────────
    pop: List[Dict] = []
    for i in range(1, len(values)):
        prev = values[i - 1]
        curr = values[i]
        if prev and prev != 0:
            change_pct = round((curr - prev) / abs(prev) * 100, 2)
        else:
            change_pct = None
        pop.append({
            "period":     str(labels[i]),
            "value":      round(float(curr), 4),
            "change_pct": change_pct,
        })

    # ── Direction ─────────────────────────────────────────────────────────────
    latest_change_pct = pop[-1]["change_pct"] if pop else None
    direction = _classify_direction(latest_change_pct)

    return {
        "rolling_average":    rolling,
        "period_over_period": pop,
        "direction":          direction,
        "latest_change_pct":  latest_change_pct,
    }


def _classify_direction(change_pct: Optional[float]) -> str:
    if change_pct is None:
        return "STABLE"
    if change_pct > 2.0:
        return "GROWING"
    if change_pct < -2.0:
        return "DECLINING"
    return "STABLE"
