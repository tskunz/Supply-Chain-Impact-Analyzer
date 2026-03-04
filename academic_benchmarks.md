# Academic Benchmarks — Quantitative Constants & Risk Coefficients

## Purpose

This file provides **Layer C domain science constants** derived from peer-reviewed research. Use these as:
1. Ground-truth coefficients for risk calculations (Nonlinear Loss, recovery multipliers)
2. Benchmarks for validating analysis output
3. Attribution when presenting methodology

Do NOT invent coefficients or modify these without flagging the change.

---

## Source Papers

### 1. Geopolitical Shocks & Energy Volatility

**Full Citation:**
Sarwar, D.S. & Rye, S. (2025). "The impact of the Russia-Ukraine war on global supply chains: a systematic literature review." *Frontiers in Sustainable Food Systems*, Vol. 9, September 2025.

**Key Quantitative Findings:**

| Finding | Value | Application |
|---|---|---|
| Russia/Ukraine share of global wheat/barley exports | ~25% | Food supply chain baseline |
| Russia/Ukraine share of sunflower oil exports | ~60% | Edible oils supply chain |
| Ukraine wheat production decline (2022) | −26% | Agricultural shock magnitude |
| Ukraine soybean production decline (2022) | −32% | Agricultural shock magnitude |
| Ukraine maize production decline (2022) | −21% | Agricultural shock magnitude |
| Conflict premium on Brent Crude (immediate) | +15% to +25% | Oil price impact range |
| Stabilization floor (days to partial recovery) | 45–60 days | Recovery baseline |

**Analyst's note:** The study identifies asymmetric vulnerability — developing economies absorb the highest food/energy shock while advanced economies experience more financial market volatility. The findings suggest permanent (not transient) changes in supply chain configurations.

---

### 2. Maritime Network Blockages

**Full Citation:**
Zhao, L.T., et al. (2024). "Modeling the dynamic impacts of maritime network blockage on global supply chains." *The Innovation*, 5(4), June 2024. (Tsinghua University)

**Key Quantitative Findings:**

| Finding | Value | Application |
|---|---|---|
| Global losses from 6-day Suez blockage (2021) | ~$136.9B | Calibration baseline |
| Daily global trade value (2021 reference) | ~$58.6B USD | Nonlinear Loss formula denominator |
| Base loss coefficient | 0.12 | 12% of daily trade value disrupted |
| Exponential growth rate | 0.1 per day | Loss compounds per day of blockage |
| India's share of global losses (disproportionate) | ~75% ($102B, 3.8% GDP) | Regional exposure note |
| Recovery multiplier (high-utilization chokepoints) | 1.73× | Hysteresis buffer for recovery estimate |

**Loss formula (Zhao-Tsinghua Nonlinear Loss Rule):**
```
Loss = (Daily_Trade_Value × 0.12) × e^(0.1 × Days_Blocked)
```

**Critical insight:** Losses are **nonlinear** — a 12-day blockage does not cost twice a 6-day blockage. Risk compounds exponentially. This is the core rationale for applying this model to maritime events.

**Two-peak pattern:** The model identifies:
- Peak 1: Direct production interruptions (immediate)
- Peak 2: Indirect losses spreading through supply chain (delayed, larger)

---

### 3. Logistics Friction & Inflationary Triggers

**Full Citation:**
Szentivanyi, N. (2024). "The Impacts of the Red Sea Shipping Crisis." *J.P. Morgan Research*, February 2024.

**Key Quantitative Findings:**

| Finding | Value | Application |
|---|---|---|
| Inflation impact (global core goods, H1 2024) | +0.7 percentage points | Macroeconomic transmission |
| Transit time increase (Cape rerouting vs. Suez) | ~30% (+10–12 days) | Logistics delay baseline |
| Effective global container capacity reduction | ~9% | Supply constraint magnitude |
| Freight cost surge (Asia–Europe routes) | ~5× (500%) | Shipping cost shock |

**Just-in-time vulnerability:** The report documents that JIT manufacturing systems caused cascading production shutdowns in European auto plants due to component delays from Asia. This demonstrates the "echelon proximity" risk — the closer the disruption to the consumer end of the chain, the more severe the impact.

---

### 4. Firm-Level Economic Consequences

**Full Citation:**
Schmitt, T., Kumar, S., Stecke, K., Glover, F., & Ehlen, M. (2015). "Modeling Economic Consequences of Supply Chain Disruptions." Sandia National Laboratories / *Omega*.

**Key Quantitative Findings:**

| Finding | Value | Application |
|---|---|---|
| Decrease in operating income post-disruption | −107% (average) | Firm-level impact baseline |
| Cost increase post-disruption | +11% | Cost transmission factor |
| Sales growth reduction post-disruption | −7% | Revenue impact |
| Share-price volatility increase (1-year window) | +13.5% | Market volatility benchmark |
| Stock return penalty (3-year window) | −33% to −40% | Long-term financial impact |
| Firms taking >1 month to recover | ~36% | Recovery distribution |

**Echelon Proximity Rule:** Disruptions occurring closer to the end consumer result in costlier and longer-lasting impacts than those further upstream. This should inform how you weight risk scores for different supply chain positions.

---

## Applied Constants for Risk Engine

Quick-reference table for the risk_calculator.py implementation:

```python
# From Zhao et al. (2024) — Nonlinear Loss Rule
DAILY_TRADE_VALUE_USD       = 58_600_000_000   # $58.6B reference (2021)
MARITIME_LOSS_COEFFICIENT   = 0.12              # Base loss per day
MARITIME_EXPONENTIAL_RATE   = 0.10              # Nonlinear growth factor
MARITIME_RECOVERY_HYSTERESIS = 1.73             # Recovery time multiplier

# From Sarwar & Rye (2025) — Geopolitical Energy Premium
GEOPOLITICAL_OIL_PREMIUM_LOW  = 15.0    # % minimum immediate Brent spike
GEOPOLITICAL_OIL_PREMIUM_HIGH = 25.0    # % maximum immediate Brent spike
GEOPOLITICAL_RECOVERY_DAYS    = 52.5    # Midpoint of 45–60 day stabilization floor

# From Schmitt et al. (2015) — Firm-Level Baselines
FIRM_VOLATILITY_INCREASE_AVG  = 13.5    # % average share-price volatility increase
FIRM_RECOVERY_FRACTION        = 0.36    # Share of firms taking >30 days to recover
FIRM_OPERATING_INCOME_IMPACT  = -107.0  # % average operating income change
```

---

## Validation Against Historical Actuals

See `docs/refs/historical_events.md` for event-specific expected ranges.

These academic benchmarks should be cross-referenced when:
- Calibrating the Nonlinear Loss model for maritime events
- Sanity-checking energy price impact magnitudes for geopolitical events
- Explaining methodology to stakeholders / in portfolio presentations

---

## Critical Reminders

1. **Use these constants exactly** — do not modify without flagging
2. **Apply Nonlinear Loss ONLY for maritime event types**
3. **Do not cite these papers as supporting current events** — use them for methodology attribution
4. **If a constant seems off during validation**, FLAG IT rather than adjusting silently
