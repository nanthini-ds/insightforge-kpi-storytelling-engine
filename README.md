# InsightForge — KPI Storytelling Engine (Working Demo)

A runnable prototype of the pipeline described in your deck: **Detect → Correlate →
Recommend → Narrate**. It explains a KPI move in plain language, grounded in real
correlated evidence, instead of you writing the story by hand.

## What's inside

| File | Pipeline stage | What it does |
|---|---|---|
| `data_gen.py` | — | Generates synthetic daily revenue (4 regions), support tickets, pricing/inventory events, and news headlines. Injects one realistic incident: a 3-day SKU-2291 stockout in the West region compounded by a competitor promo — matching the exact example on your "Solution" slide. |
| `detect.py` | **1. Detect** | Decomposes each region's revenue into trend + weekly seasonality, computes a rolling z-score on the residual, and flags statistically real shifts (not routine weekly noise). |
| `correlate.py` | **2. Correlate** | For a flagged incident, pulls matching structured events (pricing/inventory log) and unstructured signals (support ticket spike + top terms, relevant news headlines) in a date/region window around it. |
| `narrate.py` | **3. Recommend + 4. Narrate** | Sends the anomaly summary + evidence bundle to Claude with a strict JSON-brief prompt: headline, plain-language explanation, confidence level (with an explicit "not enough evidence" path), and 2-3 ranked next steps. Falls back to a deterministic template if no API key is set, so the demo still runs offline. |
| `app.py` | UI | Streamlit app tying all four stages together with an interactive chart and one-click brief generation. |

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

This opens a browser at `http://localhost:8501`. Pick **West** region and the flagged
incident around late June to see the exact stockout + competitor-promo story from your
deck reconstructed automatically from the underlying data.

## Using Claude for narration (recommended for the demo)

Without an API key the app still works end-to-end using a deterministic fallback
template (so it's never broken during judging). To have Claude actually write the
briefs:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
streamlit run app.py
```

The sidebar shows which mode is active (🟢 Claude API / 🟡 Offline fallback).

## Screenshots

Screenshots can be stored in `screenshots/` using these placeholders:

![Dashboard](screenshots/dashboard.png)
![Detect](screenshots/detect.png)
![Correlate](screenshots/correlate.png)
![Executive Brief](screenshots/executive-brief.png)
![Persona Switch](screenshots/persona-switch.png)

## UI Improvements

The dashboard keeps the dark theme and now includes responsive KPI cards, clearer
section dividers, icon-led status cues, persona-aware narratives, runtime metrics,
and a downloadable executive brief PDF.

## Extending this toward production

- **Swap `data_gen.py` for real connectors**: Power BI/Tableau REST API for KPIs,
  Zendesk/Freshdesk API for tickets, an internal events log, a news API.
- **Swap the keyword-scoring in `correlate.py` for embeddings/BM25** hybrid search
  over each source system for better recall on paraphrased signals.
- **Swap the STL-ish detector in `detect.py`** for Prophet, an ESD test, or your BI
  tool's native anomaly detection if it exposes one via API — the rest of the pipeline
  is decoupled from the detection method, it just needs an incident window.
- **Add a feedback loop**: let analysts mark a brief "helpful / not helpful" and use
  that to tune the confidence thresholds over time.

## Why this shape

- Each stage is a separate, independently testable module — mirrors the 4-step
  architecture on your "Our Solution" slide and makes it easy to demo (or swap) one
  stage at a time.
- The narration prompt explicitly instructs Claude to flag low-confidence/ambiguous
  cases rather than hallucinate a cause — this was called out as a requirement in your
  deck ("When evidence is ambiguous, it flags the uncertainty instead of guessing").
