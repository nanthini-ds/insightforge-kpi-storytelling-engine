"""
CORRELATE stage.

Cross-references a flagged KPI incident against:
  - structured signals: pricing/promo & inventory event log
  - unstructured signals: support ticket text, news headlines

This is a lightweight retrieval layer (date-window + region filter +
keyword scoring) that stands in for the "LLM reasoning layer" described
in the deck — in production this would likely be a proper hybrid search
(BM25/embeddings) over each source system.
"""
import json
import os
from collections import Counter
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

STOPWORDS = {"the", "a", "an", "for", "to", "of", "in", "on", "and", "is",
             "at", "our", "we", "due", "with", "why", "don't", "has", "have"}


def _load():
    tickets = pd.read_csv(os.path.join(DATA_DIR, "tickets.csv"), parse_dates=["date"])
    with open(os.path.join(DATA_DIR, "events.json")) as f:
        events = json.load(f)
    with open(os.path.join(DATA_DIR, "news.json")) as f:
        news = json.load(f)
    return tickets, events, news


def gather_evidence(region: str, start: str, end: str, pad_days: int = 2,
                     tickets: pd.DataFrame = None, events: list = None, news: list = None) -> dict:
    """
    tickets/events/news are optional overrides (e.g. user-uploaded files from the
    Streamlit UI). Any left as None falls back to the bundled demo data, so a user
    can upload just their own revenue+tickets and still get news/events context,
    or vice versa.
    """
    demo_tickets, demo_events, demo_news = _load()
    if tickets is None:
        tickets = demo_tickets
    if events is None:
        events = demo_events
    if news is None:
        news = demo_news

    start_dt = pd.to_datetime(start) - pd.Timedelta(days=pad_days)
    end_dt = pd.to_datetime(end) + pd.Timedelta(days=pad_days)

    window_tickets = tickets[
        (tickets["region"] == region) &
        (tickets["date"] >= start_dt) & (tickets["date"] <= end_dt)
    ]
    baseline_tickets = tickets[
        (tickets["region"] == region) &
        ~((tickets["date"] >= start_dt) & (tickets["date"] <= end_dt))
    ]

    ticket_volume_in_window = len(window_tickets)
    ticket_volume_baseline_daily_avg = (
        len(baseline_tickets) / max(baseline_tickets["date"].nunique(), 1)
    )

    words = Counter()
    for t in window_tickets["ticket_text"]:
        for w in t.lower().replace(",", "").replace("-", " ").split():
            if w not in STOPWORDS and len(w) > 2:
                words[w] += 1
    top_ticket_terms = [w for w, _ in words.most_common(6)]

    region_events = [
        e for e in events
        if e["region"] == region and start_dt <= pd.to_datetime(e["date"]) <= end_dt
    ]

    relevant_news = [
        n for n in news
        if start_dt <= pd.to_datetime(n["date"]) <= end_dt
    ]

    return {
        "region": region,
        "window": {"start": start, "end": end},
        "ticket_volume_in_window": ticket_volume_in_window,
        "ticket_volume_baseline_daily_avg": round(ticket_volume_baseline_daily_avg, 1),
        "ticket_spike_ratio": round(
            ticket_volume_in_window / max(ticket_volume_baseline_daily_avg, 0.1), 1
        ),
        "top_ticket_terms": top_ticket_terms,
        "sample_ticket_texts": window_tickets["ticket_text"].drop_duplicates().head(5).tolist(),
        "structured_events": region_events,
        "news_headlines": relevant_news,
    }
