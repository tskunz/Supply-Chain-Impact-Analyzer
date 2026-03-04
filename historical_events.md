# Historical Events Reference — Test Cases & Actuals

## Purpose

Pre-defined supply chain disruption events with documented outcomes for:
1. **Development testing** — validate analysis code produces sensible results
2. **UI pre-loading** — example events dropdown for demo
3. **Portfolio demonstration** — show real, known events with real data

Do NOT hardcode these results. Calculate everything dynamically. Use these ranges for validation only.

---

## Event Taxonomy (Maps to `event_type` in analyzer)

| Type | Description | Expected Pattern |
|---|---|---|
| `geopolitical` | Military conflict, sanctions, embargoes | Energy up fast, metals moderate |
| `maritime` | Physical shipping obstruction | Brief spike, fast recovery; apply Nonlinear Loss |
| `pandemic` | Demand destruction + supply disruption | All commodities down; oil hardest hit |
| `financial` | Credit crisis, recession trigger | Severe, broad commodity crash |

---

## Case A: Ukraine Invasion (Feb 24, 2022)

**Event type:** `geopolitical`

**Background:**
Russia's full-scale invasion of Ukraine. Russia is a top-3 global oil and gas exporter. Ukraine supplies ~25% of global wheat/barley. The event triggered immediate energy supply disruption fears across Europe.

**Analysis window:** 30 days

**Expected Commodity Impacts:**

| Commodity | Avg Change | Peak Impact | Days to Peak | Recovery |
|---|---|---|---|---|
| Brent Crude | +15 to +25% | ~+22% | 7–14 days | 45–60 days partial |
| Natural Gas | +30 to +50% | +40–60% | 10–20 days | 90+ days (incomplete) |
| Copper | +5 to +10% | +8–12% | 14–21 days | 30–45 days |
| Wheat (if included) | +15 to +25% | +20–30% | 7–14 days | 60–90 days |

**Historical actuals (documented):**
- Brent reached ~$120/bbl at peak (from ~$95 pre-invasion) ≈ +26%
- Recovery: ~52-day partial stabilization before elevated plateau

**Key insight:** Energy commodities most affected. Geopolitical energy premium (Sarwar & Rye, 2025) of +15–25% is consistent with observed outcome.

**Test code:**
```python
event = {
    'name': 'Ukraine Invasion',
    'date': datetime(2022, 2, 24),
    'event_type': 'geopolitical',
    'commodities': ['crude_oil_brent', 'natural_gas', 'copper'],
    'window_days': 30
}
# Pass criteria: oil avg_price_change_pct between 15 and 25
```

---

## Case B: COVID-19 Global Lockdowns (Mar 15, 2020)

**Event type:** `pandemic`

**Background:**
The date of widespread Western lockdown declarations. This is a demand destruction event, not a logistics friction event. Industrial demand collapsed globally, with secondary supply disruptions from factory closures.

**Analysis window:** 30 days (note: full impact extended well beyond)

**Expected Commodity Impacts:**

| Commodity | Avg Change | Peak Impact | Days to Peak | Recovery |
|---|---|---|---|---|
| Brent Crude | −50 to −65% | −60 to −71% | 30–45 days | 120+ days |
| Natural Gas | −10 to −20% | −15 to −25% | 20–30 days | 60–90 days |
| Copper | −15 to −25% | −20 to −30% | 15–25 days | 90–120 days |
| Aluminum | −10 to −20% | −15 to −25% | 20–30 days | 90–120 days |

**Historical actuals (documented):**
- Brent crude: ~71% decline from January 2020 peak to April 2020 trough
- WTI futures briefly went NEGATIVE on April 20, 2020 (unprecedented; storage constraints)
- Pattern: **Demand destruction shock** — all industrial commodities down, oil hardest hit

**Important:** This event's peak impact extends BEYOND the default 30-day window. When using 30-day analysis, the `avg_price_change_pct` will not capture the full trough. Consider using `window_days=60` for this event.

**Test code:**
```python
event = {
    'name': 'COVID-19 Global Lockdowns',
    'date': datetime(2020, 3, 15),
    'event_type': 'pandemic',
    'commodities': ['crude_oil_brent', 'copper', 'natural_gas'],
    'window_days': 45  # Extend window to capture full impact
}
# Pass criteria: oil avg_price_change_pct between -50 and -65
```

---

## Case C: Suez Canal Blockage (Mar 23, 2021)

**Event type:** `maritime`

**Background:**
The Ever Given container ship ran aground and blocked the Suez Canal for 6 days (cleared March 29). Approximately 400 vessels backlogged, representing ~10% of global seaborne trade volume.

**Analysis window:** 15 days (short-duration event)

**Expected Commodity Impacts:**

| Commodity | Avg Change | Peak Impact | Days to Peak | Recovery |
|---|---|---|---|---|
| Brent Crude | +3 to +6% | +4 to +8% | 2–5 days | 7–14 days |
| Natural Gas | +2 to +5% | +3 to +7% | 3–7 days | 7–14 days |
| Copper | Minimal | <3% | N/A | <7 days |

**Historical actuals (documented):**
- Estimated ~$10B per week in held-up trade (Zhao et al.)
- Oil: immediate spike followed by high volatility, then fast normalization
- Pattern: **Brief panic, fast recovery** — event resolved quickly

**Nonlinear Loss calculation (apply when `event_type == 'maritime'`):**
```python
# 6-day blockage, Zhao-Tsinghua model
estimated_loss = (58_600_000_000 * 0.12) * math.exp(0.1 * 6)  # ≈ $12.7B
estimated_recovery = round(6 * 1.73)  # ≈ 10 days
```

**Test code:**
```python
event = {
    'name': 'Suez Canal Blockage',
    'date': datetime(2021, 3, 23),
    'event_type': 'maritime',
    'commodities': ['crude_oil_brent', 'natural_gas'],
    'window_days': 15
}
# Pass criteria: oil avg_price_change_pct between 3 and 7
```

---

## Case D: 2008 Financial Crisis (Sep 15, 2008)

**Event type:** `financial`

**Background:**
Lehman Brothers collapse triggered global credit crisis. Industrial demand collapsed as recession spread globally. This is the largest commodity crash in modern history.

**Analysis window:** 90 days (slow-developing, structural crisis)

**Expected Commodity Impacts:**

| Commodity | Avg Change | Peak Impact | Days to Peak | Recovery |
|---|---|---|---|---|
| Brent Crude | −60 to −75% | −70 to −80% | ~90 days | 18+ months |
| Copper | −40 to −55% | −50 to −60% | ~90 days | 12–18 months |
| Aluminum | −30 to −45% | −40 to −50% | ~90 days | 12–18 months |
| Iron Ore | −50 to −65% | −60 to −70% | ~90 days | 18+ months |

**Key insight:** Broad commodity crash. All industrial commodities affected. Recovery extends well beyond any analysis window — "recovery_days" will return `None` for most commodities.

**Test code:**
```python
event = {
    'name': '2008 Financial Crisis',
    'date': datetime(2008, 9, 15),
    'event_type': 'financial',
    'commodities': ['crude_oil_brent', 'copper', 'aluminum', 'iron_ore'],
    'window_days': 90
}
# Pass criteria: oil avg_price_change_pct between -60 and -75
# Expect: recovery_days == None for most commodities
```

---

## Case E: Red Sea Shipping Disruptions (Dec 1, 2023)

**Event type:** `maritime`

**Background:**
Houthi attacks on commercial vessels in the Red Sea caused mass rerouting around the Cape of Good Hope. J.P. Morgan estimated +0.7pp to global core goods inflation in H1 2024, with ~9% reduction in effective container shipping capacity.

**Analysis window:** 30 days

**Expected Commodity Impacts:**

| Commodity | Avg Change | Peak Impact | Days to Peak | Recovery |
|---|---|---|---|---|
| Brent Crude | +5 to +10% | +8 to +12% | 10–20 days | Ongoing (as of early 2024) |
| Natural Gas | +3 to +8% | +5 to +10% | 10–20 days | Ongoing |

**Key insight:** Moderate commodity impact. Primary economic damage was to **freight costs** (5× surge on Asia-Europe routes per J.P. Morgan) rather than commodity prices directly.

**Test code:**
```python
event = {
    'name': 'Red Sea Shipping Disruptions',
    'date': datetime(2023, 12, 1),
    'event_type': 'maritime',
    'commodities': ['crude_oil_brent', 'natural_gas'],
    'window_days': 30
}
# Pass criteria: oil avg_price_change_pct between 5 and 12
```

---

## Streamlit Pre-loaded Events Dictionary

```python
from datetime import datetime

EXAMPLE_EVENTS = {
    "Ukraine Invasion (Feb 2022)": {
        "date": datetime(2022, 2, 24),
        "event_type": "geopolitical",
        "commodities": ["crude_oil_brent", "natural_gas", "copper"],
        "window": 30
    },
    "COVID-19 Lockdowns (Mar 2020)": {
        "date": datetime(2020, 3, 15),
        "event_type": "pandemic",
        "commodities": ["crude_oil_brent", "copper", "natural_gas"],
        "window": 45
    },
    "Suez Canal Blockage (Mar 2021)": {
        "date": datetime(2021, 3, 23),
        "event_type": "maritime",
        "commodities": ["crude_oil_brent", "natural_gas"],
        "window": 15
    },
    "2008 Financial Crisis (Sep 2008)": {
        "date": datetime(2008, 9, 15),
        "event_type": "financial",
        "commodities": ["crude_oil_brent", "copper", "aluminum"],
        "window": 90
    },
    "Red Sea Disruptions (Dec 2023)": {
        "date": datetime(2023, 12, 1),
        "event_type": "maritime",
        "commodities": ["crude_oil_brent", "natural_gas"],
        "window": 30
    }
}
```

---

## Validation Pass/Fail Criteria

| Check | Pass Threshold | Action if Fail |
|---|---|---|
| Price change direction | Must match expected sign (+/−) | Investigate immediately |
| Price change magnitude | Within ±8% of expected range midpoint | Investigate data quality |
| Days to peak | Within ±7 days of expected range | Review date alignment |
| Recovery detection | Not recovered for 2008/COVID is expected | Confirm None is returned correctly |

**Common failure causes:**
- Wrong FRED indicator code
- Date range too narrow to capture peak
- Missing data around event date
- Monthly data providing too few points for 30-day window

---

## Critical Reminders

1. **DO use these for testing** — run all 5 cases to validate the analysis engine
2. **DO include in UI as example dropdown** — demonstrates real-world applicability
3. **DO expect variance** — ranges are guidelines, not exact targets
4. **DO NOT hardcode expected values into production code** — calculate everything
5. **DO NOT add events not documented here** without flagging and researching expected ranges
