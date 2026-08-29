# InsightForge — KPI Storytelling Engine

**InsightForge** is a working prototype that turns KPI movements into evidence-grounded business explanations and actionable recommendations.

It follows a simple four-stage pipeline:

**Detect → Correlate → Recommend → Narrate**

Instead of manually investigating why a KPI changed, InsightForge automatically detects unusual movements, connects them with supporting business signals, evaluates confidence, and generates a concise business brief.

---

## 1. Overview

InsightForge is a prototype for Business Intelligence that detects material KPI movements, correlates them with structured and unstructured evidence, and converts the findings into persona-aware recommendations and plain-language narratives.

The prototype uses synthetic data so the complete workflow can be demonstrated without requiring proprietary enterprise data.

---

## 2. Problem

Business teams can easily see that a KPI has changed, but understanding **why it changed** and **what action should be taken next** often requires manual investigation across multiple data sources.

InsightForge addresses this problem by combining:

* KPI anomaly detection
* Cross-source evidence correlation
* Confidence-aware reasoning
* Action recommendations
* Plain-language business narratives

---

## 3. Solution

### Detect

* Decomposes regional revenue into trend and weekly seasonality.
* Calculates rolling z-scores on residuals.
* Identifies statistically meaningful KPI shifts.
* Reduces false alerts caused by normal weekly patterns.

### Correlate

For a detected incident, the system searches the surrounding time and region window for:

* Pricing events
* Inventory events
* Support-ticket spikes
* Common support-ticket terms
* Relevant news signals

### Recommend

Converts the detected KPI movement and supporting evidence into practical next steps.

### Narrate

Generates a concise business brief containing:

* Headline
* Plain-language explanation
* Confidence level
* Supporting evidence
* 2–3 ranked next actions
* An explicit "not enough evidence" path when evidence is insufficient

Claude can be used for AI-generated narration. If no API key is available, the application automatically uses a deterministic offline fallback.

---

## 4. Architecture

```text
Synthetic / Uploaded Data
          |
          v
       Detect
          |
          v
      Correlate
          |
          v
 Confidence Assessment
          |
          v
      Recommend
          |
          v
       Narrate
          |
          v
Executive / Persona-aware Brief
```

---

## 5. Repository Structure

```text
insightforge-kpi-storytelling-engine/
│
├── app.py
├── data_gen.py
├── detect.py
├── correlate.py
├── narrate.py
├── requirements.txt
├── README.md
└── screenshots/
```

---

## 6. What's Inside

| File               | Pipeline Stage      | Description                                                                                               |
| ------------------ | ------------------- | --------------------------------------------------------------------------------------------------------- |
| `data_gen.py`      | Data Generation     | Generates synthetic revenue, support tickets, pricing/inventory events, and news headlines.               |
| `detect.py`        | Detect              | Detects statistically meaningful KPI movements using trend, seasonality, residuals, and rolling z-scores. |
| `correlate.py`     | Correlate           | Connects detected incidents with pricing, inventory, support, and news evidence.                          |
| `narrate.py`       | Recommend + Narrate | Generates evidence-grounded explanations, confidence levels, and recommended actions.                     |
| `app.py`           | UI                  | Streamlit application connecting all pipeline stages.                                                     |
| `requirements.txt` | Setup               | Contains the required Python dependencies.                                                                |

---

## 7. Demo Data

The prototype generates illustrative daily data for four regions:

* Revenue
* Support tickets
* Pricing events
* Inventory events
* News headlines

The generator includes a realistic example incident:

**A 3-day SKU-2291 stockout in the West region combined with a competitor promotion.**

This incident demonstrates how InsightForge can automatically reconstruct a plausible business explanation from multiple evidence sources.

---

## 8. Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

---

## 9. Run the Application

Start the Streamlit application:

```bash
streamlit run app.py
```

The application will open locally at:

```text
http://localhost:8501
```

### Recommended Demo

1. Select the **West** region.
2. Select a persona.
3. Show the revenue movement.
4. Open the detected anomaly.
5. Explore the correlated evidence.
6. Review the confidence level.
7. Generate the executive brief.
8. Show persona-specific recommendations.

---

## 10. Claude Narration

InsightForge can use Claude to generate natural-language business briefs.

The application also works without an API key using a deterministic offline fallback.

To enable Claude-generated narration, configure the environment variable:

```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

Then run:

```bash
streamlit run app.py
```

The sidebar indicates the active mode:

* 🟢 Claude API
* 🟡 Offline fallback

**Never commit API keys or other secrets to GitHub.**

---

## 11. Key Features

* KPI anomaly detection
* Trend and seasonality analysis
* Cross-signal correlation
* Structured + unstructured evidence
* Confidence-aware narratives
* Persona-aware views
* Action recommendations
* Claude-powered narration
* Offline fallback
* Executive brief generation
* Configurable anomaly sensitivity
* Downloadable executive brief

---

## 12. Prototype Screenshots

The prototype includes screenshots demonstrating:

* KPI movement detection
* Detect stage
* Correlate stage
* Generated Executive Brief
* Sales Manager view
* Regional Director view
* Persona switching

Screenshots can be stored inside the `screenshots/` directory.

Example:

```text
screenshots/
├── dashboard.png
├── detect.png
├── correlate.png
├── executive-brief.png
└── persona-switch.png
```

---

## 13. Current Scope & Limitations

The current prototype uses synthetic and illustrative data.

Limitations include:

* No live enterprise data connectors
* Lightweight correlation logic
* Synthetic KPI and event data
* Prototype-level authentication and governance
* Limited historical data handling

The anomaly detector can also be replaced with other statistical or BI-native methods.

---

## 14. Production Extension

The prototype can be extended toward production by adding:

### Data Connectors

* Power BI / Tableau REST APIs
* Zendesk / Freshdesk APIs
* Internal event logs
* Approved news APIs
* Enterprise data warehouses

### Advanced Retrieval

The keyword-based correlation system can be replaced with:

* Embedding-based retrieval
* BM25 search
* Hybrid retrieval
* Semantic search

### Advanced Detection

The current detector can be replaced with:

* Prophet
* ESD-based detection
* BI-native anomaly detection
* Other statistical forecasting methods

### Feedback Loop

Analysts can provide feedback such as:

* Helpful
* Not helpful

This feedback can be used to improve confidence thresholds and recommendation quality.

### Enterprise Readiness

Future production development can include:

* Role-based access control
* Data lineage
* Authentication
* Monitoring
* Runtime telemetry
* Model-call monitoring
* Cost monitoring
* Continuous evaluation
* Confidence calibration

---

## 15. Why This Architecture?

Each pipeline stage is implemented as a separate module.

This makes the system:

* Easy to understand
* Independently testable
* Easy to demonstrate
* Easy to extend
* Easy to replace individual components

The narration system is also designed to avoid inventing explanations when evidence is insufficient.

When evidence is ambiguous, InsightForge can explicitly communicate uncertainty instead of guessing the cause.

---

## 16. Round 2 Alignment

The prototype demonstrates the Business Intelligence solution through:

* **KPI Movement Detection**
* **Cross-source Evidence Correlation**
* **Confidence Handling**
* **Action Recommendations**
* **Persona-aware Narratives**
* **AI-powered Business Narration**
* **Executive Brief Generation**

The architecture follows the core solution:

**Detect → Correlate → Recommend → Narrate**

---

## 17. Demo Incident

Example:

**Region:** West
**SKU:** SKU-2291
**Incident:** 3-day stockout
**Additional Signal:** Competitor promotion

InsightForge identifies the KPI movement, searches related evidence, evaluates the available signals, and produces a business explanation with recommended next actions.

---

## 18. Future Scope

Future versions can support:

* Real-time KPI monitoring
* Multiple connected business KPIs
* Enterprise data sources
* Advanced semantic search
* Automated alerting
* Analyst feedback learning
* Stronger security and governance
* Production-scale deployment

---

## 19. Project Summary

InsightForge demonstrates how AI can transform raw KPI movements into **evidence-grounded business stories and actionable decisions**.

Instead of simply telling a business user that:

> "Revenue decreased."

InsightForge aims to answer:

> **"What changed, what evidence supports the explanation, how confident are we, and what should we do next?"**

**Detect → Correlate → Recommend → Narrate**
