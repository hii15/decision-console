import pandas as pd
import numpy as np


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def calculate_d7_ltv(installs_df: pd.DataFrame, events_df: pd.DataFrame, min_maturity_days: int = 7) -> pd.DataFrame:
    installs = _normalize_columns(installs_df)
    events = _normalize_columns(events_df)

    for col in ["appsflyer_id", "media_source", "campaign", "install_time", "cost"]:
        if col not in installs.columns:
            raise KeyError(f"[installs] missing column: {col}. columns={list(installs.columns)}")

    for col in ["appsflyer_id", "event_name", "event_time", "revenue"]:
        if col not in events.columns:
            raise KeyError(f"[events] missing column: {col}. columns={list(events.columns)}")

    installs["install_time"] = pd.to_datetime(installs["install_time"], errors="coerce")
    events["event_time"] = pd.to_datetime(events["event_time"], errors="coerce")

    installs = installs[~installs["install_time"].isna()].copy()
    events = events[~events["event_time"].isna()].copy()

    if len(installs) == 0:
        return pd.DataFrame(columns=["media_source", "campaign", "installs", "cost", "d7_revenue", "d7_ltv", "d7_roas", "installs_total", "mature_ratio"])

    max_install_time = installs["install_time"].max()
    installs["cohort_age_days"] = (max_install_time - installs["install_time"]).dt.total_seconds() / 86400.0
    mature_installs = installs[installs["cohort_age_days"] >= float(min_maturity_days)].copy()

    total_agg = (
        installs.groupby(["media_source", "campaign"], as_index=False)
        .agg(installs_total=("appsflyer_id", "count"))
    )

    if len(mature_installs) == 0:
        out = total_agg.copy()
        out["installs"] = 0
        out["cost"] = 0.0
        out["d7_revenue"] = 0.0
        out["d7_ltv"] = 0.0
        out["d7_roas"] = 0.0
        out["mature_ratio"] = 0.0
        return out

    inst_key = mature_installs[["appsflyer_id", "media_source", "campaign", "install_time"]].copy()
    ev = events.merge(inst_key, on="appsflyer_id", how="left", suffixes=("_evt", "_inst"))
    ev = ev[~ev["install_time"].isna()].copy()

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

    if ("media_source" not in ev.columns) or ("campaign" not in ev.columns):
        raise KeyError(
            f"[events+installs merged] missing media_source/campaign after merge. "
            f"columns={list(ev.columns)}"
        )

    ev["days_from_install"] = (ev["event_time"] - ev["install_time"]).dt.total_seconds() / 86400.0
    ev_d7 = ev[(ev["days_from_install"] >= 0) & (ev["days_from_install"] <= 7)].copy()
    purchase_d7 = ev_d7[ev_d7["event_name"] == "af_purchase"].copy()

    if len(purchase_d7) > 0:
        rev_agg = (
            purchase_d7
            .groupby(["media_source", "campaign"], as_index=False)
            .agg(d7_revenue=("revenue", "sum"))
        )
    else:
        rev_agg = (
            mature_installs
            .groupby(["media_source", "campaign"], as_index=False)
            .size()
            .loc[:, ["media_source", "campaign"]]
        )
        rev_agg["d7_revenue"] = 0.0

    inst_agg = (
        mature_installs
        .groupby(["media_source", "campaign"], as_index=False)
        .agg(
            installs=("appsflyer_id", "count"),
            cost=("cost", "sum"),
        )
    )

    result = inst_agg.merge(rev_agg, on=["media_source", "campaign"], how="left")
    result = result.merge(total_agg, on=["media_source", "campaign"], how="left")
    result["d7_revenue"] = result["d7_revenue"].fillna(0.0)
    result["installs_total"] = result["installs_total"].fillna(result["installs"])

    result["d7_ltv"] = result["d7_revenue"] / result["installs"].replace(0, np.nan)
    result["d7_roas"] = result["d7_revenue"] / result["cost"].replace(0, np.nan)

    result["d7_ltv"] = result["d7_ltv"].fillna(0.0)
    result["d7_roas"] = result["d7_roas"].fillna(0.0)
    result["mature_ratio"] = (result["installs"] / result["installs_total"].replace(0, np.nan)).fillna(0.0)

    return result
