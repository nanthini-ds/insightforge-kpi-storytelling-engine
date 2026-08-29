"""
DETECT stage.

Separates real KPI shifts from normal seasonal/weekly noise using a
classic STL-style decomposition (trend + weekly seasonality) and a
rolling z-score on the residual. This mirrors the deck's "statistical
model separates real shifts from normal seasonal noise" step.

No ML framework dependency beyond numpy/pandas/scipy so it runs anywhere.
"""
import numpy as np
import pandas as pd


def _weekly_seasonal_component(series: pd.Series) -> pd.Series:
    """Average deviation from a centered rolling mean, by day-of-week."""
    trend = series.rolling(window=7, center=True, min_periods=1).mean()
    detrended = series - trend
    dow = series.index.dayofweek
    seasonal_avg = pd.Series(detrended.values, index=dow).groupby(level=0).mean()
    return pd.Series(dow, index=series.index).map(seasonal_avg)


def detect_anomalies(df: pd.DataFrame, region: str, z_thresh: float = 2.2) -> pd.DataFrame:
    """
    df: columns [date, region, revenue]
    Returns a dataframe indexed by date with columns:
      revenue, trend, seasonal, residual, z_score, is_anomaly, pct_vs_trend
    """
    sub = df[df["region"] == region].copy()
    sub["date"] = pd.to_datetime(sub["date"])
    sub = sub.set_index("date").sort_index()

    trend = sub["revenue"].rolling(window=7, center=True, min_periods=3).mean()
    seasonal = _weekly_seasonal_component(sub["revenue"])
    expected = trend + seasonal.fillna(0)
    residual = sub["revenue"] - expected

    resid_std = residual.rolling(window=14, min_periods=5).std()
    resid_std = resid_std.fillna(residual.std())
    z = residual / resid_std.replace(0, np.nan)

    out = pd.DataFrame({
        "revenue": sub["revenue"],
        "trend": trend,
        "seasonal": seasonal,
        "expected": expected,
        "residual": residual,
        "z_score": z,
    })
    out["is_anomaly"] = out["z_score"].abs() >= z_thresh
    out["pct_vs_trend"] = (out["revenue"] - out["trend"]) / out["trend"] * 100
    return out


def summarize_anomalies(anomaly_df: pd.DataFrame) -> list[dict]:
    """
    Collapse consecutive anomalous days into incidents (start, end, magnitude),
    since a real-world shift usually spans several days, not one isolated point.
    """
    flagged = anomaly_df[anomaly_df["is_anomaly"]].copy()
    if flagged.empty:
        return []

    incidents = []
    current_start = None
    prev_date = None
    for date, row in flagged.iterrows():
        if current_start is None:
            current_start = date
        elif prev_date is not None and (date - prev_date).days > 1:
            incidents.append((current_start, prev_date))
            current_start = date
        prev_date = date
    incidents.append((current_start, prev_date))

    results = []
    for start, end in incidents:
        window = anomaly_df.loc[start:end]
        avg_pct = window["pct_vs_trend"].mean()
        results.append({
            "start": start.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
            "avg_pct_vs_trend": round(float(avg_pct), 2),
            "max_abs_z": round(float(window["z_score"].abs().max()), 2),
            "direction": "drop" if avg_pct < 0 else "spike",
        })
    return results
