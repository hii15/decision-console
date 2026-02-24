import pandas as pd
import numpy as np


def compute_ltv_curve(
    installs_df: pd.DataFrame,
    events_df: pd.DataFrame,
    level: str = "media_source",
    day_points=(0, 1, 3, 7),
    lookback_days: int | None = 30,
    purchase_event_name: str = "af_purchase",
) -> pd.DataFrame:
    """
    LTV/ROAS Curve 계산 (install cohort 기반, appsflyer_id join)
    - level: media_source | campaign | media_source_campaign
    - day_points: (0,1,3,7) 같은 누적 기준일
    - lookback_days: 최근 N일 install cohort만 포함 (None이면 전체)

    반환(long format):
      level_key, day, installs, cost, revenue, ltv, roas
    """

    installs = installs_df.copy()
    events = events_df.copy()

    installs.columns = [str(c).strip() for c in installs.columns]
    events.columns = [str(c).strip() for c in events.columns]

    # 필수 체크
    need_i = ["appsflyer_id", "install_time", "install_date", "media_source", "campaign", "cost"]
    need_e = ["appsflyer_id", "event_time", "event_name", "revenue"]
    for c in need_i:
        if c not in installs.columns:
            raise KeyError(f"[cohort_curve] installs missing: {c}")
    for c in need_e:
        if c not in events.columns:
            raise KeyError(f"[cohort_curve] events missing: {c}")

    installs["install_time"] = pd.to_datetime(installs["install_time"], errors="coerce")
    installs["install_date"] = pd.to_datetime(installs["install_date"], errors="coerce")
    events["event_time"] = pd.to_datetime(events["event_time"], errors="coerce")

    installs = installs[~installs["install_time"].isna()].copy()
    installs = installs[~installs["install_date"].isna()].copy()
    events = events[~events["event_time"].isna()].copy()

    # lookback filter (install cohort 기준)
    if lookback_days is not None and len(installs) > 0:
        max_date = installs["install_date"].max()
        start_date = max_date - pd.Timedelta(days=int(lookback_days) - 1)
        installs = installs[installs["install_date"] >= start_date].copy()

    # level_key 생성
    if level == "media_source":
        installs["level_key"] = installs["media_source"].astype(str)
    elif level == "campaign":
        installs["level_key"] = installs["campaign"].astype(str)
    elif level == "media_source_campaign":
        installs["level_key"] = installs["media_source"].astype(str) + " | " + installs["campaign"].astype(str)
    else:
        raise ValueError("level must be one of: media_source, campaign, media_source_campaign")

    # installs 기준 installs/cost 집계
    base = (
        installs.groupby("level_key", as_index=False)
        .agg(
            installs=("appsflyer_id", "count"),
            cost=("cost", "sum"),
        )
    )

    # events에 install_time, level_key 붙이기
    inst_key = installs[["appsflyer_id", "install_time", "level_key"]].copy()
    ev = events.merge(inst_key, on="appsflyer_id", how="left", suffixes=("_evt", "_inst"))
    ev = ev[~ev["install_time"].isna()].copy()

    # purchase 이벤트만
    ev = ev[ev["event_name"] == purchase_event_name].copy()

    # install 이후 경과일
    ev["days_from_install"] = (ev["event_time"] - ev["install_time"]).dt.total_seconds() / 86400.0

    # 누적 day_points용 집계
    day_points = sorted(set(int(d) for d in day_points))
    rows = []

    for d in day_points:
        # 누적: <= d
        sub = ev[(ev["days_from_install"] >= 0) & (ev["days_from_install"] <= d)].copy()

        if len(sub) > 0:
            rev = (
                sub.groupby("level_key", as_index=False)
                .agg(revenue=("revenue", "sum"))
            )
        else:
            rev = base[["level_key"]].copy()
            rev["revenue"] = 0.0

        out = base.merge(rev, on="level_key", how="left")
        out["revenue"] = out["revenue"].fillna(0.0)
        out["day"] = d

        # LTV / ROAS
        out["ltv"] = out["revenue"] / out["installs"].replace(0, np.nan)
        out["roas"] = out["revenue"] / out["cost"].replace(0, np.nan)
        out["ltv"] = out["ltv"].fillna(0.0)
        out["roas"] = out["roas"].fillna(0.0)

        rows.append(out)

    curve = pd.concat(rows, ignore_index=True)
    curve = curve.sort_values(["level_key", "day"]).reset_index(drop=True)

    return curve