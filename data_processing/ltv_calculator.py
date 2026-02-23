# data_processing/ltv_calculator.py
import pandas as pd
import numpy as np


def calculate_d7_ltv(installs_df: pd.DataFrame, events_df: pd.DataFrame) -> pd.DataFrame:
    """
    D7 LTV/ROAS 계산 (Appsflyer raw 느낌)
    - appsflyer_id 기준으로 install_time 붙인 뒤
    - purchase 이벤트(af_purchase)의 install 이후 0~7일 revenue 합산
    - media_source+campaign 단위로 집계
    """

    installs = installs_df.copy()
    events = events_df.copy()

    # 필수 컬럼 체크
    for col in ["appsflyer_id", "media_source", "campaign", "install_time", "cost"]:
        if col not in installs.columns:
            raise ValueError(f"installs missing required column: {col}")

    for col in ["appsflyer_id", "event_name", "event_time", "revenue"]:
        if col not in events.columns:
            raise ValueError(f"events missing required column: {col}")

    installs["install_time"] = pd.to_datetime(installs["install_time"], errors="coerce")
    events["event_time"] = pd.to_datetime(events["event_time"], errors="coerce")

    # installs의 주요 속성만 유지
    inst_key = installs[["appsflyer_id", "media_source", "campaign", "install_time", "cost"]].copy()

    # events에 install_time 붙이기 (정확한 코호트)
    ev = events.merge(inst_key, on="appsflyer_id", how="left")

    # install이 없는 이벤트는 제외 (정합성)
    ev = ev[~ev["install_time"].isna()].copy()

    # 구매 이벤트만 (필요하면 나중에 UI로 확장)
    purchase = ev[ev["event_name"] == "af_purchase"].copy()

    # install 이후 경과일
    purchase["days_from_install"] = (purchase["event_time"] - purchase["install_time"]).dt.total_seconds() / 86400.0

    # 0~7일
    purchase_d7 = purchase[(purchase["days_from_install"] >= 0) & (purchase["days_from_install"] <= 7)].copy()

    # D7 revenue 집계
    rev_agg = (
        purchase_d7
        .groupby(["media_source", "campaign"], as_index=False)
        .agg(d7_revenue=("revenue", "sum"))
    )

    # installs / cost 집계
    inst_agg = (
        installs
        .groupby(["media_source", "campaign"], as_index=False)
        .agg(
            installs=("appsflyer_id", "count"),
            cost=("cost", "sum")
        )
    )

    result = inst_agg.merge(rev_agg, on=["media_source", "campaign"], how="left")
    result["d7_revenue"] = result["d7_revenue"].fillna(0.0)

    # LTV / ROAS
    result["d7_ltv"] = result["d7_revenue"] / result["installs"].replace(0, np.nan)
    result["d7_roas"] = result["d7_revenue"] / result["cost"].replace(0, np.nan)

    # 보기 좋게 NaN -> 0
    result["d7_ltv"] = result["d7_ltv"].fillna(0.0)
    result["d7_roas"] = result["d7_roas"].fillna(0.0)

    return result