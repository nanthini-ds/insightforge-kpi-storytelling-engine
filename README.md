InsightForge — KPI Storytelling Engine

Round 2 Prototype README

Turn KPI movements into evidence-grounded business explanations and recommended next actions.

1. Overview

InsightForge is a working prototype for Business Intelligence that detects material KPI movements, correlates them with supporting business signals, and converts the evidence into persona-aware recommendations and plain-language narratives.

Core pipeline:

Detect → Correlate → Recommend → Narrate

The prototype is intentionally designed around illustrative/synthetic data so the core mechanism can be demonstrated without proprietary enterprise data.

2. Problem

Business teams can see that a KPI has moved, but understanding why it moved and what to do next often requires manual investigation across multiple data sources.

InsightForge addresses this gap by connecting KPI anomaly detection with structured and unstructured evidence, confidence-aware reasoning, and actionable recommendations.

3. Solution

Detect

Decomposes regional revenue into trend and weekly seasonality.

Computes residual rolling z-scores.

Flags statistically meaningful shifts rather than routine weekly noise.

Correlate

Searches the incident window for matching pricing/inventory events.

Examines support-ticket spikes and common terms.

Uses relevant news signals when available.

Recommend

Converts the detected movement and evidence into practical next steps.

Narrate

Generates a concise business brief.

Includes explanation and confidence.

Provides an explicit low-evidence path instead of inventing a cause.

Uses Claude when configured, with a deterministic offline fallback.

4. Architecture

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

5. Repository Structure

insightforge-kpi-storytelling-engine/
├── app.py
├── data_gen.py
├── detect.py
├── correlate.py
├── narrate.py
├── requirements.txt
├── README.md
└── prototype screenshots

6. Demo Data

data_gen.py generates illustrative daily data for four regions:

Revenue

Support tickets

Pricing/inventory events

News headlines

The generator injects a realistic incident involving a 3-day SKU-2291 stockout in the West region compounded by a competitor promotion.

7. Installation

pip install -r requirements.txt

8. Run

streamlit run app.py

The application opens locally at:

http://localhost:8501

9. Claude Narration

The prototype works without an API key using a deterministic fallback template.

To enable Claude-generated briefs:

export ANTHROPIC_API_KEY=your_api_key_here
streamlit run app.py

Never commit API keys to GitHub.

10. Key Features

KPI anomaly detection

Trend and seasonality analysis

Cross-signal correlation

Structured + unstructured evidence

Persona-aware views

Configurable anomaly sensitivity

Confidence-aware narratives

Claude narration

Offline fallback

Executive brief generation

11. Prototype Screenshots

The repository contains screenshots for:

Detect stage

Correlate stage

Generated Executive Brief

Sales Manager view

Regional Director view

12. Current Scope & Limitations

Uses synthetic/illustrative data rather than live enterprise connectors.

Correlation is lightweight and can be extended with hybrid retrieval.

Production deployment would require stronger governance, authentication/authorization, monitoring, and source connectors.

The anomaly detector can be replaced with other statistical or BI-native methods.

13. Production Extension

Future development can include:

BI/warehouse API connectors.

Customer-support system connectors.

Internal event-log and approved news connectors.

Hybrid embedding/BM25 retrieval.

Analyst feedback loops.

Stronger lineage and access controls.

Runtime telemetry, model-call and cost monitoring.

Continuous evaluation and confidence calibration.

14. Recommended Demo Flow

Select region and persona.

Show actual revenue versus expected trend.

Demonstrate the flagged anomaly.

Open Correlate and show supporting evidence.

Explain the confidence level.

Generate the executive brief.

Show persona-specific recommendations.

Demonstrate offline fallback if required.

15. Round 2 Alignment

The prototype demonstrates the BusinessIntelligence.ai direction through:

KPI movement detection

Cross-source evidence correlation

Persona-aware narratives

Confidence handling

Action recommendations

Further validation/extension areas include multiple connected KPIs/data sources, semantic definitions, sparse-history handling, role-based security, lineage, LLM/non-LLM separation, and runtime telemetry.

Repository

https://github.com/nanthini-ds/insightforge-kpi-storytelling-engine
