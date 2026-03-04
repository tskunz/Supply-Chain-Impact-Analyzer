# Supply Chain Event Impact Analyzer — Claude Code Instructions

## READ THIS FIRST

You are building a **quantitative supply chain event impact analyzer** that uses real commodity price data to measure economic disruption. This is NOT a chatbot or RAG system — it is statistical analysis over real FRED API time series data.

This project uses the **Three-Layer Knowledge Architecture**:
- **Layer A (Library Syntax):** Python, pandas, plotly, streamlit — you know these natively
- **Layer B (Project Decisions):** Architecture, tradeoffs — defined in this file
- **Layer C (Domain Science):** Commodity indicators, statistical methods, academic benchmarks, event taxonomy — defined in `docs/refs/`

---

## Documentation Strategy (PRIORITY ORDER)

1. **READ THIS FILE FIRST** — understand architecture and constraints
2. **READ ALL FILES IN `docs/refs/`** before writing any analysis code:
   - `commodity_indicators.md` — exact FRED codes to use
   - `statistical_methods.md` — formulas and implementation patterns
   - `academic_benchmarks.md` — quantitative constants and risk coefficients
   - `historical_events.md` — test cases with expected output ranges
3. **USE YOUR BUILT-IN KNOWLEDGE** for Python, pandas, plotly, streamlit (Layer A)
4. **WEB SEARCH ONLY AS LAST RESORT** — for novel bugs not covered by ref docs

---

## Project Goal

Build a Streamlit dashboard that:
1. Accepts user input: event name + date
2. Fetches commodity price data from the FRED API
3. Performs before/after statistical analysis using **log returns**
4. Displays interactive Plotly charts with event markers
5. Calculates risk metrics: price change, peak impact, volatility, recovery time, risk score

**Deliverable:** Working demo deployable to Streamlit Cloud

---

## Architecture Decisions (Layer B)

### Data Source: FRED API ONLY

**Decision:** Use Federal Reserve Economic Data via the `fredapi` Python library
- **Why:** Free, high-quality, well-maintained, simple Python integration
- **Not using:** World Bank API, web scraping, paid APIs

**Core indicators (see `docs/refs/commodity_indicators.md` for exact codes):**
- Brent Crude Oil (daily)
- Natural Gas Henry Hub (daily)
- Copper (monthly)
- Aluminum (monthly)
- Iron Ore (monthly)

### Statistical Methodology

**Decision:** Log returns + before/after comparison with configurable windows (default 30 days)
- **Log returns:** `R_t = ln(P_t / P_{t-1})` — statistically symmetric, additive over time
- **Before window:** `event_date - window_days` to `event_date - 1`
- **After window:** `event_date` to `event_date + window_days`
- **Maritime events:** Apply Zhao-Tsinghua Nonlinear Loss Rule (see `docs/refs/statistical_methods.md`)
- **Not using:** ARIMA, VAR, ML models — this is statistical analysis, not prediction

### Technology Stack

| Layer | Tool | Notes |
|---|---|---|
| Frontend | Streamlit | Single-page, no tabs |
| Charts | Plotly | Interactive, use_container_width=True |
| Data | pandas + numpy | In-memory only, no DB |
| API | fredapi | pip install fredapi |
| Deployment | Streamlit Cloud | Free tier, public URL |

### Code Organization

```
src/
├── data_collector.py    — FRED API integration, data fetching, cleaning
├── event_analyzer.py    — Statistical analysis, before/after, log returns
├── risk_calculator.py   — Composite risk score, Nonlinear Loss Rule
└── app.py               — Streamlit UI, main entry point
```

---

## Implementation Order

### Phase 1: Data Collection (target: 1 hour)

**File:** `src/data_collector.py`

**Requirements:**
1. Initialize FRED client from `fredapi`
2. Implement `get_commodity_data(indicator_code, start_date, end_date) -> pd.DataFrame`
3. Return DataFrame with DatetimeIndex and `price` column
4. Forward-fill missing data (limit: 5 days), warn user if gaps remain
5. Validate: non-empty, chronological, no >20% NaN

**Test:** Fetch `DCOILBRENTEU` for 2021–2023, verify structure

---

### Phase 2: Event Analysis (target: 1.5 hours)

**File:** `src/event_analyzer.py`

**Requirements:**
1. Implement `analyze_event_impact(commodity_data, event_date, window_days=30, event_type='general') -> dict`
2. Calculate log returns before computing all metrics
3. Key metrics to return:

```python
{
    'avg_price_change_pct': float,    # (μ_after - μ_before) / μ_before × 100
    'peak_impact_pct': float,         # max % deviation from pre-event baseline
    'peak_date': datetime,
    'days_to_peak': int,
    'volatility_change_pct': float,   # (σ_after - σ_before) / σ_before × 100
    'recovery_days': int | None,      # None if not recovered within window
    'pre_event_avg': float,
    'post_event_avg': float,
    'log_return_mean_before': float,  # mean of log returns in before window
    'log_return_mean_after': float,   # mean of log returns in after window
}
```

4. For `event_type='maritime'`, apply Zhao-Tsinghua Nonlinear Loss Rule (see `docs/refs/statistical_methods.md`)

**Validation:** Test against Ukraine invasion (Feb 24, 2022) — expected oil +15–25%

---

### Phase 3: Streamlit Dashboard (target: 1.5 hours)

**File:** `src/app.py`

**User Inputs:**
- Event name (text input)
- Event date (date picker)
- Event type (selectbox: General / Maritime / Financial / Pandemic)
- Analysis window (slider: 15–90 days, default 30)
- Commodity selection (multiselect)

**Display:**
1. **Interactive Plotly chart:**
   - Price over time (line)
   - Dashed red vertical: event date
   - Dotted orange vertical: peak impact date
   - Shaded before/after windows
   - Dotted gray horizontal: pre-event mean

2. **st.columns metrics:**
   - Average Price Change (%)
   - Peak Impact (%)
   - Days to Peak
   - Volatility Change (%)
   - Recovery Time (days or "Not recovered")
   - Risk Score (0–100 with level badge)

3. **Summary table (st.dataframe):** Multi-commodity comparison when >1 selected

**Bonus (time permitting):**
- Pre-loaded example events dropdown
- Export to CSV button
- Statistical significance (p-value from Welch's t-test)

**UI tone:** Maintain "Analyst's Shield" framing — label events as "logistical friction" or "demand shock", not political commentary

---

### Phase 4: Polish & Deploy (target: 30 minutes)

1. `requirements.txt` with pinned versions
2. `.gitignore` for Python
3. `README.md` with live demo link, architecture explanation, example use cases
4. Deploy to Streamlit Cloud
5. Validate with 3 historical events from `docs/refs/historical_events.md`

---

## Error Handling Guidelines

```python
# FRED API errors
try:
    data = fred.get_series(indicator, start, end)
except Exception as e:
    st.error(f"Failed to fetch {indicator}: {str(e)}")
    return None

# Missing data
data = data.ffill(limit=5)
if data.isna().any():
    st.warning(f"Data gaps remain after forward-fill for {commodity}")

# Insufficient data
if len(before_data) < 10:
    st.error("Insufficient data before event date (need ≥10 data points)")
    return None
```

---

## FRED API Key Handling

**NEVER hardcode the API key.**

**Local development:** Add to `.streamlit/secrets.toml` (already gitignored):
```toml
FRED_API_KEY = "your_key_here"
```

**Streamlit Cloud deployment:** Do NOT rely on `secrets.toml` — that file is gitignored and will not be present in the deployed repo. Instead, set the secret via the Streamlit Cloud dashboard:
- Go to your app → Settings → Secrets
- Add: `FRED_API_KEY = "your_key_here"`

**In `app.py`:**
```python
import streamlit as st
from fredapi import Fred

fred = Fred(api_key=st.secrets["FRED_API_KEY"])
```

**Add a graceful fallback for missing key:**
```python
try:
    api_key = st.secrets["FRED_API_KEY"]
except KeyError:
    st.error(
        "FRED API key not found. "
        "Local: add to .streamlit/secrets.toml. "
        "Streamlit Cloud: add via app Settings → Secrets."
    )
    st.stop()
```

---

## Code Quality Requirements

Every function must have:
1. Type hints for all parameters and return values
2. Docstring: description, Parameters, Returns, Raises
3. Input validation with meaningful error messages
4. Error handling for expected failure modes

---

## Critical Constraints

### MUST DO:
- ✅ Read ALL `docs/refs/` files before writing analysis code
- ✅ Use log returns (`ln(P_t / P_{t-1})`) for volatility and delta calculations
- ✅ Use FRED indicator codes EXACTLY as listed in `commodity_indicators.md`
- ✅ Apply Nonlinear Loss Rule for maritime event types
- ✅ Validate results against `historical_events.md` expected ranges
- ✅ Handle missing data gracefully (forward-fill, warn user)
- ✅ Keep UI single-page, clean, "Analyst's Shield" tone

### MUST NOT DO:
- ❌ Build ML models (no ARIMA, XGBoost, neural nets)
- ❌ Guess commodity indicator codes — use the ref doc
- ❌ Hardcode FRED API key
- ❌ Use a database (pandas DataFrames are sufficient)
- ❌ Add real-time data updates
- ❌ Invent statistical formulas — use those in `statistical_methods.md`
- ❌ Over-engineer the UI (no multi-page navigation, no auth)

---

## When Information Is Missing

If you encounter unclear methodology, missing indicator codes, or ambiguous behavior:

1. **FLAG IT** — state what's missing
2. **SUGGEST OPTIONS** — propose reasonable approaches with tradeoffs
3. **WAIT FOR CLARIFICATION** — do not guess or web search for domain knowledge

Do NOT silently proceed with an assumption on domain questions.

---

## Success Metrics

**MVP achieved when:**
1. ✅ User inputs event + date
2. ✅ System fetches FRED data
3. ✅ Chart renders with event marker
4. ✅ Metrics calculated using log returns
5. ✅ App deployed to Streamlit Cloud with public URL

**Stretch goals:**
- ✅ Multi-commodity comparison table
- ✅ Risk score with Nonlinear Loss for maritime events
- ✅ Example events dropdown (pre-loaded)
- ✅ CSV export
- ✅ Statistical significance display (p-value)

---

**Start with Phase 1. Read `docs/refs/` first. Flag gaps. Ship working code.** 🚀
