"""
Generates synthetic data for the KPI Storytelling Engine demo:
- Daily revenue by region (structured KPI, with one injected anomaly)
- Support ticket volume/text (unstructured-ish signal)
- Pricing/promo events (structured signal)
- News/market headlines (unstructured signal)

Everything is seeded for reproducibility and cached to CSV/JSON so the
Streamlit app doesn't regenerate data on every rerun.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import os

SEED = 42
OUT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUT_DIR, exist_ok=True)

REGIONS = ["West", "East", "North", "South"]
N_DAYS = 90
START = datetime(2026, 5, 1)


def generate():
    rng = np.random.default_rng(SEED)
    dates = [START + timedelta(days=i) for i in range(N_DAYS)]

    rows = []
    for region in REGIONS:
        base = {"West": 42000, "East": 38000, "North": 31000, "South": 27000}[region]
        weekly_amp = base * 0.08
        trend = np.linspace(0, base * 0.05, N_DAYS)
        noise = rng.normal(0, base * 0.02, N_DAYS)
        seasonal = weekly_amp * np.sin(np.arange(N_DAYS) * (2 * np.pi / 7))
        revenue = base + trend + seasonal + noise

        # Inject the anomaly described in the deck: West region, 3-day stockout,
        # days 60-62, ~8% drop, compounded by a competitor promo.
        if region == "West":
            revenue[60:63] *= 0.90  # stockout dip
            revenue[61:66] *= 0.965  # competitor promo drag, slightly wider window

        for i, d in enumerate(dates):
            rows.append({"date": d.strftime("%Y-%m-%d"), "region": region,
                         "revenue": round(float(revenue[i]), 2)})

    revenue_df = pd.DataFrame(rows)
    revenue_df.to_csv(os.path.join(OUT_DIR, "revenue.csv"), index=False)

    # Support tickets: spike in West around the stockout
    ticket_rows = []
    ticket_texts = [
        "Customer reports SKU-2291 unavailable at checkout",
        "Backorder complaint for SKU-2291, requesting ETA",
        "Store associate flags empty shelf for SKU-2291 in West region",
        "Customer asks why competitor has stock and we don't",
        "Refund request due to canceled order - out of stock",
    ]
    generic_texts = [
        "General billing question",
        "App login issue reported",
        "Positive feedback on delivery speed",
        "Question about loyalty points",
        "Request to update shipping address",
    ]
    for region in REGIONS:
        for i, d in enumerate(dates):
            if region == "West" and 59 <= i <= 65:
                n = int(rng.integers(8, 15))
                texts = rng.choice(ticket_texts, size=n).tolist()
            else:
                n = int(rng.integers(1, 5))
                texts = rng.choice(generic_texts, size=n).tolist()
            for t in texts:
                ticket_rows.append({"date": d.strftime("%Y-%m-%d"), "region": region, "ticket_text": t})
    pd.DataFrame(ticket_rows).to_csv(os.path.join(OUT_DIR, "tickets.csv"), index=False)

    # Structured pricing/promo + inventory events log
    events = [
        {"date": dates[58].strftime("%Y-%m-%d"), "region": "West", "type": "inventory",
         "detail": "SKU-2291 stock depleted at West DC (fulfillment center #4)"},
        {"date": dates[61].strftime("%Y-%m-%d"), "region": "West", "type": "inventory",
         "detail": "SKU-2291 restock ETA delayed 48h due to carrier backlog"},
        {"date": dates[59].strftime("%Y-%m-%d"), "region": "West", "type": "competitor",
         "detail": "Competitor 'NovaMart' launches 20% off promotion on comparable SKU in West region"},
        {"date": dates[30].strftime("%Y-%m-%d"), "region": "East", "type": "promo",
         "detail": "Internal 10% loyalty promo ran in East region (planned, no anomaly)"},
    ]
    with open(os.path.join(OUT_DIR, "events.json"), "w") as f:
        json.dump(events, f, indent=2)

    # Unstructured news/market headlines
    news = [
        {"date": dates[59].strftime("%Y-%m-%d"), "headline": "NovaMart undercuts rivals with aggressive West Coast pricing push"},
        {"date": dates[57].strftime("%Y-%m-%d"), "headline": "Regional carrier reports shipping delays amid port congestion"},
        {"date": dates[62].strftime("%Y-%m-%d"), "headline": "Consumer sentiment index steady; no broad demand shift reported"},
        {"date": dates[10].strftime("%Y-%m-%d"), "headline": "Industry report: seasonal demand for category expected to rise in Q3"},
    ]
    with open(os.path.join(OUT_DIR, "news.json"), "w") as f:
        json.dump(news, f, indent=2)

    return revenue_df


if __name__ == "__main__":
    df = generate()
    print(f"Generated {len(df)} revenue rows across {df['region'].nunique()} regions.")
    print("Files written to", OUT_DIR)
