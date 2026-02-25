from __future__ import annotations

import numpy as np
import pandas as pd


PURCHASE_EVENT_NAMES = {"af_purchase", "purchase", "in_app_purchase"}


def _cohort_events(installs: pd.DataFrame, events: pd.DataFrame, max_day: int = 30) -> pd.DataFrame:
    merged = installs[["user_key", "install_time", "media_source", "campaign"]].merge(events, on="user_key", how="left")
    merged["day_diff"] = (merged["event_time"] - merged["install_time"]).dt.days
    return merged[merged["day_diff"].between(0, max_day, inclusive="both")].copy()


def _purchase_events(events: pd.DataFrame) -> pd.DataFrame:
    if "event_name" not in events.columns:
        return events.copy()
    names = events["event_name"].astype(str).str.lower()
    return events[names.isin(PURCHASE_EVENT_NAMES)].copy()


def calculate_media_metrics(installs: pd.DataFrame, events: pd.DataFrame, cost: pd.DataFrame) -> pd.DataFrame:
    installs = installs.copy()
    installs["install_date"] = pd.to_datetime(installs["install_time"]).dt.date

    purchase_events = _purchase_events(events)
    cohort = _cohort_events(installs, purchase_events, max_day=30)

    install_agg = installs.groupby(["media_source", "campaign"], as_index=False).agg(installs=("user_key", "nunique"))

    rev = cohort.groupby(["media_source", "campaign"], as_index=False).agg(
        d1_revenue=("revenue", lambda s: s[cohort.loc[s.index, "day_diff"] <= 1].sum()),
        d7_revenue=("revenue", lambda s: s[cohort.loc[s.index, "day_diff"] <= 7].sum()),
        d30_revenue=("revenue", lambda s: s[cohort.loc[s.index, "day_diff"] <= 30].sum()),
        purchasers=("user_key", "nunique"),
        purchase_revenue=("revenue", "sum"),
    )

    cost_agg = cost.groupby(["media_source", "campaign"], as_index=False).agg(
        spend=("spend", "sum"), impressions=("impressions", "sum"), clicks=("clicks", "sum")
    )

    result = install_agg.merge(rev, on=["media_source", "campaign"], how="left").merge(
        cost_agg, on=["media_source", "campaign"], how="left"
    )
    result = result.fillna(0)

    result["cpi"] = np.where(result["installs"] > 0, result["spend"] / result["installs"], np.nan)
    result["purchase_rate"] = np.where(result["installs"] > 0, result["purchasers"] / result["installs"], 0)
    result["arppu"] = np.where(result["purchasers"] > 0, result["purchase_revenue"] / result["purchasers"], 0)
    result["arpu"] = np.where(result["installs"] > 0, result["purchase_revenue"] / result["installs"], 0)
    result["d1_ltv"] = np.where(result["installs"] > 0, result["d1_revenue"] / result["installs"], 0)
    result["d7_ltv"] = np.where(result["installs"] > 0, result["d7_revenue"] / result["installs"], 0)
    result["d1_roas"] = np.where(result["spend"] > 0, result["d1_revenue"] / result["spend"], 0)
    result["d7_roas"] = np.where(result["spend"] > 0, result["d7_revenue"] / result["spend"], 0)

    daily_recovery = np.where(result["d7_revenue"] > 0, result["d7_revenue"] / 7.0, np.nan)
    result["payback_period_days"] = np.where(daily_recovery > 0, result["spend"] / daily_recovery, np.nan)

    return result.sort_values(["media_source", "campaign"]).reset_index(drop=True)


def calculate_cohort_curve(installs: pd.DataFrame, events: pd.DataFrame, max_day: int = 30) -> pd.DataFrame:
    purchase_events = _purchase_events(events)
    cohort = _cohort_events(installs, purchase_events, max_day=max_day)
    install_counts = installs.groupby("media_source")["user_key"].nunique().rename("installs")

    rows = []
    for media_source in install_counts.index:
        group = cohort[cohort["media_source"] == media_source]
        installs_n = install_counts.get(media_source, 0)

        for day in range(1, max_day + 1):
            cum_revenue = group.loc[group["day_diff"] <= day, "revenue"].sum() if not group.empty else 0.0
            ltv = cum_revenue / installs_n if installs_n else 0
            rows.append({"media_source": media_source, "day": day, "cum_revenue": cum_revenue, "ltv": ltv})

    return pd.DataFrame(rows)
