"""
Supply Chain Event Impact Analyzer — Streamlit Dashboard.

Main entry point. Run from the project root:
    streamlit run src/app.py

Analyst's Shield: All events are treated as standardized data triggers
(transit closures, energy premiums, demand shocks, financial contagion).
This is operational supply chain research, not political commentary.
"""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from io import StringIO

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from fredapi import Fred

# Ensure src/ is on sys.path for sibling imports (works locally and on Streamlit Cloud)
sys.path.insert(0, os.path.dirname(__file__))

from data_collector import (
    COMMODITIES,
    build_fred_client,
    check_window_compatibility,
    get_commodity_data,
)
from event_analyzer import analyze_event_impact, detect_outliers
from risk_calculator import (
    calculate_composite_risk_score,
    calculate_nonlinear_maritime_loss,
    price_change_label,
)

# ── Pre-loaded example events ──────────────────────────────────────────────────
# Source: historical_events.md — Streamlit Pre-loaded Events Dictionary

EXAMPLE_EVENTS: dict[str, dict | None] = {
    "— select an example —": None,
    "Ukraine Invasion (Feb 2022)": {
        "date":        date(2022, 2, 24),
        "event_type":  "geopolitical",
        "commodities": ["crude_oil_brent", "natural_gas", "copper"],
        "window":      30,
    },
    "COVID-19 Lockdowns (Mar 2020)": {
        "date":        date(2020, 3, 15),
        "event_type":  "pandemic",
        "commodities": ["crude_oil_brent", "copper", "natural_gas"],
        "window":      45,
    },
    "Suez Canal Blockage (Mar 2021)": {
        "date":        date(2021, 3, 23),
        "event_type":  "maritime",
        "commodities": ["crude_oil_brent", "natural_gas"],
        "window":      15,
    },
    "2008 Financial Crisis (Sep 2008)": {
        "date":        date(2008, 9, 15),
        "event_type":  "financial",
        "commodities": ["crude_oil_brent", "copper", "aluminum"],
        "window":      90,
    },
    "Red Sea Disruptions (Dec 2023)": {
        "date":        date(2023, 12, 1),
        "event_type":  "maritime",
        "commodities": ["crude_oil_brent", "natural_gas"],
        "window":      30,
    },
}

EVENT_TYPE_OPTIONS: dict[str, str] = {
    "geopolitical": "Geopolitical — conflict, sanctions, embargo",
    "maritime":     "Maritime — shipping obstruction, port closure",
    "pandemic":     "Pandemic — demand destruction, factory closure",
    "financial":    "Financial — credit crisis, recession trigger",
    "general":      "General",
}

RISK_BADGE: dict[str, str] = {
    "LOW":      "🟢 LOW",
    "MODERATE": "🟡 MODERATE",
    "HIGH":     "🟠 HIGH",
    "CRITICAL": "🔴 CRITICAL",
}

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Supply Chain Risk Analyzer",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── FRED API key ───────────────────────────────────────────────────────────────

try:
    api_key = st.secrets["FRED_API_KEY"]
except KeyError:
    st.error(
        "**FRED API key not found.**\n\n"
        "• **Local development:** add `FRED_API_KEY = \"your_key\"` to `.streamlit/secrets.toml`\n\n"
        "• **Streamlit Cloud:** add via App Settings → Secrets"
    )
    st.stop()

fred: Fred = build_fred_client(api_key)

# ── Header ─────────────────────────────────────────────────────────────────────

st.title("Supply Chain Event Impact Analyzer")
st.caption(
    "Quantitative risk analysis using real commodity price data (Federal Reserve FRED API). "
    "Measures the economic transmission of logistical shocks — not a news summarizer."
)
st.divider()

# ── Sidebar: Event Parameters ──────────────────────────────────────────────────

with st.sidebar:
    st.header("Event Parameters")

    # ── Example events dropdown ────────────────────────────────────────────────
    selected_example_key = st.selectbox(
        "Load example event",
        options=list(EXAMPLE_EVENTS.keys()),
    )
    example = EXAMPLE_EVENTS[selected_example_key]

    st.divider()

    # ── Event name ─────────────────────────────────────────────────────────────
    # Use a key that changes with example selection so the field auto-refreshes.
    default_name = (
        selected_example_key.split("(")[0].strip()
        if example else ""
    )
    event_name: str = st.text_input(
        "Event name",
        value=default_name,
        placeholder="e.g. Red Sea Disruptions",
        key=f"event_name_{selected_example_key}",
    )

    # ── Event date ─────────────────────────────────────────────────────────────
    default_date: date = example["date"] if example else date(2022, 2, 24)
    event_date: date = st.date_input(
        "Event date",
        value=default_date,
        min_value=date(1980, 1, 1),
        max_value=date.today(),
    )

    # ── Event type ─────────────────────────────────────────────────────────────
    type_keys = list(EVENT_TYPE_OPTIONS.keys())
    default_type_idx = (
        type_keys.index(example["event_type"])
        if example and example["event_type"] in type_keys
        else 0
    )
    event_type: str = st.selectbox(
        "Event type",
        options=type_keys,
        format_func=lambda k: EVENT_TYPE_OPTIONS[k],
        index=default_type_idx,
    )

    # ── Analysis window ────────────────────────────────────────────────────────
    default_window: int = example["window"] if example else 30
    window_days: int = st.slider(
        "Analysis window (days)",
        min_value=15,
        max_value=90,
        value=default_window,
        step=5,
        help="Days before/after the event date included in the analysis.",
    )

    # ── Commodity selection ────────────────────────────────────────────────────
    commodity_options = list(COMMODITIES.keys())
    default_commodities = (
        example["commodities"]
        if example
        else ["crude_oil_brent", "natural_gas"]
    )
    selected_commodities: list[str] = st.multiselect(
        "Commodities to analyze",
        options=commodity_options,
        default=default_commodities,
        format_func=lambda k: COMMODITIES[k]["name"],
    )

    # ── Maritime: days blocked ─────────────────────────────────────────────────
    days_blocked: int | None = None
    if event_type == "maritime":
        days_blocked = st.number_input(
            "Days blocked (Nonlinear Loss estimate)",
            min_value=1,
            max_value=365,
            value=6,
            help=(
                "Duration of the maritime blockage used for the "
                "Zhao-Tsinghua Nonlinear Loss model (Zhao et al., 2024)."
            ),
        )

    st.divider()
    run_analysis: bool = st.button(
        "Analyze", type="primary", use_container_width=True
    )

# ── Idle state ─────────────────────────────────────────────────────────────────

if not run_analysis:
    st.info(
        "Configure event parameters in the sidebar and click **Analyze**.\n\n"
        "Try a pre-loaded example to see the analyzer in action."
    )
    st.stop()

# ── Input validation ───────────────────────────────────────────────────────────

if not event_name.strip():
    st.error("Please enter an event name.")
    st.stop()

if not selected_commodities:
    st.error("Please select at least one commodity.")
    st.stop()

# ── Window compatibility check ─────────────────────────────────────────────────
# Monthly series (copper, aluminum, iron_ore) need ≥90-day windows.

compatible_commodities: list[str] = []
for key in selected_commodities:
    ok, msg = check_window_compatibility(key, window_days)
    if not ok:
        st.warning(f"**Window mismatch:** {msg}")
    else:
        compatible_commodities.append(key)

if not compatible_commodities:
    st.error(
        "No compatible commodities after window check. "
        "Increase the analysis window to ≥90 days or select daily-frequency commodities "
        "(Brent Crude, Natural Gas)."
    )
    st.stop()

# ── Fetch data and run analysis ────────────────────────────────────────────────

fetch_start = event_date - timedelta(days=window_days + 15)   # extra buffer for log returns
fetch_end   = event_date + timedelta(days=window_days + 15)

results: dict[str, dict] = {}

with st.spinner("Fetching commodity data from FRED…"):
    for key in compatible_commodities:
        meta = COMMODITIES[key]
        df = get_commodity_data(fred, meta["code"], fetch_start, fetch_end)
        if df is None:
            continue

        # Flag outliers (do not remove — they may be legitimate shock values)
        outliers = detect_outliers(df)
        if len(outliers) > 0:
            st.warning(
                f"**{meta['name']}**: {len(outliers)} potential outlier(s) detected "
                f"(|z-score| > 3). These are preserved — verify data quality for "
                f"extreme values in this series."
            )

        result = analyze_event_impact(df, event_date, window_days, event_type)

        if result is None or "error" in result:
            err_msg = result.get("error", "Unknown error") if result else "Unknown error"
            st.error(f"**{meta['name']}**: Analysis failed — {err_msg}")
            continue

        risk = calculate_composite_risk_score(
            peak_impact_pct=result["peak_impact_pct"],
            days_to_peak=result["days_to_peak"],
            volatility_change_pct=result["volatility_change_pct"],
            recovery_days=result["recovery_days"],
        )
        result["risk"] = risk
        result["meta"] = meta
        results[key] = result

if not results:
    st.error(
        "No results could be computed. "
        "Check your event date, analysis window, and commodity selection."
    )
    st.stop()

# ── Results header ─────────────────────────────────────────────────────────────

st.subheader(f"Results — {event_name}")
st.caption(
    f"Event date: **{event_date.strftime('%b %d, %Y')}** | "
    f"Type: **{EVENT_TYPE_OPTIONS[event_type]}** | "
    f"Window: **±{window_days} days**"
)

# ── Maritime: Nonlinear Loss estimate ─────────────────────────────────────────

if event_type == "maritime" and days_blocked:
    maritime_loss = calculate_nonlinear_maritime_loss(int(days_blocked))
    loss_b = maritime_loss["estimated_global_loss_usd"] / 1e9

    with st.expander(
        "Maritime Risk Estimate — Zhao-Tsinghua Nonlinear Loss Model",
        expanded=True,
    ):
        c1, c2, c3 = st.columns(3)
        c1.metric("Days Blocked", f"{maritime_loss['days_blocked']} days")
        c2.metric("Estimated Global Loss", f"${loss_b:.1f}B USD")
        c3.metric("Est. Recovery Time", f"{maritime_loss['estimated_recovery_days']} days")
        st.caption(
            "Formula: Loss = (Daily_Trade_Value × 0.12) × e^(0.1 × Days_Blocked) | "
            "Recovery multiplier: 1.73× (high-utilization chokepoints) | "
            "Source: Zhao et al. (2024), *The Innovation*, Tsinghua University"
        )

# ── Per-commodity results ──────────────────────────────────────────────────────

for key, result in results.items():
    meta      = result["meta"]
    risk      = result["risk"]
    before_df = result["before_data"]
    after_df  = result["after_data"]

    st.divider()
    st.subheader(meta["name"])

    # ── Metric columns ─────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    avg_pct  = result["avg_price_change_pct"]
    peak_pct = result["peak_impact_pct"]
    vol_pct  = result["volatility_change_pct"]
    rec_days = result["recovery_days"]
    score    = risk["score"]
    level    = risk["level"]

    c1.metric(
        "Avg Price Change",
        f"{avg_pct:+.1f}%",
        help="Mean price change: (μ_after − μ_before) / μ_before × 100",
    )
    c2.metric(
        "Peak Impact",
        f"{peak_pct:+.1f}%",
        help="Maximum % deviation from pre-event baseline.",
    )
    c3.metric(
        "Days to Peak",
        str(result["days_to_peak"]),
        help="Days from event date to maximum impact.",
    )
    c4.metric(
        "Volatility Δ",
        f"{vol_pct:+.1f}%" if vol_pct is not None else "N/A",
        help="Change in price standard deviation: (σ_after − σ_before) / σ_before × 100",
    )
    c5.metric(
        "Recovery",
        f"{rec_days} days" if rec_days is not None else "Not recovered",
        help="Days until price re-enters pre-event mean ± 1 std dev.",
    )
    c6.metric(
        "Risk Score",
        f"{score} / 100",
        delta=RISK_BADGE.get(level, level),
        delta_color="off",
        help="Composite score: Price Impact (40) + Speed (20) + Volatility (20) + Recovery (20)",
    )

    # Statistical significance note
    p_val = result["p_value"]
    sig_text = (
        f"Statistically significant (Welch's t-test, p = {p_val:.4f})"
        if result["is_significant"]
        else f"Not statistically significant (Welch's t-test, p = {p_val:.4f})"
    )
    st.caption(sig_text)

    # ── Plotly chart ───────────────────────────────────────────────────────────
    chart_df = pd.concat([before_df, after_df]).sort_index()

    fig = go.Figure()

    # Price line (blue, width 2)
    fig.add_trace(go.Scatter(
        x=chart_df.index,
        y=chart_df["price"],
        mode="lines",
        name=meta["name"],
        line=dict(color="steelblue", width=2),
        hovertemplate="%{x|%b %d, %Y}<br>Price: %{y:.2f} " + meta["units"] + "<extra></extra>",
    ))

    # Before window shading (gray)
    if len(before_df) > 0:
        fig.add_vrect(
            x0=before_df.index.min(),
            x1=before_df.index.max(),
            fillcolor="rgba(128,128,128,0.1)",
            line_width=0,
            annotation_text="Pre-event window",
            annotation_position="top left",
            annotation_font_size=11,
            annotation_font_color="gray",
        )

    # After window shading (blue)
    if len(after_df) > 0:
        fig.add_vrect(
            x0=after_df.index.min(),
            x1=after_df.index.max(),
            fillcolor="rgba(70,130,180,0.1)",
            line_width=0,
            annotation_text="Post-event window",
            annotation_position="top right",
            annotation_font_size=11,
            annotation_font_color="steelblue",
        )

    # Event date line (dashed red)
    fig.add_vline(
        x=pd.Timestamp(event_date),
        line_dash="dash",
        line_color="red",
        line_width=2,
        annotation_text=f"Event: {event_date.strftime('%b %d, %Y')}",
        annotation_position="top right",
        annotation_font_color="red",
        annotation_font_size=11,
    )

    # Peak impact line (dotted orange)
    fig.add_vline(
        x=result["peak_date"],
        line_dash="dot",
        line_color="darkorange",
        line_width=2,
        annotation_text=f"Peak: {peak_pct:+.1f}%",
        annotation_position="bottom right",
        annotation_font_color="darkorange",
        annotation_font_size=11,
    )

    # Pre-event mean (dotted gray horizontal)
    pre_avg = result["pre_event_avg"]
    fig.add_hline(
        y=pre_avg,
        line_dash="dot",
        line_color="gray",
        line_width=1,
        annotation_text=f"Pre-event mean: {pre_avg:.2f}",
        annotation_position="bottom right",
        annotation_font_color="gray",
        annotation_font_size=10,
    )

    fig.update_layout(
        title=dict(
            text=f"{meta['name']} — {event_name}",
            font=dict(size=15),
        ),
        xaxis_title="Date",
        yaxis_title=f"Price ({meta['units']})",
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.15),
        margin=dict(t=60, b=50, l=60, r=20),
        height=420,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(200,200,200,0.3)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(200,200,200,0.3)")

    st.plotly_chart(fig, use_container_width=True)

    # Risk score breakdown
    with st.expander("Risk score breakdown"):
        comps = risk["components"]
        bc1, bc2, bc3, bc4 = st.columns(4)
        bc1.metric("Price Impact",  f"{comps['price_impact']} / 40")
        bc2.metric("Speed to Peak", f"{comps['speed_to_peak']} / 20")
        bc3.metric("Volatility",    f"{comps['volatility']} / 20")
        bc4.metric("Recovery",      f"{comps['recovery']} / 20")
        st.caption(
            f"Magnitude: {price_change_label(peak_pct)} | "
            f"Log return mean before: {result['log_return_mean_before']:.5f} | "
            f"Log return mean after: {result['log_return_mean_after']:.5f}"
        )

# ── Multi-commodity summary table ─────────────────────────────────────────────

if len(results) > 1:
    st.divider()
    st.subheader("Multi-Commodity Comparison")

    rows = []
    for key, result in results.items():
        meta = result["meta"]
        risk = result["risk"]
        rows.append({
            "Commodity":        meta["name"],
            "Avg Change (%)":   f"{result['avg_price_change_pct']:+.1f}%",
            "Peak Impact (%)":  f"{result['peak_impact_pct']:+.1f}%",
            "Days to Peak":     result["days_to_peak"],
            "Volatility Δ (%)": (
                f"{result['volatility_change_pct']:+.1f}%"
                if result["volatility_change_pct"] is not None else "N/A"
            ),
            "Recovery":         (
                f"{result['recovery_days']} days"
                if result["recovery_days"] is not None else "Not recovered"
            ),
            "Risk Score":       f"{risk['score']} / 100",
            "Risk Level":       RISK_BADGE.get(risk["level"], risk["level"]),
            "p-value":          f"{result['p_value']:.4f}",
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ── CSV Export ────────────────────────────────────────────────────────────────

st.divider()

export_rows = []
for key, result in results.items():
    meta = result["meta"]
    risk = result["risk"]
    export_rows.append({
        "event_name":              event_name,
        "event_date":              event_date.isoformat(),
        "event_type":              event_type,
        "window_days":             window_days,
        "commodity":               meta["name"],
        "fred_code":               meta["code"],
        "avg_price_change_pct":    round(result["avg_price_change_pct"], 2),
        "peak_impact_pct":         round(result["peak_impact_pct"], 2),
        "days_to_peak":            result["days_to_peak"],
        "volatility_change_pct":   (
            round(result["volatility_change_pct"], 2)
            if result["volatility_change_pct"] is not None else None
        ),
        "recovery_days":           result["recovery_days"],
        "pre_event_avg":           round(result["pre_event_avg"], 4),
        "post_event_avg":          round(result["post_event_avg"], 4),
        "log_return_mean_before":  round(result["log_return_mean_before"], 6),
        "log_return_mean_after":   round(result["log_return_mean_after"], 6),
        "risk_score":              risk["score"],
        "risk_level":              risk["level"],
        "p_value":                 round(result["p_value"], 6),
        "is_significant":          result["is_significant"],
    })

export_df = pd.DataFrame(export_rows)
csv_buffer = StringIO()
export_df.to_csv(csv_buffer, index=False)

safe_name = event_name.strip().replace(" ", "_")
st.download_button(
    label="Export results to CSV",
    data=csv_buffer.getvalue(),
    file_name=f"scm_risk_{safe_name}_{event_date}.csv",
    mime="text/csv",
)

# ── Footer ─────────────────────────────────────────────────────────────────────

st.divider()
st.caption(
    "**Methodology:** Log returns event study (Zhao et al., 2024; Sarwar & Rye, 2025; Schmitt et al., 2015) | "
    "**Maritime loss:** Zhao-Tsinghua Nonlinear Loss Rule (2024) | "
    "**Data:** Federal Reserve Economic Data (FRED) | "
    "**Analyst's Shield:** Events are standardized data triggers for supply chain research."
)
