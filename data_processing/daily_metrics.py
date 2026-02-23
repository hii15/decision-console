import pandas as pd
import numpy as np


def compute_daily_d7_metrics(installs_df: pd.DataFrame, events_df: pd.DataFrame, level: str = "media_source") -> pd.DataFrame:
    """
    Daily D7 cohort metrics (install_date 기준)
    - installs_df: install_time, install_date, appsflyer_id, cost, media_source, campaign 포함
    - events_df: appsflyer_id, event_time, event_name, revenue 포함
    - level: "media_source" 또는 "campaign" 또는 "media_source_campaign"

    Returns columns:
      level_key, install_date, installs, cost, d7_revenue, d7_roas
    """

    installs = installs_df.copy()
    events = events_df.copy()

    # normalize
    installs.columns = [str(c).strip() for c in installs.columns]
    events.columns = [str(c).strip() for c in events.columns]

    # 필수 체크
    need_i = ["appsflyer_id", "install_time", "install_date", "media_source", "campaign", "cost"]
    need_e = ["appsflyer_id", "event_time", "event_name", "revenue"]
    for c in need_i:
        if c not in installs.columns:
            raise KeyError(f"[daily_metrics] installs missing: {c}")
    for c in need_e:
        if c not in events.columns:
            raise KeyError(f"[daily_metrics] events missing: {c}")

    installs["install_time"] = pd.to_datetime(installs["install_time"], errors="coerce")
    events["event_time"] = pd.to_datetime(events["event_time"], errors="coerce")
    installs = installs[~installs["install_time"].isna()].copy()
    events = events[~events["event_time"].isna()].copy()

    # level key 만들기
    if level == "media_source":
        installs["level_key"] = installs["media_source"].astype(str)
    elif level == "campaign":
        installs["level_key"] = installs["campaign"].astype(str)
    elif level == "media_source_campaign":
        installs["level_key"] = installs["media_source"].astype(str) + " | " + installs["campaign"].astype(str)
    else:
        raise ValueError("level must be one of: media_source, campaign, media_source_campaign")

    # events에 install_time / install_date / level_key 붙이기
    inst_key = installs[["appsflyer_id", "install_time", "install_date", "level_key"]].copy()
    ev = events.merge(inst_key, on="appsflyer_id", how="left", suffixes=("_evt", "_inst"))
    ev = ev[~ev["install_time"].isna()].copy()

    # install 이후 경과일
    ev["days_from_install"] = (ev["event_time"] - ev["install_time"]).dt.total_seconds() / 86400.0
    ev_d7 = ev[(ev["days_from_install"] >= 0) & (ev["days_from_install"] <= 7)].copy()

    # purchase만 revenue로
    purchase_d7 = ev_d7[ev_d7["event_name"] == "af_purchase"].copy()

    # D7 revenue by (install_date, level_key)
    if len(purchase_d7) > 0:
        rev = (
            purchase_d7
            .groupby(["install_date", "level_key"], as_index=False)
            .agg(d7_revenue=("revenue", "sum"))
        )
    else:
        rev = installs.groupby(["install_date", "level_key"], as_index=False).size()
        rev = rev[["install_date", "level_key"]]
        rev["d7_revenue"] = 0.0

    # installs + cost by (install_date, level_key)
    base = (
        installs
        .groupby(["install_date", "level_key"], as_index=False)
        .agg(
            installs=("appsflyer_id", "count"),
            cost=("cost", "sum"),
        )
    )

    out = base.merge(rev, on=["install_date", "level_key"], how="left")
    out["d7_revenue"] = out["d7_revenue"].fillna(0.0)
    out["d7_roas"] = out["d7_revenue"] / out["cost"].replace(0, np.nan)
    out["d7_roas"] = out["d7_roas"].fillna(0.0)

    # 날짜 정렬
    out["install_date"] = pd.to_datetime(out["install_date"])
    out = out.sort_values(["level_key", "install_date"]).reset_index(drop=True)

    return out