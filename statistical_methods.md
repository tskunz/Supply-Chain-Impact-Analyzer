# Statistical Methods Reference — Event Impact Analysis

## Methodological Foundation

This analysis uses **standard econometric event study methodology** with log returns transformation, consistent with:
- Zhao et al. (2024), *The Innovation* — Maritime network blockage modeling
- Sarwar & Rye (2025), *Frontiers in Sustainable Food Systems* — Geopolitical shock propagation
- Schmitt et al. (2015), Sandia National Labs — Economic consequences of supply chain disruptions

See `docs/refs/academic_benchmarks.md` for quantitative constants derived from these papers.

**Analyst's Shield:** All events are treated as standardized data triggers (transit closures, energy premiums, demand shocks). This is operational research, not political commentary.

---

## Step 0: Log Returns Transformation

**Apply this before computing ALL metrics.**

```
R_t = ln(P_t / P_{t-1})
```

**Why log returns:**
- Statistically symmetric (gains and losses treated equally)
- Additive over time (weekly return = sum of daily log returns)
- Consistent with academic literature (Zhao et al., Sarwar & Rye)
- Handles the compounding nature of commodity price movements

**Implementation:**
```python
import numpy as np

# Add log returns column to data
commodity_data['log_return'] = np.log(
    commodity_data['price'] / commodity_data['price'].shift(1)
)

# Extract before/after windows
before_data = commodity_data[before_start:before_end].copy()
after_data = commodity_data[after_start:after_end].copy()
```

---

## Analysis Window Definition

```python
from datetime import timedelta

before_start = event_date - timedelta(days=window_days)
before_end   = event_date - timedelta(days=1)
after_start  = event_date
after_end    = event_date + timedelta(days=window_days)

before_data = commodity_data[before_start:before_end].copy()
after_data  = commodity_data[after_start:after_end].copy()
```

**Default window:** 30 days (captures immediate impact, limits confounding events)
**Configurable range:** 15–90 days (user-adjustable via Streamlit slider)

**Rationale for 30 days:**
- Zhao et al. show nonlinear impacts emerge and peak within this window for maritime events
- Long enough to capture sustained impact; short enough to isolate the triggering event
- Works for both daily and monthly FRED data

---

## Metric 1: Average Price Change

**Definition:** Percentage change in mean price from before to after period

```
Δ% = ((μ_after - μ_before) / μ_before) × 100
```

**Implementation:**
```python
before_mean = before_data['price'].mean()
after_mean  = after_data['price'].mean()
avg_price_change_pct = ((after_mean - before_mean) / before_mean) * 100
```

**Interpretation:**
| Range | Magnitude |
|---|---|
| < ±5% | Minor |
| ±5–15% | Moderate |
| > ±15% | Major |

**Edge cases:**
- `before_mean == 0`: Return `None` (invalid baseline)
- `len(before_data) < 10`: Return `None` with user warning

---

## Metric 2: Peak Impact

**Definition:** Maximum percentage deviation from pre-event baseline during the after window

```python
if after_mean > before_mean:
    # Positive shock — find maximum price
    peak_price = after_data['price'].max()
    peak_date  = after_data['price'].idxmax()
else:
    # Negative shock — find minimum price
    peak_price = after_data['price'].min()
    peak_date  = after_data['price'].idxmin()

peak_impact_pct = ((peak_price - before_mean) / before_mean) * 100
days_to_peak    = (peak_date - event_date).days
```

**Interpretation:**
- **Fast peak (< 7 days):** Immediate shock, likely supply panic
- **Medium peak (7–21 days):** Propagating disruption
- **Slow peak (> 21 days):** Cascading or structural effect

---

## Metric 3: Volatility Change

**Definition:** Change in price standard deviation before vs. after the event

```
Volatility Change % = ((σ_after - σ_before) / σ_before) × 100
```

**Implementation:**
```python
before_std = before_data['price'].std()
after_std  = after_data['price'].std()
volatility_change_pct = ((after_std - before_std) / before_std) * 100
```

**Why volatility matters more than price change for supply chains:**
- High volatility = planning failure, panic buying, speculative hoarding
- Even a price that returns to baseline with high volatility signals persistent disruption
- Schmitt et al. document a 13.5% average increase in share-price volatility post-disruption

---

## Metric 4: Recovery Timeline

**Definition:** Days until price re-enters the "normal" range (within 1 std dev of pre-event mean)

```python
lower_bound = before_mean - before_std
upper_bound = before_mean + before_std

# Consecutive recovery check (3 days for daily data, 1 point for monthly)
recovered = after_data[
    (after_data['price'] >= lower_bound) &
    (after_data['price'] <= upper_bound)
]

if len(recovered) > 0:
    recovery_date = recovered.index[0]
    recovery_days = (recovery_date - event_date).days
else:
    recovery_days = None  # Not recovered within analysis window
```

**Hysteresis buffer (Zhao et al.):**
For maritime blockages, apply a 1.73× multiplier to estimate full recovery:
```python
# Zhao-Tsinghua: highly utilized chokepoints take ~73% longer to recover
if event_type == 'maritime' and recovery_days is not None:
    estimated_full_recovery = round(recovery_days * 1.73)
```

---

## Metric 5: Log Return Statistics

**Report alongside price-level metrics for statistical completeness:**

```python
log_return_mean_before = before_data['log_return'].mean()
log_return_mean_after  = after_data['log_return'].mean()
log_return_std_before  = before_data['log_return'].std()
log_return_std_after   = after_data['log_return'].std()
```

---

## Zhao-Tsinghua Nonlinear Loss Rule (Maritime Events Only)

**Apply when `event_type == 'maritime'`**

Based on Zhao et al. (2024), *The Innovation*: A 6-day Suez blockage generated ~$136.9B in global losses. Losses scale nonlinearly with blockage duration.

**Formula:**
```
Loss = (Daily_Trade_Value × 0.12) × e^(0.1 × Days_Blocked)
```

**Constants (from Zhao et al.):**
- Base loss coefficient: `0.12` (12% of daily trade value disrupted)
- Exponential growth rate: `0.1` per day
- Daily global seaborne trade value (2021 reference): ~$58.6B USD

**Implementation:**
```python
import math

DAILY_TRADE_VALUE_USD = 58_600_000_000  # $58.6B (2021 reference, Zhao et al.)
BASE_LOSS_COEFFICIENT = 0.12
EXPONENTIAL_RATE      = 0.1
RECOVERY_HYSTERESIS   = 1.73  # Zhao et al.: highly utilized chokepoints

def calculate_nonlinear_maritime_loss(days_blocked: int) -> dict:
    """
    Apply Zhao-Tsinghua Nonlinear Loss Rule for maritime blockage events.
    
    Formula: Loss = (Daily_Trade_Value × 0.12) × e^(0.1 × Days_Blocked)
    Source: Zhao et al. (2024), The Innovation
    """
    estimated_loss = (DAILY_TRADE_VALUE_USD * BASE_LOSS_COEFFICIENT) * math.exp(
        EXPONENTIAL_RATE * days_blocked
    )
    estimated_recovery_days = round(days_blocked * RECOVERY_HYSTERESIS)
    
    return {
        'estimated_global_loss_usd': estimated_loss,
        'estimated_recovery_days': estimated_recovery_days,
        'days_blocked': days_blocked,
        'methodology': 'Zhao-Tsinghua Nonlinear Loss (2024)'
    }
```

---

## Statistical Significance (Stretch Goal)

```python
from scipy import stats

t_stat, p_value = stats.ttest_ind(
    before_data['price'].dropna(),
    after_data['price'].dropna(),
    equal_var=False  # Welch's t-test (does not assume equal variance)
)

is_significant = p_value < 0.05
```

**Display:** Report p-value as supporting context, but do not over-emphasize. Visual magnitude and direction matter more for operational supply chain decision-making.

---

## Composite Risk Score (0–100 Scale)

```
Score = Price Impact (0–40) + Speed to Peak (0–20) + Volatility (0–20) + Recovery (0–20)
```

| Component | Formula |
|---|---|
| Price Impact | `min(|peak_impact_pct| × 2, 40)` |
| Speed to Peak | `<7d → 20`, `7–14d → 15`, `15–30d → 10`, `>30d → 5` |
| Volatility | `min(|volatility_change_pct| / 5, 20)` |
| Recovery | `None → 20`, `>90d → 15`, `60–90d → 10`, `30–60d → 5`, `<30d → 0` |

**Risk levels:**
| Score | Level |
|---|---|
| 0–25 | LOW |
| 26–50 | MODERATE |
| 51–75 | HIGH |
| 76–100 | CRITICAL |

---

## Data Validation

```python
def validate_data(before_data: pd.DataFrame, after_data: pd.DataFrame) -> tuple[bool, str | None]:
    """Validate data sufficiency before running analysis."""
    
    if len(before_data) < 10:
        return False, "Insufficient before-event data (need ≥10 points)"
    
    if len(after_data) < 10:
        return False, "Insufficient after-event data (need ≥10 points)"
    
    total = len(before_data) + len(after_data)
    missing = before_data['price'].isna().sum() + after_data['price'].isna().sum()
    
    if missing / total > 0.2:
        return False, f"Excessive missing data: {missing/total*100:.1f}% (max 20%)"
    
    return True, None
```

---

## Outlier Handling

**DO NOT automatically remove outliers.** Supply chain shocks create legitimate extreme values (e.g., negative oil futures in April 2020). Instead, flag and inform:

```python
z_scores = abs((data['price'] - data['price'].mean()) / data['price'].std())
outliers = data[z_scores > 3]

if len(outliers) > 0:
    st.warning(f"⚠️ {len(outliers)} potential outliers detected — verify data quality for extreme values")
```

---

## Visualization Specification

**Required chart elements:**
1. Price over time (blue line, width=2)
2. Vertical dashed red line at event date
3. Vertical dotted orange line at peak impact date (with annotation)
4. Horizontal dotted gray line at pre-event mean
5. Shaded region: before window (rgba gray, opacity=0.1)
6. Shaded region: after window (rgba blue, opacity=0.1)

**Chart title format:** `"{Commodity Name} — {Event Name}"`
**Y-axis label:** `"Price ({units})"` (units from `commodity_indicators.md`)

---

## Critical Reminders

1. **Always apply log returns transformation first** before computing metrics
2. **Apply Nonlinear Loss Rule only for maritime event types**
3. **Do not invent formulas** — use the exact calculations specified above
4. **Validate against expected ranges** in `historical_events.md`
5. **Return `None` for uncomputable metrics** (e.g., recovery_days if not recovered)
6. **Do not remove outliers** — flag them instead

**If methodology is unclear for a specific case, FLAG IT. Do not guess.**
