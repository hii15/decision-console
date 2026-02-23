import pandas as pd
import numpy as np


def calculate_d7_ltv(installs_df: pd.DataFrame, events_df: pd.DataFrame) -> pd.DataFrame:
    """
    D7 LTV/ROAS 계산 (appsflyer_id로 join → raw 느낌)
    - purchase 이벤트(af_purchase)만 revenue로 사용
    - install 이후 0~7일 누적 revenue
    - media_source + campaign 집계
    """

    installs = installs_df.copy()
    events = events_df.copy()

    # installs 필수
    for col in ["appsflyer_id", "media_source", "campaign", "install_time", "cost"]:
        if col not in installs.columns:
            raise KeyError(f"[installs] missing column: {col}. columns={list(installs.columns)}")

    # events 필수
    for col in ["appsflyer_id", "event_name", "event_time", "revenue"]:
        if col not in events.columns:
            raise KeyError(f"[events] missing column: {col}. columns={list(events.columns)}")

    installs["install_time"] = pd.to_datetime(installs["install_time"], errors="coerce")
    events["event_time"] = pd.to_datetime(events["event_time"], errors="coerce")

    installs = installs[~installs["install_time"].isna()].copy()
    events = events[~events["event_time"].isna()].copy()

    inst_key = installs[["appsflyer_id", "media_source", "campaign", "install_time"]].copy()
    ev = events.merge(inst_key, on="appsflyer_id", how="left")

    # install 매칭 없는 이벤트 제거
    ev = ev[~ev["install_time"].isna()].copy()

    ev["days_from_install"] = (ev["event_time"] - ev["install_time"]).dt.total_seconds() / 86400.0
    ev_d7 = ev[(ev["days_from_install"] >= 0) & (ev["days_from_install"] <= 7)].copy()

    purchase_d7 = ev_d7[ev_d7["event_name"] == "af_purchase"].copy()

    # revenue 집계
    if len(purchase_d7) > 0:
        rev_agg = (
            purchase_d7.groupby(["media_source", "campaign"], as_index=False)
            .agg(d7_revenue=("revenue", "sum"))
        )
    else:
        # purchase 없으면 0으로
        rev_agg = installs.groupby(["media_source", "campaign"], as_index=False).size()
        rev_agg = rev_agg[["media_source", "campaign"]]
        rev_agg["d7_revenue"] = 0.0

    inst_agg = (
        installs.groupby(["media_source", "campaign"], as_index=False)
        .agg(
            installs=("appsflyer_id", "count"),
            cost=("cost", "sum"),
        )
    )

    result = inst_agg.merge(rev_agg, on=["media_source", "campaign"], how="left")
    result["d7_revenue"] = result["d7_revenue"].fillna(0.0)

    result["d7_ltv"] = result["d7_revenue"] / result["installs"].replace(0, np.nan)
    result["d7_roas"] = result["d7_revenue"] / result["cost"].replace(0, np.nan)

    result["d7_ltv"] = result["d7_ltv"].fillna(0.0)
    result["d7_roas"] = result["d7_roas"].fillna(0.0)

    return result