# Supply Chain Event Impact Analyzer — Project Manifest

## Project Overview

**Goal:** A quantitative engine that measures the transmission of logistical shocks into global energy and commodity markets using real FRED API data.

**Differentiator:** This is NOT a text summarizer or RAG chatbot. It is quantitative risk analysis — commodity prices are ground truth, and the system calculates actual economic impact, not news summaries.

---

## ⚖️ Analyst's Shield Disclaimer

This tool is a **Quantitative Supply Chain Risk Study**. All events are treated as standardized data triggers:
- Transit Closures (maritime blockages, port shutdowns)
- Energy Premiums (geopolitical supply disruptions)
- Demand Shocks (recession, pandemic-driven contraction)
- Financial Contagion (credit crisis propagation)

This framing provides operational research for supply chain planning. It is not political commentary.

---

## Core Value Proposition

**What it does:**
1. User inputs a supply chain event (e.g., "Red Sea Disruptions") + date + event type
2. Fetches commodity price time series from FRED API
3. Analyzes before/after price behavior using log returns
4. Quantifies: price change %, peak impact, volatility spike, recovery timeline
5. Calculates composite risk score (0–100) with Nonlinear Loss for maritime events
6. Displays interactive charts and metric dashboards

**Why it matters:**
- Turns "Russia invaded Ukraine, oil went up" into "Brent +22% in 10 days, volatility +47%, partial recovery at 52 days"
- Demonstrates analyst thinking + engineering execution + domain knowledge
- Portfolio differentiator: quantitative analyst mindset vs. bootcamp chatbot builder

---

## Tech Stack

| Component | Tool | Rationale |
|---|---|---|
| Data | FRED API via `fredapi` | Free, high-quality, Python-native |
| Processing | Python 3.10+, pandas, numpy | Time series manipulation |
| Visualization | Plotly | Interactive, embeds cleanly in Streamlit |
| Frontend | Streamlit | Fast to build, free cloud deployment |
| Hosting | Streamlit Cloud | Public URL, zero DevOps |

---

## Project Structure

```
supply-chain-impact-analyzer/
├── CLAUDE.md                          ← Claude Code instructions (READ FIRST)
├── PROJECT_MANIFEST.md               ← This file
├── README.md                          ← Portfolio documentation
├── requirements.txt                   ← Pinned dependencies
├── .gitignore
├── .streamlit/
│   └── secrets.toml                  ← FRED API key (gitignored)
├── docs/
│   └── refs/
│       ├── commodity_indicators.md    ← Layer C: FRED codes and priorities
│       ├── statistical_methods.md     ← Layer C: Formulas and log returns
│       ├── academic_benchmarks.md     ← Layer C: Quantitative constants
│       └── historical_events.md       ← Layer C: Test cases and actuals
└── src/
    ├── data_collector.py              ← FRED API integration
    ├── event_analyzer.py              ← Statistical analysis (log returns)
    ├── risk_calculator.py             ← Risk score + Nonlinear Loss Rule
    └── app.py                         ← Streamlit UI
```

---

## Build Phases

### Phase 1: Data Collection (1 hour)
- `data_collector.py` with FRED API integration
- Fetch, validate, and clean commodity time series
- Forward-fill gaps (limit: 5 days)

### Phase 2: Event Analysis (1.5 hours)
- `event_analyzer.py` with log returns methodology
- Before/after comparison, peak detection, volatility, recovery
- Zhao-Tsinghua Nonlinear Loss for maritime event types

### Phase 3: Streamlit Dashboard (1.5 hours)
- Complete `app.py` UI
- Interactive Plotly charts with event/peak markers
- Metric columns, summary table, risk score
- Example events dropdown, CSV export

### Phase 4: Polish & Deploy (30 minutes)
- README with live demo URL + architecture explanation
- Deploy to Streamlit Cloud
- Validate against 3 historical test cases

---

## Pre-loaded Example Events

| Event | Date | Type | Primary Commodities |
|---|---|---|---|
| Ukraine Invasion | Feb 24, 2022 | Geopolitical | Brent, Natural Gas, Copper |
| COVID-19 Lockdowns | Mar 15, 2020 | Pandemic | Brent, Copper, Aluminum |
| Suez Canal Blockage | Mar 23, 2021 | Maritime | Brent, Natural Gas |
| 2008 Financial Crisis | Sep 15, 2008 | Financial | Brent, Copper, Aluminum, Iron Ore |
| Red Sea Disruptions | Dec 1, 2023 | Maritime | Brent, Natural Gas |

---

## Portfolio Presentation Script

> "I built a supply chain event impact analyzer that quantifies disruption risk using real commodity price data from the Federal Reserve. Instead of summarizing news, it measures actual economic impact — price changes, volatility spikes, recovery timelines.
>
> For example: analyze the Ukraine invasion and see that Brent crude jumped 22% in 10 days, natural gas spiked 35%, and it took 52 days for prices to partially stabilize. All calculated from real FRED data using log returns and before/after event study methodology — the same framework used in peer-reviewed supply chain research.
>
> For maritime events like Suez or Red Sea, I implemented the Zhao-Tsinghua Nonlinear Loss model, which captures how risk compounds exponentially as a blockage duration extends.
>
> It demonstrates data engineering, statistical analysis, domain expertise, and product thinking. Built in one evening using a three-layer knowledge architecture separating library code, project decisions, and domain science. Live demo: [URL]"

---

## Future Extensions

### Phase 5: Semantic Commodity Suggestion (RAG-lite, 1–2 days)

**Problem it solves:** User types "Taiwan Strait tensions" and doesn't know which commodities to analyze. The current UI requires them to already know to pick copper (semiconductors), aluminum (aerospace), and natural gas (LNG rerouting).

**Implementation:** A Claude API call over the extended 25-commodity FRED catalog in `commodity_indicators.md`. The full catalog fits in a single prompt — no vector database or embeddings required at this size.

```python
# Prompt pattern (see commodity_indicators.md for full implementation)
response = claude.messages.create(
    model="claude-sonnet-4-20250514",
    messages=[{
        "role": "user",
        "content": f"Event: {event_name}\nType: {event_type}\n"
                   f"From this catalog: {catalog_json}\n"
                   f"Suggest 3-5 commodities likely to show measurable impact. "
                   f"Return JSON with commodity keys and one-sentence rationale each. "
                   f"Flag relevant exposures NOT in this catalog."
    }]
)
```

**Output in UI:** `st.info()` box showing suggested commodities with rationale, one-click "Add to analysis" button per suggestion.

**Why no vector DB:** At 25–30 commodities, embedding + similarity search adds infrastructure complexity with no accuracy benefit. Upgrade to embeddings only if catalog exceeds ~200 entries.

---

### Phase 6: True RAG over Multi-Source Catalog (1–2 weeks)

**When to do this:** If you want to go beyond FRED — adding IMF commodity indices, LME spot prices, World Bank Pink Sheet, or proprietary indices.

**Architecture at that point:**
- Embed commodity descriptions + relevance tags
- Store in a lightweight vector store (ChromaDB or Pinecone free tier)
- Query by event description embedding at runtime
- Return top-k commodities with source + FRED/non-FRED flag

**Note:** At this stage you'd also need to handle non-FRED data pipelines, which adds meaningful complexity. Phase 5 (Claude API over FRED catalog) should cover 80% of use cases at 5% of the effort.

---

### Other Future Extensions

- Agricultural commodity deep-dive (wheat, corn, urea for food supply chain events)
- Predictive layer: XGBoost + Monte Carlo simulation over historical event patterns
- Multi-event correlation analysis (overlapping disruptions, compound risk)
- Industry-specific risk profiles (semiconductor, automotive, pharma, aerospace)
- Real-time monitoring with alert thresholds (requires paid data source)
- Automated event detection from news feed → trigger analysis pipeline

**For tonight: Ship the MVP. Get the live demo URL. The roadmap sells itself.**
