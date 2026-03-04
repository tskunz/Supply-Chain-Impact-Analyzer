"""
Data collection module — Supply Chain Event Impact Analyzer.

Fetches commodity price time series from the FRED API, validates data quality,
and provides the canonical commodity catalog.

Usage:
    fred = build_fred_client(api_key)
    df   = get_commodity_data(fred, "DCOILBRENTEU", start_date, end_date)
"""

from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd
import streamlit as st
from fredapi import Fred

# ── Commodity catalog ──────────────────────────────────────────────────────────
# FRED codes from commodity_indicators.md — DO NOT change without checking the ref doc.

COMMODITIES: dict[str, dict] = {
    "crude_oil_brent": {
        "code": "DCOILBRENTEU",
        "name": "Crude Oil (Brent)",
        "units": "USD/Barrel",
        "frequency": "daily",
        "priority": 1,
    },
    "natural_gas": {
        "code": "DHHNGSP",
        "name": "Natural Gas (Henry Hub)",
        "units": "USD/MMBtu",
        "frequency": "daily",
        "priority": 2,
    },
    "copper": {
        "code": "PCOPPUSDM",
        "name": "Copper",
        "units": "USD/Metric Ton",
        "frequency": "monthly",
        "priority": 3,
    },
    "aluminum": {
        "code": "PALUMUSDM",
        "name": "Aluminum",
        "units": "USD/Metric Ton",
        "frequency": "monthly",
        "priority": 4,
    },
    "iron_ore": {
        "code": "PIORECRUSDM",
        "name": "Iron Ore",
        "units": "USD/Dry Metric Ton",
        "frequency": "monthly",
        "priority": 5,
    },
}

# Commodities that report monthly — need ≥90-day windows for statistical validity.
# Source: commodity_indicators.md "Monthly Data + Short Window Warning"
MONTHLY_COMMODITIES: set[str] = {
    "copper", "aluminum", "iron_ore", "nickel", "zinc",
    "wheat", "corn", "soybeans", "coal",
}


# ── Window compatibility check ─────────────────────────────────────────────────

def check_window_compatibility(commodity_key: str, window_days: int) -> tuple[bool, str | None]:
    """
    Check whether the analysis window is long enough for the commodity's data frequency.

    Monthly series require ≥90-day windows to have sufficient data points (≥10)
    for statistical validity. A 30-day window yields only 1–2 monthly data points.

    Parameters
    ----------
    commodity_key : str
        Key from the COMMODITIES dict (e.g. 'copper').
    window_days : int
        Analysis window in days.

    Returns
    -------
    tuple[bool, str | None]
        (True, None) if compatible; (False, warning_message) if not.
    """
    if commodity_key in MONTHLY_COMMODITIES and window_days < 90:
        name = COMMODITIES.get(commodity_key, {}).get("name", commodity_key)
        return False, (
            f"**{name}** is a monthly series. "
            f"A {window_days}-day window yields too few data points for analysis "
            f"(need ≥90 days for monthly data, or use a daily series like Brent Crude / Natural Gas)."
        )
    return True, None


# ── Core data fetcher ──────────────────────────────────────────────────────────

def get_commodity_data(
    fred_client: Fred,
    indicator_code: str,
    start_date: date,
    end_date: date,
) -> Optional[pd.DataFrame]:
    """
    Fetch a commodity price series from the FRED API.

    Returns a DataFrame with a DatetimeIndex and a single 'price' column.
    Gaps up to 5 consecutive days are forward-filled (weekends, holidays).

    Parameters
    ----------
    fred_client : Fred
        Initialised fredapi.Fred client.
    indicator_code : str
        FRED series identifier, e.g. 'DCOILBRENTEU'.
    start_date : date
        Inclusive start of the fetch window.
    end_date : date
        Inclusive end of the fetch window.

    Returns
    -------
    pd.DataFrame | None
        DataFrame with DatetimeIndex and 'price' column, or None on failure.

    Raises
    ------
    Displays st.error / st.warning in the Streamlit UI on data quality issues.
    """
    try:
        raw = fred_client.get_series(
            indicator_code,
            observation_start=start_date.isoformat(),
            observation_end=end_date.isoformat(),
        )
    except Exception as exc:
        st.error(f"Failed to fetch **{indicator_code}** from FRED: {exc}")
        return None

    if raw is None or raw.empty:
        st.error(f"No data returned for **{indicator_code}** in the requested date range.")
        return None

    df = raw.rename("price").to_frame()
    df.index = pd.to_datetime(df.index)
    df.index.name = "date"
    df = df.sort_index()

    # Forward-fill gaps up to 5 trading days (weekends, public holidays, reporting delays)
    df["price"] = df["price"].ffill(limit=5)

    remaining_na = int(df["price"].isna().sum())
    if remaining_na > 0:
        st.warning(
            f"**{indicator_code}**: {remaining_na} data point(s) still missing after "
            f"forward-fill. Data quality may affect analysis."
        )

    return df


# ── Client factory ─────────────────────────────────────────────────────────────

def build_fred_client(api_key: str) -> Fred:
    """
    Create and return a configured fredapi.Fred client.

    Parameters
    ----------
    api_key : str
        FRED API key (never hardcode — read from st.secrets).

    Returns
    -------
    fredapi.Fred
    """
    return Fred(api_key=api_key)
