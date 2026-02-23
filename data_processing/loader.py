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
    installs_raw.csv (dummy MMP/Appsflyer raw 형태) 대응
    - install_time_utc를 표준 install_time으로 변환
    - install_date 추가
    - cost 없으면 (옵션) 더미 CPI 기반 cost 생성
    """
    df = df.copy()

    # 필수
    for col in ["media_source", "campaign"]:
        if col not in df.columns:
            raise ValueError(f"[installs] missing required column: {col}. columns={list(df.columns)}")

    # 시간 컬럼
    if "install_time_utc" in df.columns:
        df["install_time"] = pd.to_datetime(df["install_time_utc"], errors="coerce")
    elif "install_time" in df.columns:
        df["install_time"] = pd.to_datetime(df["install_time"], errors="coerce")
    elif "install_date" in df.columns:
        df["install_time"] = pd.to_datetime(df["install_date"], errors="coerce")
    else:
        raise ValueError(
            "[installs] needs one of install_time_utc/install_time/install_date. "
            f"columns={list(df.columns)}"
        )

    if df["install_time"].isna().all():
        raise ValueError("[installs] install_time parse failed. Check install_time_utc format.")

    df["install_date"] = df["install_time"].dt.date

    # cost 처리(더미)
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
        else:
            df["cost"] = 0.0
    else:
        df["cost"] = pd.to_numeric(df["cost"], errors="coerce").fillna(0.0)

    return df


def preprocess_events(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """
    events_raw.csv 대응
    - event_time_utc -> event_time 표준화
    - revenue: af_revenue_usd 우선, 없으면 event_revenue 사용
    """
    df = df.copy()

    if "event_name" not in df.columns:
        raise ValueError(f"[events] missing required column: event_name. columns={list(df.columns)}")

    if "event_time_utc" in df.columns:
        df["event_time"] = pd.to_datetime(df["event_time_utc"], errors="coerce")
    elif "event_time" in df.columns:
        df["event_time"] = pd.to_datetime(df["event_time"], errors="coerce")
    elif "event_date" in df.columns:
        df["event_time"] = pd.to_datetime(df["event_date"], errors="coerce")
    else:
        raise ValueError(
            "[events] needs one of event_time_utc/event_time/event_date. "
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

    # appsflyer_id는 cohort join에 중요
    if "appsflyer_id" not in df.columns:
        # 없으면 나중에 정확 조인이 어려움
        df["appsflyer_id"] = None

    return df