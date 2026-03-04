# Commodity Indicators Reference — FRED API

## Source
Federal Reserve Economic Data (FRED) — https://fred.stlouisfed.org/
Accessed via `fredapi` Python library (`pip install fredapi`)

---

## Core Commodity Indicators (MVP Focus)

### Energy Commodities

| Commodity | FRED Code | Units | Frequency | Supply Chain Relevance |
|---|---|---|---|---|
| Crude Oil (Brent) | `DCOILBRENTEU` | USD/Barrel | Daily | Global logistics cost proxy; geopolitical risk benchmark |
| Crude Oil (WTI) | `DCOILWTICO` | USD/Barrel | Daily | US benchmark; secondary to Brent for global analysis |
| Natural Gas (Henry Hub) | `DHHNGSP` | USD/MMBtu | Daily | Energy-intensive manufacturing; European exposure |
| Coal (Australia) | `PCOALAUUSDM` | USD/Metric Ton | Monthly | Power generation; lower priority for MVP |

**Priority for MVP:** Brent Crude (P1), Natural Gas (P2)

---

### Industrial Metals

| Commodity | FRED Code | Units | Frequency | Supply Chain Relevance |
|---|---|---|---|---|
| Copper | `PCOPPUSDM` | USD/Metric Ton | Monthly | Industrial demand proxy; semiconductor/electronics |
| Aluminum | `PALUMUSDM` | USD/Metric Ton | Monthly | Automotive, packaging; energy-intensive production |
| Iron Ore | `PIORECRUSDM` | USD/Dry Metric Ton | Monthly | Steel production; construction/heavy industry |
| Nickel | `PNICKUSDM` | USD/Metric Ton | Monthly | EV batteries, stainless steel; lower priority for MVP |
| Zinc | `PZINCUSDM` | USD/Metric Ton | Monthly | Galvanizing, construction; lower priority for MVP |

**Priority for MVP:** Copper (P3), Aluminum (P4), Iron Ore (P5)

---

### Precious Metals (Optional)

| Commodity | FRED Code | Units | Frequency | Notes |
|---|---|---|---|---|
| Gold | `GOLDAMGBD228NLBM` | USD/Troy Oz | Daily | "Fear index" / safe-haven demand signal |
| Silver | `SLVPRUSD` | USD/Troy Oz | Daily | Industrial + safe-haven hybrid |

**Note:** Gold is useful as a risk-sentiment indicator (inverse correlation with risk assets). Lower priority for supply chain focus but useful for the fear/uncertainty dimension.

---

### Agricultural Commodities (Stretch Goal)

| Commodity | FRED Code | Units | Frequency | Notes |
|---|---|---|---|---|
| Wheat (US) | `PWHEAMTUSDM` | USD/Metric Ton | Monthly | Food supply chain; critical for Ukraine event analysis |
| Corn | `PMAIZMTUSDM` | USD/Metric Ton | Monthly | Feed/fuel supply chain |
| Soybeans | `PSOYBUSDQ` | USD/Metric Ton | Quarterly | Coarse frequency; lower MVP priority |

**Note:** Wheat is especially relevant for the Ukraine invasion case (Russia/Ukraine = ~25% of global wheat exports).

---

## Recommended MVP Selection (4–5 Commodities)

```python
COMMODITIES = {
    'crude_oil_brent': {
        'code': 'DCOILBRENTEU',
        'name': 'Crude Oil (Brent)',
        'units': 'USD/Barrel',
        'frequency': 'daily',
        'priority': 1
    },
    'natural_gas': {
        'code': 'DHHNGSP',
        'name': 'Natural Gas (Henry Hub)',
        'units': 'USD/MMBtu',
        'frequency': 'daily',
        'priority': 2
    },
    'copper': {
        'code': 'PCOPPUSDM',
        'name': 'Copper',
        'units': 'USD/Metric Ton',
        'frequency': 'monthly',
        'priority': 3
    },
    'aluminum': {
        'code': 'PALUMUSDM',
        'name': 'Aluminum',
        'units': 'USD/Metric Ton',
        'frequency': 'monthly',
        'priority': 4
    },
    'iron_ore': {
        'code': 'PIORECRUSDM',
        'name': 'Iron Ore',
        'units': 'USD/Dry Metric Ton',
        'frequency': 'monthly',
        'priority': 5
    }
}
```

---

## Extended Commodity Catalog (Phase 5 — Semantic Suggestion Layer)

This expanded catalog supports the semantic suggestion feature: when a user describes an event in natural language, a Claude API call over this dictionary surfaces relevant commodities to analyze. With ~30 entries the full catalog fits in a single prompt — no vector database required.

**Do not use these in the MVP UI multiselect unless time permits. Add them in Phase 5.**

### Energy (Extended)

| Commodity | FRED Code | Units | Frequency | Relevance Tags |
|---|---|---|---|---|
| Crude Oil (Brent) | `DCOILBRENTEU` | USD/Barrel | Daily | energy, geopolitical, shipping, logistics |
| Crude Oil (WTI) | `DCOILWTICO` | USD/Barrel | Daily | energy, US benchmark |
| Natural Gas | `DHHNGSP` | USD/MMBtu | Daily | energy, manufacturing, Europe, winter |
| Propane | `DPROPANEMBTX` | USD/Gallon | Daily | energy, petrochemical, heating |
| Coal (Australia) | `PCOALAUUSDM` | USD/Metric Ton | Monthly | energy, power generation, Asia |
| Heating Oil | `DHOILNYH` | USD/Gallon | Daily | energy, logistics, winter, northeast US |
| Gasoline (US Retail) | `GASREGCOVW` | USD/Gallon | Weekly | energy, consumer, logistics |

### Industrial Metals (Extended)

| Commodity | FRED Code | Units | Frequency | Relevance Tags |
|---|---|---|---|---|
| Copper | `PCOPPUSDM` | USD/Metric Ton | Monthly | manufacturing, electronics, EV, construction |
| Aluminum | `PALUMUSDM` | USD/Metric Ton | Monthly | automotive, aerospace, packaging, energy-intensive |
| Iron Ore | `PIORECRUSDM` | USD/Dry Metric Ton | Monthly | steel, construction, heavy industry |
| Nickel | `PNICKUSDM` | USD/Metric Ton | Monthly | stainless steel, EV batteries, aerospace |
| Zinc | `PZINCUSDM` | USD/Metric Ton | Monthly | galvanizing, construction, automotive |
| Lead | `PLEAD01USD` | USD/Metric Ton | Monthly | batteries, construction, manufacturing |
| Tin | `PTINUSDM` | USD/Metric Ton | Monthly | electronics, solder, semiconductor packaging |

### Precious Metals

| Commodity | FRED Code | Units | Frequency | Relevance Tags |
|---|---|---|---|---|
| Gold | `GOLDAMGBD228NLBM` | USD/Troy Oz | Daily | safe-haven, fear index, financial crisis |
| Silver | `SLVPRUSD` | USD/Troy Oz | Daily | industrial, solar, electronics, safe-haven |
| Platinum | `PLATINUMUSDM` | USD/Troy Oz | Monthly | automotive catalysts, hydrogen fuel cells |
| Palladium | `PPALMUSDM` | USD/Troy Oz | Monthly | automotive catalysts, semiconductor |

### Agricultural Commodities

| Commodity | FRED Code | Units | Frequency | Relevance Tags |
|---|---|---|---|---|
| Wheat (US) | `PWHEAMTUSDM` | USD/Metric Ton | Monthly | food security, Ukraine, Russia, drought |
| Corn | `PMAIZMTUSDM` | USD/Metric Ton | Monthly | food, ethanol, feed, drought |
| Soybeans | `PSOYBUSDQ` | USD/Metric Ton | Quarterly | food, feed, China trade, Brazil |
| Rice | `PRICENPQUSDM` | USD/Metric Ton | Monthly | Asia food security, flood risk |
| Sugar | `PSUGAISAUSDM` | USD/Metric Ton | Monthly | food, ethanol, Brazil |
| Cotton | `PCOTTINDUSDM` | USD/Metric Ton | Monthly | textiles, apparel supply chain |
| Rubber (Natural) | `PRUBBERNUSDM` | USD/Metric Ton | Monthly | automotive tires, medical supplies |

### Chemicals & Fertilizers

| Commodity | FRED Code | Units | Frequency | Relevance Tags |
|---|---|---|---|---|
| Urea (Fertilizer) | `PUREAUSDM` | USD/Metric Ton | Monthly | agriculture, food security, Russia |
| Potash | `PPOTAUSDM` | USD/Metric Ton | Monthly | fertilizer, Belarus, Russia, agriculture |

### Lumber & Construction

| Commodity | FRED Code | Units | Frequency | Relevance Tags |
|---|---|---|---|---|
| Lumber | `WPU0811` | Index | Monthly | construction, housing, pandemic demand |

---

## Semantic Suggestion — Implementation Notes (Phase 5)

When implementing the commodity suggestion feature, pass this full catalog as context in a Claude API call:

```python
COMMODITY_CATALOG_FOR_SUGGESTION = {
    key: {
        'name': val['name'],
        'frequency': val['frequency'],
        'relevance_tags': val['relevance_tags']
    }
    for key, val in EXTENDED_COMMODITIES.items()
}

# Prompt pattern for suggestion:
prompt = f"""
Given the following supply chain disruption event:
Event: {event_name}
Date: {event_date}
Event Type: {event_type}

From this commodity catalog:
{json.dumps(COMMODITY_CATALOG_FOR_SUGGESTION, indent=2)}

Suggest the 3-5 commodities most likely to show measurable price impact.
Return a JSON list of commodity keys with a one-sentence rationale for each.
Flag any relevant supply chain exposures NOT covered by this catalog.
"""
```

**Note:** Monthly commodities suggested by this system should automatically trigger the window compatibility check (require ≥90 days). The suggestion layer should surface the warning alongside the suggestion.

---

## Shipping & Logistics Notes

**Baltic Dry Index is NOT available on FRED as a free time series.**

**Decision for MVP:** Skip dedicated shipping index. Use Brent Crude as logistics cost proxy — freight costs are ~60–70% correlated with oil prices and sufficient for this analysis.

**If shipping-specific data becomes needed:** Investigate Quandl or direct BDI sources as a Phase 2 addition.

---

## Data Quality Notes

### Update Frequencies
- **Daily series:** Crude oil, natural gas, gold — best for event-level resolution
- **Monthly series:** Metals, agriculture — adequate for 30-day windows; be aware that 30 trading days = ~6 monthly data points, which is near the minimum for statistical reliability

### ⚠️ Monthly Data + Short Window Warning

**Copper, Aluminum, Iron Ore, and all agricultural commodities are MONTHLY series.**

A 30-day analysis window yields only ~1–2 monthly data points before and after the event — below the 10-point minimum required for statistical validity. This will trigger the data validation error and produce no results for these commodities.

**Rules to implement in `data_collector.py` and `app.py`:**

```python
MONTHLY_COMMODITIES = {'copper', 'aluminum', 'iron_ore', 'nickel', 'zinc',
                       'wheat', 'corn', 'soybeans', 'coal'}

def check_window_compatibility(commodity_key: str, window_days: int) -> tuple[bool, str | None]:
    """Warn if analysis window is too short for monthly data."""
    if commodity_key in MONTHLY_COMMODITIES and window_days < 90:
        return False, (
            f"{commodity_key} is a monthly series. "
            f"A {window_days}-day window yields too few data points for analysis. "
            f"Use window_days ≥ 90 for monthly commodities, "
            f"or switch to a daily series (Brent Crude, Natural Gas)."
        )
    return True, None
```

**In the Streamlit UI:** When a user selects a monthly commodity with window < 90 days, show `st.warning()` with the above message and either auto-extend the window to 90 or exclude that commodity from the analysis run. Do not silently fail.

---

### Missing Data Handling

```python
# Standard approach: forward-fill up to 5 days (pandas 2.0+ syntax)
df = df.ffill(limit=5)

# Warn if gaps remain
if df['price'].isna().sum() > 0:
    st.warning(f"{df['price'].isna().sum()} data points still missing after forward-fill")
```

### Date Range Coverage
- Daily series: ~1980s to present
- Monthly series: ~1960s to present
- Sufficient for any modern supply chain event

---

## Expected Rough Price Ranges (for Data Validation)

Use these to sanity-check that you fetched the right series and units are correct:

| Commodity | Typical Range | Notes |
|---|---|---|
| Brent Crude | $20–$130/bbl | Spiked briefly >$130 in 2022 |
| Natural Gas | $1.50–$9/MMBtu | Spike to ~$9 in Aug 2022 |
| Copper | $4,000–$11,000/MT | |
| Aluminum | $1,200–$3,500/MT | |
| Iron Ore | $50–$230/DMT | |

**If fetched values are outside these ranges, check:** units, FRED code accuracy, date range selection.

---

## Critical Reminders

1. **DO NOT guess indicator codes** — use the codes in this file exactly
2. **DO NOT use WTI as primary oil benchmark** — use Brent (global standard)
3. **DO validate units** — especially for metals (per metric ton, not per pound)
4. **DO handle monthly data carefully** — 30-day windows = very few data points
5. **DO forward-fill gaps** — weekends, holidays, reporting delays are normal

**If you need a commodity not listed here, FLAG IT. Do not guess the FRED code.**
