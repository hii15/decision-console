import pandas as pd


def compute_data_quality_metrics(installs_df: pd.DataFrame, events_df: pd.DataFrame) -> dict:
    """Compute lightweight data-quality diagnostics for uploaded installs/events data."""
    installs = installs_df.copy()
    events = events_df.copy()

    installs_rows = len(installs)
    events_rows = len(events)

    installs_invalid_ts = installs["install_time"].isna().sum() if "install_time" in installs.columns else installs_rows
    events_invalid_ts = events["event_time"].isna().sum() if "event_time" in events.columns else events_rows

    installs_invalid_ts_rate = (installs_invalid_ts / installs_rows) if installs_rows else 0.0
    events_invalid_ts_rate = (events_invalid_ts / events_rows) if events_rows else 0.0

    install_ids = set(installs["appsflyer_id"].dropna().astype(str)) if "appsflyer_id" in installs.columns else set()
    event_ids = set(events["appsflyer_id"].dropna().astype(str)) if "appsflyer_id" in events.columns else set()

    matched_event_id_count = len(event_ids.intersection(install_ids))
    unmatched_event_id_count = len(event_ids - install_ids)
    match_rate = (matched_event_id_count / len(event_ids)) if event_ids else 0.0

    purchase_events = 0
    if "event_name" in events.columns:
        purchase_events = int((events["event_name"] == "af_purchase").sum())

    purchase_coverage = (purchase_events / events_rows) if events_rows else 0.0

    missing_revenue_count = 0
    if "revenue" in events.columns:
        missing_revenue_count = int(events["revenue"].isna().sum())
    missing_revenue_rate = (missing_revenue_count / events_rows) if events_rows else 0.0

    quality_score = max(
        0.0,
        100.0
        - installs_invalid_ts_rate * 35.0
        - events_invalid_ts_rate * 35.0
        - (1.0 - match_rate) * 20.0
        - missing_revenue_rate * 10.0,
    )

    return {
        "installs_rows": installs_rows,
        "events_rows": events_rows,
        "installs_invalid_ts": int(installs_invalid_ts),
        "events_invalid_ts": int(events_invalid_ts),
        "installs_invalid_ts_rate": float(installs_invalid_ts_rate),
        "events_invalid_ts_rate": float(events_invalid_ts_rate),
        "event_id_count": int(len(event_ids)),
        "matched_event_id_count": int(matched_event_id_count),
        "unmatched_event_id_count": int(unmatched_event_id_count),
        "event_id_match_rate": float(match_rate),
        "missing_revenue_count": int(missing_revenue_count),
        "missing_revenue_rate": float(missing_revenue_rate),
        "purchase_event_count": int(purchase_events),
        "purchase_event_coverage": float(purchase_coverage),
        "quality_score": float(quality_score),
    }
