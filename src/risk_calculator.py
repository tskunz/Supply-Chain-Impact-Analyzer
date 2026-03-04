"""
Risk calculation module — Supply Chain Event Impact Analyzer.

Implements:
  - Composite Risk Score (0–100) from statistical_methods.md
  - Zhao-Tsinghua Nonlinear Loss Rule for maritime events (Zhao et al., 2024)

All constants sourced from academic_benchmarks.md — do not modify without flagging.
"""

from __future__ import annotations

import math

# ── Academic constants — DO NOT modify without flagging ───────────────────────

# Zhao et al. (2024) — Nonlinear Loss Rule
# Source: "Modeling the dynamic impacts of maritime network blockage", The Innovation
DAILY_TRADE_VALUE_USD         = 58_600_000_000   # $58.6B daily seaborne trade (2021)
MARITIME_LOSS_COEFFICIENT     = 0.12             # Base loss: 12% of daily trade value
MARITIME_EXPONENTIAL_RATE     = 0.10             # Nonlinear growth rate per day blocked
MARITIME_RECOVERY_HYSTERESIS  = 1.73             # Highly utilized chokepoints recovery multiplier

# Sarwar & Rye (2025) — Geopolitical Energy Premium
GEOPOLITICAL_OIL_PREMIUM_LOW  = 15.0    # % minimum immediate Brent spike
GEOPOLITICAL_OIL_PREMIUM_HIGH = 25.0    # % maximum immediate Brent spike
GEOPOLITICAL_RECOVERY_DAYS    = 52.5    # Midpoint of 45–60 day stabilization floor

# Schmitt et al. (2015) — Firm-Level Baselines (Sandia National Labs)
FIRM_VOLATILITY_INCREASE_AVG  = 13.5    # % average share-price volatility increase
FIRM_RECOVERY_FRACTION        = 0.36    # Share of firms taking >30 days to recover
FIRM_OPERATING_INCOME_IMPACT  = -107.0  # % average operating income change


# ── Zhao-Tsinghua Nonlinear Loss Rule ─────────────────────────────────────────

def calculate_nonlinear_maritime_loss(days_blocked: int) -> dict:
    """
    Apply the Zhao-Tsinghua Nonlinear Loss Rule for maritime blockage events.

    Formula: Loss = (Daily_Trade_Value × 0.12) × e^(0.1 × Days_Blocked)

    Losses scale nonlinearly — a 12-day blockage does NOT cost twice a 6-day blockage.
    Risk compounds exponentially with blockage duration.

    Source: Zhao et al. (2024), "Modeling the dynamic impacts of maritime network
    blockage on global supply chains", The Innovation, 5(4).

    Parameters
    ----------
    days_blocked : int
        Number of days the maritime chokepoint is blocked (must be > 0).

    Returns
    -------
    dict with keys:
        estimated_global_loss_usd : float  — estimated economic loss in USD
        estimated_recovery_days   : int    — recovery time with 1.73× hysteresis
        days_blocked              : int
        methodology               : str    — citation string

    Raises
    ------
    ValueError if days_blocked <= 0.
    """
    if days_blocked <= 0:
        raise ValueError(f"days_blocked must be a positive integer, got {days_blocked}")

    estimated_loss = (DAILY_TRADE_VALUE_USD * MARITIME_LOSS_COEFFICIENT) * math.exp(
        MARITIME_EXPONENTIAL_RATE * days_blocked
    )
    estimated_recovery_days = round(days_blocked * MARITIME_RECOVERY_HYSTERESIS)

    return {
        "estimated_global_loss_usd": estimated_loss,
        "estimated_recovery_days":   estimated_recovery_days,
        "days_blocked":              days_blocked,
        "methodology":               "Zhao-Tsinghua Nonlinear Loss Rule (Zhao et al., 2024)",
    }


# ── Composite Risk Score ───────────────────────────────────────────────────────

def calculate_composite_risk_score(
    peak_impact_pct: float,
    days_to_peak: int,
    volatility_change_pct: float | None,
    recovery_days: int | None,
) -> dict:
    """
    Calculate the composite supply chain risk score on a 0–100 scale.

    Score = Price Impact (0–40)
          + Speed to Peak (0–20)
          + Volatility    (0–20)
          + Recovery      (0–20)

    Source: statistical_methods.md — Composite Risk Score section.

    Parameters
    ----------
    peak_impact_pct : float
        Maximum percentage deviation from pre-event baseline (signed).
    days_to_peak : int
        Days from event date to peak impact.
    volatility_change_pct : float | None
        Percentage change in price standard deviation; None if uncomputable.
    recovery_days : int | None
        Days until price re-enters pre-event ±1σ range; None if not recovered.

    Returns
    -------
    dict with keys:
        score      : int        — 0–100
        level      : str        — LOW / MODERATE / HIGH / CRITICAL
        level_color: str        — green / orange / red / darkred
        components : dict       — breakdown of each sub-score
    """
    # Component 1: Price Impact (0–40)
    # min(|peak_impact_pct| × 2, 40)
    price_component = min(abs(peak_impact_pct) * 2.0, 40.0)

    # Component 2: Speed to Peak (0–20)
    if days_to_peak < 7:
        speed_component = 20.0
    elif days_to_peak <= 14:
        speed_component = 15.0
    elif days_to_peak <= 30:
        speed_component = 10.0
    else:
        speed_component = 5.0

    # Component 3: Volatility (0–20)
    # min(|volatility_change_pct| / 5, 20)
    if volatility_change_pct is None:
        vol_component = 0.0
    else:
        vol_component = min(abs(volatility_change_pct) / 5.0, 20.0)

    # Component 4: Recovery (0–20)
    if recovery_days is None:
        rec_component = 20.0        # Not recovered within window
    elif recovery_days > 90:
        rec_component = 15.0
    elif recovery_days >= 60:
        rec_component = 10.0
    elif recovery_days >= 30:
        rec_component = 5.0
    else:
        rec_component = 0.0         # Fast recovery < 30 days

    score = round(price_component + speed_component + vol_component + rec_component)
    score = max(0, min(100, score))  # clamp to [0, 100]

    # Risk level thresholds from statistical_methods.md
    if score <= 25:
        level = "LOW"
        level_color = "green"
    elif score <= 50:
        level = "MODERATE"
        level_color = "orange"
    elif score <= 75:
        level = "HIGH"
        level_color = "red"
    else:
        level = "CRITICAL"
        level_color = "darkred"

    return {
        "score":       score,
        "level":       level,
        "level_color": level_color,
        "components": {
            "price_impact":  round(price_component, 1),
            "speed_to_peak": round(speed_component, 1),
            "volatility":    round(vol_component, 1),
            "recovery":      round(rec_component, 1),
        },
    }


# ── Magnitude label helper ─────────────────────────────────────────────────────

def price_change_label(pct: float) -> str:
    """
    Return a human-readable magnitude label for a price change percentage.

    Parameters
    ----------
    pct : float
        Signed percentage change (e.g. 22.3 for +22.3%, -15.0 for -15%).

    Returns
    -------
    str
        e.g. 'Major (+22.3%)' or 'Moderate (-15.0%)'
    """
    abs_pct = abs(pct)
    sign    = "+" if pct >= 0 else ""

    if abs_pct < 5:
        label = "Minor"
    elif abs_pct <= 15:
        label = "Moderate"
    else:
        label = "Major"

    return f"{label} ({sign}{pct:.1f}%)"
