import os
import json
import io
import time
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from data_gen import generate, OUT_DIR
from detect import detect_anomalies, summarize_anomalies
from correlate import gather_evidence
from narrate import generate_brief

st.set_page_config(page_title="InsightForge — KPI Storytelling Engine", layout="wide")
st.markdown("""
<style>
    .block-container {max-width: 1450px; padding-top: 2rem; padding-bottom: 3rem;}
    [data-testid="stMetric"] {background: #172033; border: 1px solid #2b3850; border-radius: 8px; padding: 1rem;}
    .section-rule {border-top: 1px solid #2b3850; margin: 1.5rem 0 1rem;}
</style>
""", unsafe_allow_html=True)


def build_pdf(brief: dict, incident: dict, region: str) -> bytes:
    buffer = io.BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.7 * inch,
                                 leftMargin=0.7 * inch, topMargin=0.7 * inch,
                                 bottomMargin=0.7 * inch)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("InsightForge Executive Brief", styles["Title"]),
        Spacer(1, 0.15 * inch),
        Paragraph(f"<b>Region:</b> {region}", styles["BodyText"]),
        Paragraph(f"<b>Investigation Window:</b> {incident['start']} to {incident['end']}", styles["BodyText"]),
        Spacer(1, 0.15 * inch),
        Paragraph(f"<b>Headline:</b> {brief['headline']}", styles["BodyText"]),
        Spacer(1, 0.1 * inch),
        Paragraph(f"<b>Explanation:</b> {brief['explanation']}", styles["BodyText"]),
        Spacer(1, 0.1 * inch),
        Paragraph(f"<b>Confidence:</b> {brief['confidence']}", styles["BodyText"]),
        Paragraph(f"<b>Confidence Reason:</b> {brief['confidence_reason']}", styles["BodyText"]),
        Spacer(1, 0.1 * inch),
        Paragraph("<b>Recommended Actions:</b>", styles["BodyText"]),
    ]
    story.extend(Paragraph(f"{index}. {action}", styles["BodyText"])
                 for index, action in enumerate(brief["recommended_actions"], 1))
    document.build(story)
    return buffer.getvalue()

# ---------- Data ----------
if not os.path.exists(os.path.join(OUT_DIR, "revenue.csv")):
    generate()
demo_revenue_df = pd.read_csv(os.path.join(OUT_DIR, "revenue.csv"))

REQUIRED_REVENUE_COLS = {"date", "region", "revenue"}

st.title("📊 InsightForge — KPI Storytelling Engine")
st.caption("An AI layer that explains every KPI move in plain language, the moment it happens.")
processing_started = time.perf_counter()

uploaded_tickets_df = None
uploaded_events = None
uploaded_news = None

with st.sidebar:
    st.header("Data source")
    data_source = st.radio(
        "Revenue / KPI data",
        ["Upload my own CSV (default)", "Use demo dataset"],
        index=0,
    )

    revenue_df = demo_revenue_df
    using_custom_data = False

    if data_source == "Upload my own CSV (default)":
        st.caption("CSV must have columns: `date`, `region`, `revenue` (one row per day per region).")
        uploaded_file = st.file_uploader("Revenue CSV", type=["csv"], key="revenue_upload")
        if uploaded_file is not None:
            try:
                custom_df = pd.read_csv(uploaded_file)
                missing = REQUIRED_REVENUE_COLS - set(custom_df.columns.str.lower())
                custom_df.columns = [c.lower() for c in custom_df.columns]
                if missing:
                    st.error(f"Missing required column(s): {', '.join(missing)}. Using demo dataset instead.")
                else:
                    custom_df["date"] = pd.to_datetime(custom_df["date"]).dt.strftime("%Y-%m-%d")
                    revenue_df = custom_df[["date", "region", "revenue"]]
                    using_custom_data = True
                    st.success(f"Loaded {len(revenue_df)} rows across {revenue_df['region'].nunique()} region(s).")
            except Exception as e:
                st.error(f"Couldn't read that file ({e}). Using demo dataset instead.")
        else:
            st.info("No file uploaded yet — showing demo dataset below until you do.")

        with st.expander("Optional: also upload correlation signals"):
            st.caption("Without these, Correlate still runs using the bundled demo tickets/events/news as context.")
            tix_file = st.file_uploader("Support tickets CSV (`date`, `region`, `ticket_text`)", type=["csv"], key="tix")
            if tix_file is not None:
                try:
                    uploaded_tickets_df = pd.read_csv(tix_file, parse_dates=["date"])
                except Exception as e:
                    st.error(f"Couldn't read tickets file ({e}).")

            ev_file = st.file_uploader("Events JSON (`date`, `region`, `type`, `detail`)", type=["json"], key="ev")
            if ev_file is not None:
                try:
                    uploaded_events = json.load(ev_file)
                except Exception as e:
                    st.error(f"Couldn't read events file ({e}).")

            news_file = st.file_uploader("News JSON (`date`, `headline`)", type=["json"], key="news")
            if news_file is not None:
                try:
                    uploaded_news = json.load(news_file)
                except Exception as e:
                    st.error(f"Couldn't read news file ({e}).")

    st.divider()
    st.header("Controls")
    persona = st.selectbox("Persona", ["Sales Manager", "Regional Director"])
    region = st.selectbox("Region", sorted(revenue_df["region"].unique()), index=0)
    z_thresh = st.slider("Anomaly sensitivity (z-score threshold)", 1.0, 4.0, 2.2, 0.1)
    st.divider()
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    narration_mode = "Claude API" if has_key else "Offline Fallback"
    st.write("**Narration engine:**", "🟢 Claude API" if has_key else "🟡 Offline fallback template")
    if not has_key:
        st.caption("Set ANTHROPIC_API_KEY to have Claude write the briefs instead of the template.")

if using_custom_data:
    st.caption("📁 Using your uploaded dataset.")
else:
    st.caption("🧪 No file uploaded yet — showing the built-in demo dataset. Upload a CSV in the sidebar to use real data.")

# ---------- 1. DETECT ----------
st.subheader("1️⃣ Detect")
anomaly_df = detect_anomalies(revenue_df, region, z_thresh=z_thresh)
incidents = summarize_anomalies(anomaly_df)

fig = go.Figure()
fig.add_trace(go.Scatter(x=anomaly_df.index, y=anomaly_df["revenue"], name="Actual revenue",
                          line=dict(color="#2563EB", width=2)))
fig.add_trace(go.Scatter(x=anomaly_df.index, y=anomaly_df["expected"], name="Expected (trend+seasonal)",
                          line=dict(color="#94A3B8", width=1.5, dash="dot")))
anom_points = anomaly_df[anomaly_df["is_anomaly"]]
fig.add_trace(go.Scatter(x=anom_points.index, y=anom_points["revenue"], mode="markers",
                          name="Flagged anomaly", marker=dict(color="#DC2626", size=9, symbol="x")))
fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10),
                   legend=dict(orientation="h", yanchor="bottom", y=1.02))
st.plotly_chart(fig, use_container_width=True)

if not incidents:
    st.info(f"No anomalies flagged for {region} at this sensitivity — try lowering the threshold.")
    st.stop()

st.write(f"**{len(incidents)} incident(s) flagged** for {region}:")
incident_labels = [
    f"{i['start']} → {i['end']} · {i['direction']} {i['avg_pct_vs_trend']:+.1f}% vs trend (|z|={i['max_abs_z']})"
    for i in incidents
]
chosen_idx = st.radio("Select an incident to investigate:", range(len(incidents)),
                       format_func=lambda i: incident_labels[i], index=0)
incident = incidents[chosen_idx]

# ---------- 2. CORRELATE ----------
st.subheader("2️⃣ Correlate")
evidence = gather_evidence(
    region, incident["start"], incident["end"],
    tickets=uploaded_tickets_df, events=uploaded_events, news=uploaded_news,
)
processing_time = time.perf_counter() - processing_started
estimated_input_tokens = 350 + len(evidence["top_ticket_terms"]) * 15 + len(persona)
estimated_output_tokens = 450
estimated_token_usage = estimated_input_tokens + estimated_output_tokens
estimated_cost = (estimated_input_tokens * 3 + estimated_output_tokens * 15) / 1_000_000

with st.sidebar:
    st.divider()
    st.header("System Status")
    st.metric("Processing Time", f"{processing_time:.2f}s")
    st.metric("Narration Mode", narration_mode)
    st.metric("Estimated Token Usage", f"{estimated_token_usage:,}")
    st.metric("Estimated Cost", f"${estimated_cost:.4f}")

confidence_level = (
    "High" if evidence["structured_events"] and evidence["ticket_spike_ratio"] >= 2
    else "Medium" if evidence["structured_events"] else "Low"
)
st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
st.subheader("Dashboard overview")
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
with kpi_col1:
    st.metric("Revenue", f"${anomaly_df['revenue'].iloc[-1]:,.0f}")
with kpi_col2:
    st.metric("Revenue Change (% vs trend)", f"{incident['avg_pct_vs_trend']:+.1f}%")
with kpi_col3:
    confidence_colors = {"High": "#22c55e", "Medium": "#f59e0b", "Low": "#ef4444"}
    st.markdown(f"<span style='color:{confidence_colors[confidence_level]};font-weight:600'>● {confidence_level}</span>", unsafe_allow_html=True)
    st.metric("Confidence Level", confidence_level)
with kpi_col4:
    st.metric("Ticket Spike Ratio", f"{evidence['ticket_spike_ratio']:.1f}x")

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Structured signals (events log)**")
    if evidence["structured_events"]:
        st.table(pd.DataFrame(evidence["structured_events"]))
    else:
        st.caption("No structured events logged in this window.")
    st.markdown("**News / market headlines**")
    if evidence["news_headlines"]:
        for n in evidence["news_headlines"]:
            st.write(f"- {n['date']}: {n['headline']}")
    else:
        st.caption("No relevant headlines found.")

with col2:
    st.markdown("**Unstructured signals (support tickets)**")
    st.metric("Ticket volume in window", evidence["ticket_volume_in_window"],
               delta=f"{evidence['ticket_spike_ratio']}x baseline")
    st.write("Top terms:", ", ".join(evidence["top_ticket_terms"]) or "—")
    with st.expander("Sample ticket text"):
        for t in evidence["sample_ticket_texts"]:
            st.write(f"- {t}")

# ---------- 3 & 4. RECOMMEND + NARRATE ----------
st.subheader("3️⃣ + 4️⃣ Recommend & Narrate")
brief_context = (region, incident["start"], incident["end"], persona)
if st.button("Generate brief", type="primary"):
    with st.spinner("Reasoning over correlated signals..."):
        brief = generate_brief(incident, evidence, persona)
    st.session_state["brief"] = brief
    st.session_state["brief_context"] = brief_context

if st.session_state.get("brief_context") == brief_context:
    brief = st.session_state["brief"]

    conf_color = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}.get(brief.get("confidence"), "⚪")

    st.markdown(f"### {brief['headline']}")
    st.write(brief["explanation"])
    st.write(f"**Confidence:** {conf_color} {brief['confidence']} — {brief['confidence_reason']}")
    st.markdown("**Recommended next steps:**")
    for i, action in enumerate(brief["recommended_actions"], 1):
        st.write(f"{i}. {action}")
    st.caption(f"Source: {brief.get('_source', 'unknown')}")
    st.download_button(
        "Download Executive Brief (PDF)",
        data=build_pdf(brief, incident, region),
        file_name=f"insightforge_{region.lower()}_executive_brief.pdf",
        mime="application/pdf",
    )
else:
    st.caption("Click above to have the engine turn this evidence into a natural-language brief.")
