"""
Event analysis module — Supply Chain Event Impact Analyzer.

Computes before/after statistics using log returns methodology.
All formulas follow statistical_methods.md exactly — do not invent new ones.

Core function: analyze_event_impact()
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats


# ── Analysis window helper ─────────────────────────────────────────────────────

def build_analysis_windows(
    commodity_data: pd.DataFrame,
    event_date: date | datetime,
    window_days: int = 30,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Slice before/after windows from commodity_data around event_date.

    before window: [event_date - window_days, event_date - 1]
    after  window: [event_date, event_date + window_days]

    Parameters
    ----------
    commodity_data : pd.DataFrame
        Full price DataFrame (DatetimeIndex, 'price' column).
    event_date : date | datetime
        The supply chain disruption event date.
    window_days : int
        Number of days on each side of the event.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        (before_data, after_data)
    """
    if isinstance(event_date, date) and not isinstance(event_date, datetime):
        event_dt = datetime.combine(event_date, datetime.min.time())
    else:
        event_dt = event_date

    before_start = event_dt - timedelta(days=window_days)
    before_end   = event_dt - timedelta(days=1)
    after_start  = event_dt
    after_end    = event_dt + timedelta(days=window_days)

    before_data = commodity_data.loc[
        (commodity_data.index >= before_start) &
        (commodity_data.index <= before_end)
    ].copy()

    after_data = commodity_data.loc[
        (commodity_data.index >= after_start) &
        (commodity_data.index <= after_end)
    ].copy()

    return before_data, after_data


# ── Data validation ────────────────────────────────────────────────────────────

def validate_window_data(
    before_data: pd.DataFrame,
    after_data: pd.DataFrame,
) -> tuple[bool, str | None]:
    """
    Validate that before/after windows have sufficient, clean data.

    Parameters
    ----------
    before_data : pd.DataFrame
    after_data : pd.DataFrame

    Returns
    -------
    tuple[bool, str | None]
        (True, None) if valid; (False, error_message) if not.
    """
    if len(before_data) < 10:
        return False, (
            f"Insufficient before-event data: {len(before_data)} point(s) "
            f"(need ≥10). Try increasing the analysis window or checking the date range."
        )
    if len(after_data) < 10:
        return False, (
            f"Insufficient after-event data: {len(after_data)} point(s) "
            f"(need ≥10). Try increasing the analysis window."
        )

    total   = len(before_data) + len(after_data)
    missing = int(before_data["price"].isna().sum() + after_data["price"].isna().sum())
    if total > 0 and (missing / total) > 0.2:
        return False, (
            f"Excessive missing data: {missing / total * 100:.1f}% "
            f"(max 20%). Check data quality for this series and date range."
        )

    return True, None


# ── Outlier detection (flag only — never remove) ──────────────────────────────

def detect_outliers(data: pd.DataFrame) -> pd.DataFrame:
    """
    Return rows where the absolute z-score of 'price' exceeds 3.

    DO NOT remove outliers — supply chain shocks create legitimate extreme values
    (e.g. negative WTI futures in April 2020). Flag and inform only.

    Parameters
    ----------
    data : pd.DataFrame
        Must have a 'price' column.

    Returns
    -------
    pd.DataFrame
        Subset of rows that are statistical outliers (may be empty).
    """
    if len(data) < 4:
        return pd.DataFrame()

    mean  = data["price"].mean()
    std   = data["price"].std()
    if std == 0 or pd.isna(std):
        return pd.DataFrame()

    z_scores = (data["price"] - mean).abs() / std
    return data[z_scores > 3]


# ── Core analysis function ─────────────────────────────────────────────────────

def analyze_event_impact(
    commodity_data: pd.DataFrame,
    event_date: date | datetime,
    window_days: int = 30,
    event_type: str = "general",
) -> dict | None:
    """
    Perform a before/after event study on a commodity price series.

    Step 0: Compute log returns (R_t = ln(P_t / P_{t-1})) on the full series.
    Then slice before/after windows and compute all five metrics.

    Parameters
    ----------
    commodity_data : pd.DataFrame
        DatetimeIndex DataFrame with a 'price' column.
    event_date : date | datetime
        The supply chain disruption date.
    window_days : int
        Analysis window in days on each side of the event (default 30).
    event_type : str
        One of: 'general', 'geopolitical', 'maritime', 'pandemic', 'financial'.
        Maritime events apply the Zhao-Tsinghua hysteresis multiplier (1.73×)
        to the recovery timeline.

    Returns
    -------
    dict | None
        Analysis metrics dict, or dict with 'error' key if data is insufficient.

    Keys
    ----
    avg_price_change_pct    : float   — (μ_after - μ_before) / μ_before × 100
    peak_impact_pct         : float   — max % deviation from pre-event baseline
    peak_date               : Timestamp
    days_to_peak            : int
    volatility_change_pct   : float | None
    recovery_days           : int | None — None if not recovered within window
    pre_event_avg           : float
    post_event_avg          : float
    log_return_mean_before  : float
    log_return_mean_after   : float
    log_return_std_before   : float
    log_return_std_after    : float
    p_value                 : float   — Welch's t-test p-value
    is_significant          : bool    — p < 0.05
    before_data             : pd.DataFrame
    after_data              : pd.DataFrame
    """
    # ── Step 0: Log returns transformation ────────────────────────────────────
    # Apply FIRST — required before computing any metric.
    # R_t = ln(P_t / P_{t-1})
    data = commodity_data.copy()
    data["log_return"] = np.log(data["price"] / data["price"].shift(1))

    # ── Slice windows ──────────────────────────────────────────────────────────
    before_data, after_data = build_analysis_windows(data, event_date, window_days)

    # ── Validate ───────────────────────────────────────────────────────────────
    valid, err = validate_window_data(before_data, after_data)
    if not valid:
        return {"error": err}

    # Normalise event_date to datetime for arithmetic
    if isinstance(event_date, date) and not isinstance(event_date, datetime):
        event_dt = datetime.combine(event_date, datetime.min.time())
    else:
        event_dt = event_date

    # ── Metric 1: Average Price Change ────────────────────────────────────────
    # Δ% = (μ_after - μ_before) / μ_before × 100
    before_mean: float = float(before_data["price"].mean())
    after_mean:  float = float(after_data["price"].mean())

    if before_mean == 0:
        return {"error": "Pre-event mean price is zero — invalid baseline."}

    avg_price_change_pct: float = ((after_mean - before_mean) / before_mean) * 100.0

    # ── Metric 2: Peak Impact ─────────────────────────────────────────────────
    # Positive shock → find max price; negative shock → find min price.
    if after_mean >= before_mean:
        peak_price = float(after_data["price"].max())
        peak_date  = after_data["price"].idxmax()
    else:
        peak_price = float(after_data["price"].min())
        peak_date  = after_data["price"].idxmin()

    peak_impact_pct: float = ((peak_price - before_mean) / before_mean) * 100.0
    days_to_peak: int = max(0, (peak_date - pd.Timestamp(event_dt)).days)

    # ── Metric 3: Volatility Change ───────────────────────────────────────────
    # Volatility Change % = (σ_after - σ_before) / σ_before × 100
    before_std: float = float(before_data["price"].std())
    after_std:  float = float(after_data["price"].std())

    if before_std == 0 or pd.isna(before_std):
        volatility_change_pct: float | None = None
    else:
        volatility_change_pct = ((after_std - before_std) / before_std) * 100.0

    # ── Metric 4: Recovery Timeline ───────────────────────────────────────────
    # Recovery: price re-enters pre-event mean ± 1 std dev.
    lower_bound = before_mean - before_std
    upper_bound = before_mean + before_std

    recovered = after_data[
        (after_data["price"] >= lower_bound) &
        (after_data["price"] <= upper_bound)
    ]

    recovery_days: int | None = None
    if len(recovered) > 0:
        recovery_date = recovered.index[0]
        recovery_days = int((recovery_date - pd.Timestamp(event_dt)).days)

    # Zhao-Tsinghua hysteresis buffer for maritime events (1.73× multiplier)
    # Source: statistical_methods.md — Metric 4 / Recovery Timeline
    if event_type == "maritime" and recovery_days is not None:
        recovery_days = round(recovery_days * 1.73)

    # ── Metric 5: Log Return Statistics ──────────────────────────────────────
    log_return_mean_before = float(before_data["log_return"].mean())
    log_return_mean_after  = float(after_data["log_return"].mean())
    log_return_std_before  = float(before_data["log_return"].std())
    log_return_std_after   = float(after_data["log_return"].std())

    # ── Stretch: Statistical Significance (Welch's t-test) ───────────────────
    # Does not assume equal variance — appropriate for before/after price windows.
    t_stat, p_value = stats.ttest_ind(
        before_data["price"].dropna(),
        after_data["price"].dropna(),
        equal_var=False,
    )
    is_significant: bool = bool(float(p_value) < 0.05)

    return {
        "avg_price_change_pct":   avg_price_change_pct,
        "peak_impact_pct":        peak_impact_pct,
        "peak_date":              peak_date,
        "days_to_peak":           days_to_peak,
        "volatility_change_pct":  volatility_change_pct,
        "recovery_days":          recovery_days,
        "pre_event_avg":          before_mean,
        "post_event_avg":         after_mean,
        "log_return_mean_before": log_return_mean_before,
        "log_return_mean_after":  log_return_mean_after,
        "log_return_std_before":  log_return_std_before,
        "log_return_std_after":   log_return_std_after,
        "p_value":                float(p_value),
        "is_significant":         is_significant,
        "before_data":            before_data,
        "after_data":             after_data,
    }
