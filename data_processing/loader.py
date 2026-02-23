# data_processing/loader.py
import pandas as pd
import numpy as np


def load_file(uploaded_file):
    name = getattr(uploaded_file, "name", "") or str(uploaded_file)
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(uploaded_file)
    raise ValueError("Unsupported file format. Use CSV or XLSX.")


def preprocess_installs(df: pd.DataFrame, generate_cost_if_missing: bool = True, **kwargs) -> pd.DataFrame:
    """
    installs_raw.csv (Appsflyer/Adjust 스타일) 대응
    - generate_cost_if_missing: cost 없을 때 더미 생성 여부
    - **kwargs: 과거/미래 파라미터 호환용
    """
    df = df.copy()

    for col in ["media_source", "campaign"]:
        if col not in df.columns:
            raise ValueError(f"installs data missing required column: '{col}'")

    # install_time_utc 우선 사용
    if "install_time_utc" in df.columns:
        df["install_time"] = pd.to_datetime(df["install_time_utc"], errors="coerce")
    elif "install_time" in df.columns:
        df["install_time"] = pd.to_datetime(df["install_time"], errors="coerce")
    elif "install_date" in df.columns:
        df["install_time"] = pd.to_datetime(df["install_date"], errors="coerce")
    else:
        raise ValueError(
            "installs needs one of: install_time_utc / install_time / install_date. "
            f"Your columns: {list(df.columns)}"
        )

    if df["install_time"].isna().all():
        raise ValueError("install_time could not be parsed. Check install_time_utc format.")

    df["install_date"] = df["install_time"].dt.date

    # cost 처리
    if "cost" not in df.columns:
        if generate_cost_if_missing:
            import numpy as np
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
        else:
            df["cost"] = 0.0
    else:
        df["cost"] = pd.to_numeric(df["cost"], errors="coerce").fillna(0.0)

    return df


def preprocess_events(df: pd.DataFrame) -> pd.DataFrame:
    """
    events_raw.csv 대응
    기대 컬럼:
      - event_time_utc (필수)
      - event_name (필수)
      - af_revenue_usd 또는 event_revenue (둘 중 하나)
      - appsflyer_id (권장, cohort join 정확도용)
    """
    df = df.copy()

    if "event_name" not in df.columns:
        raise ValueError("events data missing required column: 'event_name'")

    if "event_time_utc" in df.columns:
        df["event_time"] = pd.to_datetime(df["event_time_utc"], errors="coerce")
    elif "event_time" in df.columns:
        df["event_time"] = pd.to_datetime(df["event_time"], errors="coerce")
    elif "event_date" in df.columns:
        df["event_time"] = pd.to_datetime(df["event_date"], errors="coerce")
    else:
        raise ValueError(
            "events needs one of: event_time_utc / event_time / event_date. "
            f"Your columns: {list(df.columns)}"
        )

    if df["event_time"].isna().all():
        raise ValueError("event_time could not be parsed. Check event_time_utc format.")

    df["event_date"] = df["event_time"].dt.date

    # revenue: af_revenue_usd 우선
    if "af_revenue_usd" in df.columns:
        df["revenue"] = pd.to_numeric(df["af_revenue_usd"], errors="coerce").fillna(0.0)
    elif "event_revenue" in df.columns:
        df["revenue"] = pd.to_numeric(df["event_revenue"], errors="coerce").fillna(0.0)
    else:
        df["revenue"] = 0.0

    return df