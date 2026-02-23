# data_processing/ltv_calculator.py

import pandas as pd


def calculate_d7_ltv(installs_df, events_df):
    """
    D7 LTV 계산

    Logic:
        - install_date 기준
        - install 이후 7일 이내 revenue 합산
        - media_source / campaign 단위 집계

    Returns:
        aggregated dataframe
    """

    installs = installs_df.copy()
    events = events_df.copy()

    # install_date datetime 변환
    installs["install_date"] = pd.to_datetime(installs["install_date"])
    events["event_date"] = pd.to_datetime(events["event_date"])

    # install_date merge
    merged = events.merge(
        installs[["media_source", "campaign", "install_date"]],
        on=["media_source", "campaign"],
        how="left"
    )

    # install 후 7일 이내 필터
    merged["days_diff"] = (
        merged["event_date"] - merged["install_date"]
    ).dt.days

    d7_events = merged[(merged["days_diff"] >= 0) & (merged["days_diff"] <= 7)]

    # revenue 집계
    revenue_agg = (
        d7_events
        .groupby(["media_source", "campaign"])
        .agg(d7_revenue=("revenue", "sum"))
        .reset_index()
    )

    # installs 집계
    install_agg = (
        installs
        .groupby(["media_source", "campaign"])
        .agg(installs=("install_date", "count"))
        .reset_index()
    )

    # cost 집계 (optional)
    if "cost" in installs.columns:
        cost_agg = (
            installs
            .groupby(["media_source", "campaign"])
            .agg(cost=("cost", "sum"))
            .reset_index()
        )
    else:
        cost_agg = install_agg.copy()
        cost_agg["cost"] = 0

    # merge all
    result = (
        install_agg
        .merge(revenue_agg, on=["media_source", "campaign"], how="left")
        .merge(cost_agg, on=["media_source", "campaign"], how="left")
    )

    result["d7_revenue"] = result["d7_revenue"].fillna(0)

    # LTV
    result["d7_ltv"] = result["d7_revenue"] / result["installs"]

    # ROAS
    result["d7_roas"] = result.apply(
        lambda x: x["d7_revenue"] / x["cost"] if x["cost"] > 0 else 0,
        axis=1
    )

    return result