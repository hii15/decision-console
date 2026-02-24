import pandas as pd
import numpy as np


KST_TZ = "Asia/Seoul"


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _to_kst_naive(series: pd.Series, assume_utc: bool = True) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce", utc=assume_utc)
    return parsed.dt.tz_convert(KST_TZ).dt.tz_localize(None)


def load_file(uploaded_file):
    name = getattr(uploaded_file, "name", "") or str(uploaded_file)
    if name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif name.endswith(".xlsx") or name.endswith(".xls"):
        df = pd.read_excel(uploaded_file)
    else:
        raise ValueError("Unsupported file format. Use CSV or XLSX.")
    return _normalize_columns(df)


def preprocess_installs(
    df: pd.DataFrame,
    generate_cost_if_missing: bool = False,
    convert_utc_to_kst: bool = True,
    **kwargs,
) -> pd.DataFrame:
    df = _normalize_columns(df)

    for col in ["media_source", "campaign"]:
        if col not in df.columns:
            raise ValueError(f"[installs] missing required column: '{col}'. columns={list(df.columns)}")

    if "install_time_utc" in df.columns:
        if convert_utc_to_kst:
            df["install_time"] = _to_kst_naive(df["install_time_utc"], assume_utc=True)
        else:
            df["install_time"] = pd.to_datetime(df["install_time_utc"], errors="coerce")
    elif "install_time" in df.columns:
        if convert_utc_to_kst:
            df["install_time"] = _to_kst_naive(df["install_time"], assume_utc=True)
        else:
            df["install_time"] = pd.to_datetime(df["install_time"], errors="coerce")
    elif "install_date" in df.columns:
        df["install_time"] = pd.to_datetime(df["install_date"], errors="coerce")
    else:
        raise ValueError(
            "[installs] needs one of install_time_utc / install_time / install_date. "
            f"columns={list(df.columns)}"
        )

    if df["install_time"].isna().all():
        raise ValueError("[installs] install_time parse failed. Check install_time_utc format.")

    df["install_date"] = df["install_time"].dt.date

    if "cost" not in df.columns:
        if generate_cost_if_missing:
            base_cpi = {
                "facebook": 3.5,
                "googleadwords_int": 4.2,
                "tiktok_int": 2.6,
                "organic": 0.0,
            }
            rng = np.random.default_rng(42)
            cpi = df["media_source"].map(base_cpi).fillna(3.5).to_numpy()
            noise = rng.normal(0, 0.6, size=len(df))
            cpi = np.clip(cpi + noise, 0, None)
            df["cost"] = cpi
            df["cost_source"] = "synthetic"
        else:
            df["cost"] = 0.0
            df["cost_source"] = "missing_default_zero"
    else:
        df["cost"] = pd.to_numeric(df["cost"], errors="coerce").fillna(0.0)
        df["cost_source"] = "uploaded"

    if "appsflyer_id" not in df.columns:
        df["appsflyer_id"] = df.index.astype(str)

    return df


def preprocess_events(df: pd.DataFrame, convert_utc_to_kst: bool = True, **kwargs) -> pd.DataFrame:
    df = _normalize_columns(df)

    if "event_name" not in df.columns:
        raise ValueError(f"[events] missing required column: event_name. columns={list(df.columns)}")

    if "event_time_utc" in df.columns:
        if convert_utc_to_kst:
            df["event_time"] = _to_kst_naive(df["event_time_utc"], assume_utc=True)
        else:
            df["event_time"] = pd.to_datetime(df["event_time_utc"], errors="coerce")
    elif "event_time" in df.columns:
        if convert_utc_to_kst:
            df["event_time"] = _to_kst_naive(df["event_time"], assume_utc=True)
        else:
            df["event_time"] = pd.to_datetime(df["event_time"], errors="coerce")
    elif "event_date" in df.columns:
        df["event_time"] = pd.to_datetime(df["event_date"], errors="coerce")
    else:
        raise ValueError(
            "[events] needs one of event_time_utc / event_time / event_date. "
            f"columns={list(df.columns)}"
        )

    if df["event_time"].isna().all():
        raise ValueError("[events] event_time parse failed. Check event_time_utc format.")

    df["event_date"] = df["event_time"].dt.date

    if "af_revenue_usd" in df.columns:
        df["revenue"] = pd.to_numeric(df["af_revenue_usd"], errors="coerce").fillna(0.0)
    elif "event_revenue" in df.columns:
        df["revenue"] = pd.to_numeric(df["event_revenue"], errors="coerce").fillna(0.0)
    else:
        df["revenue"] = 0.0

    if "appsflyer_id" not in df.columns:
        df["appsflyer_id"] = None

    return df
