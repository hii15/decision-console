import pandas as pd
import numpy as np


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _ensure_base_cols(df: pd.DataFrame, base: str) -> pd.DataFrame:
    """
    merge로 인해 base, base_x, base_y가 생길 수 있음.
    installs에서 온 컬럼은 보통 _y(merge 시 오른쪽), 또는 우리가 직접 지정한 이름.
    우선순위: base -> base_y -> base_x
    최종적으로 base만 남기고 표준화.
    """
    if base in df.columns:
        return df

    y = f"{base}_y"
    x = f"{base}_x"

    if y in df.columns:
        df[base] = df[y]
        return df
    if x in df.columns:
        df[base] = df[x]
        return df

    # 못 찾으면 그대로 두고 상위에서 에러
    return df


def calculate_d7_ltv(installs_df: pd.DataFrame, events_df: pd.DataFrame) -> pd.DataFrame:
    installs = _normalize_columns(installs_df)
    events = _normalize_columns(events_df)

    # installs 필수 컬럼
    for col in ["appsflyer_id", "media_source", "campaign", "install_time", "cost"]:
        if col not in installs.columns:
            raise KeyError(f"[installs] missing column: {col}. columns={list(installs.columns)}")

    # events 필수 컬럼
    for col in ["appsflyer_id", "event_name", "event_time", "revenue"]:
        if col not in events.columns:
            raise KeyError(f"[events] missing column: {col}. columns={list(events.columns)}")

    installs["install_time"] = pd.to_datetime(installs["install_time"], errors="coerce")
    events["event_time"] = pd.to_datetime(events["event_time"], errors="coerce")

    installs = installs[~installs["install_time"].isna()].copy()
    events = events[~events["event_time"].isna()].copy()

    # events에 installs 정보 붙이기 (install쪽이 정답이므로 installs 값을 우선)
    inst_key = installs[["appsflyer_id", "media_source", "campaign", "install_time"]].copy()

    # suffix를 강제로 지정해서 예측 가능하게 만들기
    ev = events.merge(inst_key, on="appsflyer_id", how="left", suffixes=("_evt", "_inst"))

    # install 매칭 없는 이벤트 제거
    ev = ev[~ev["install_time"].isna()].copy()

    # ✅ merge 결과 컬럼명 표준화 (핵심)
    # installs에서 온 값은 media_source_inst / campaign_inst 형태로 들어옴
    # (혹시 events에 같은 이름이 있으면 media_source_evt도 존재)
    if "media_source" not in ev.columns:
        if "media_source_inst" in ev.columns:
            ev["media_source"] = ev["media_source_inst"]
        elif "media_source_evt" in ev.columns:
            ev["media_source"] = ev["media_source_evt"]

    if "campaign" not in ev.columns:
        if "campaign_inst" in ev.columns:
            ev["campaign"] = ev["campaign_inst"]
        elif "campaign_evt" in ev.columns:
            ev["campaign"] = ev["campaign_evt"]

    # 여기서도 없으면 진짜 데이터/전처리 문제
    if ("media_source" not in ev.columns) or ("campaign" not in ev.columns):
        raise KeyError(
            f"[events+installs merged] missing media_source/campaign after merge. "
            f"columns={list(ev.columns)}"
        )

    # install 이후 경과일
    ev["days_from_install"] = (ev["event_time"] - ev["install_time"]).dt.total_seconds() / 86400.0

    # 0~7일
    ev_d7 = ev[(ev["days_from_install"] >= 0) & (ev["days_from_install"] <= 7)].copy()

    # purchase 이벤트만 revenue로 집계
    purchase_d7 = ev_d7[ev_d7["event_name"] == "af_purchase"].copy()

    # ✅ D7 revenue 집계
    if len(purchase_d7) > 0:
        rev_agg = (
            purchase_d7
            .groupby(["media_source", "campaign"], as_index=False)
            .agg(d7_revenue=("revenue", "sum"))
        )
    else:
        # purchase가 없으면 0으로 채운 집계 프레임 생성
        rev_agg = (
            installs
            .groupby(["media_source", "campaign"], as_index=False)
            .size()
            .loc[:, ["media_source", "campaign"]]
        )
        rev_agg["d7_revenue"] = 0.0

    # installs/cost 집계
    inst_agg = (
        installs
        .groupby(["media_source", "campaign"], as_index=False)
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