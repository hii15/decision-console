from __future__ import annotations

import pandas as pd

from data_processing.metrics_engine import PURCHASE_EVENT_NAMES


def compare_liveops_impact(
    installs: pd.DataFrame,
    events: pd.DataFrame,
    event_start: str,
    event_end: str,
    baseline_days: int | None = None,
) -> pd.DataFrame:
    installs = installs.copy()
    installs["install_date"] = pd.to_datetime(installs["install_time"]).dt.date
    event_start_dt = pd.to_datetime(event_start).date()
    event_end_dt = pd.to_datetime(event_end).date()

    names = events["event_name"].astype(str).str.lower() if "event_name" in events.columns else None
    purchase_events = events[names.isin(PURCHASE_EVENT_NAMES)].copy() if names is not None else events.copy()

    liveops = installs[installs["install_date"].between(event_start_dt, event_end_dt)]

    duration = (event_end_dt - event_start_dt).days + 1
    baseline_days = baseline_days or duration
    baseline_end = event_start_dt - pd.Timedelta(days=1)
    baseline_start = baseline_end - pd.Timedelta(days=baseline_days - 1)
    baseline = installs[installs["install_date"].between(baseline_start, baseline_end)]

    def _d7_ltv(cohort: pd.DataFrame) -> tuple[float, int]:
        if cohort.empty:
            return 0.0, 0
        merged = cohort[["user_key", "install_time"]].merge(purchase_events, on="user_key", how="left")
        merged["day_diff"] = (merged["event_time"] - merged["install_time"]).dt.days
        rev = merged.loc[merged["day_diff"].between(0, 7, inclusive="both"), "revenue"].sum()
        installs_n = cohort["user_key"].nunique()
        return (rev / installs_n if installs_n else 0.0), installs_n

    liveops_ltv, liveops_n = _d7_ltv(liveops)
    baseline_ltv, baseline_n = _d7_ltv(baseline)

    return pd.DataFrame(
        {
            "event_start": [event_start_dt],
            "event_end": [event_end_dt],
            "baseline_start": [baseline_start],
            "baseline_end": [baseline_end],
            "liveops_d7_ltv": [liveops_ltv],
            "baseline_d7_ltv": [baseline_ltv],
            "impact": [liveops_ltv - baseline_ltv],
            "liveops_sample": [liveops_n],
            "baseline_sample": [baseline_n],
        }
    )
