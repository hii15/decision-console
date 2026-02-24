import pandas as pd
import numpy as np


def compute_payback_days(
    installs_df: pd.DataFrame,
    events_df: pd.DataFrame,
    level: str = "media_source",
    max_day: int = 30,
    purchase_event_name: str = "af_purchase",
) -> pd.DataFrame:
    """
    Compute payback day by install cohort grouping level.

    Returns:
      level_key, installs, cost, payback_day
    where payback_day is first day d such that cumulative_revenue(d) >= cost,
    otherwise NaN.
    """
    installs = installs_df.copy()
    events = events_df.copy()

    installs.columns = [str(c).strip() for c in installs.columns]
    events.columns = [str(c).strip() for c in events.columns]

    need_i = ["appsflyer_id", "install_time", "media_source", "campaign", "cost"]
    need_e = ["appsflyer_id", "event_time", "event_name", "revenue"]
    for col in need_i:
        if col not in installs.columns:
            raise KeyError(f"[payback] installs missing: {col}")
    for col in need_e:
        if col not in events.columns:
            raise KeyError(f"[payback] events missing: {col}")

    installs["install_time"] = pd.to_datetime(installs["install_time"], errors="coerce")
    events["event_time"] = pd.to_datetime(events["event_time"], errors="coerce")

    installs = installs[~installs["install_time"].isna()].copy()
    events = events[~events["event_time"].isna()].copy()

    if level == "media_source":
        installs["level_key"] = installs["media_source"].astype(str)
    elif level == "campaign":
        installs["level_key"] = installs["campaign"].astype(str)
    elif level == "media_source_campaign":
        installs["level_key"] = installs["media_source"].astype(str) + " | " + installs["campaign"].astype(str)
    else:
        raise ValueError("level must be one of: media_source, campaign, media_source_campaign")

    base = (
        installs.groupby("level_key", as_index=False)
        .agg(installs=("appsflyer_id", "count"), cost=("cost", "sum"))
    )

    inst_key = installs[["appsflyer_id", "install_time", "level_key"]].copy()
    ev = events.merge(inst_key, on="appsflyer_id", how="left")
    ev = ev[~ev["install_time"].isna()].copy()
    ev = ev[ev["event_name"] == purchase_event_name].copy()

    ev["days_from_install"] = (ev["event_time"] - ev["install_time"]).dt.total_seconds() / 86400.0
    ev = ev[(ev["days_from_install"] >= 0) & (ev["days_from_install"] <= int(max_day))].copy()

    if len(ev) == 0:
        out = base.copy()
        out["payback_day"] = np.nan
        return out

    ev["day"] = np.floor(ev["days_from_install"]).astype(int)

    rev_by_day = (
        ev.groupby(["level_key", "day"], as_index=False)
        .agg(revenue=("revenue", "sum"))
        .sort_values(["level_key", "day"])
    )
    rev_by_day["cum_revenue"] = rev_by_day.groupby("level_key")["revenue"].cumsum()

    merged = rev_by_day.merge(base[["level_key", "cost"]], on="level_key", how="left")
    reached = merged[merged["cum_revenue"] >= merged["cost"]].copy()

    first = reached.groupby("level_key", as_index=False).agg(payback_day=("day", "min"))
    out = base.merge(first, on="level_key", how="left")
    return out
