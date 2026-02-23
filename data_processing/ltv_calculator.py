import pandas as pd
import numpy as np


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # index로 들어간 컬럼이 있으면 다시 컬럼으로
    if isinstance(df.index, pd.MultiIndex) or df.index.name is not None:
        df = df.reset_index()

    df.columns = [str(c).strip() for c in df.columns]
    return df


def calculate_d7_ltv(installs_df: pd.DataFrame, events_df: pd.DataFrame) -> pd.DataFrame:
    installs = _normalize_columns(installs_df)
    events = _normalize_columns(events_df)

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

    # events에 source/campaign/설치시간 붙이기
    inst_key = installs[["appsflyer_id", "media_source", "campaign", "install_time"]].copy()
    ev = events.merge(inst_key, on="appsflyer_id", how="left")

    # install 매칭 없는 이벤트 제거
    ev = ev[~ev["install_time"].isna()].copy()

    ev["days_from_install"] = (ev["event_time"] - ev["install_time"]).dt.total_seconds() / 86400.0
    ev_d7 = ev[(ev["days_from_install"] >= 0) & (ev["days_from_install"] <= 7)].copy()

    purchase_d7 = ev_d7[ev_d7["event_name"] == "af_purchase"].copy()

    # D7 revenue 집계
    if len(purchase_d7) > 0:
        rev_agg = (
            purchase_d7.groupby(["media_source", "campaign"], as_index=False)
            .agg(d7_revenue=("revenue", "sum"))
        )
    else:
        # purchase 없으면 0으로 (여기서 groupby KeyError 방지 위해 columns 재확인)
        if not all(c in installs.columns for c in ["media_source", "campaign"]):
            raise KeyError(f"[installs] groupby keys missing. columns={list(installs.columns)}")
        rev_agg = (
            installs.groupby(["media_source", "campaign"], as_index=False)
            .size()
            .loc[:, ["media_source", "campaign"]]
        )
        rev_agg["d7_revenue"] = 0.0

    # installs/cost 집계
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

    return result.fillna({"d7_ltv": 0.0, "d7_roas": 0.0})