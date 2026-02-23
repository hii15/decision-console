# data_processing/loader.py

import pandas as pd


def load_file(uploaded_file):
    """
    CSV / XLSX 파일 로드

    Returns:
        pd.DataFrame
    """
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
    else:
        raise ValueError("Unsupported file format. Use CSV or XLSX.")

    return df


def preprocess_installs(df):
    """
    installs raw 전처리

    Expected Columns:
        install_time
        media_source
        campaign
        cost (optional)

    Returns:
        cleaned installs df
    """

    df = df.copy()

    # 날짜 컬럼 통일
    if "install_time" in df.columns:
        df["install_date"] = pd.to_datetime(df["install_time"]).dt.date
    elif "install_date" in df.columns:
        df["install_date"] = pd.to_datetime(df["install_date"]).dt.date
    else:
        raise ValueError("install_time or install_date column required")

    # 필수 컬럼 체크
    required_cols = ["media_source", "campaign"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"{col} column missing in installs data")

    return df


def preprocess_events(df):
    """
    events raw 전처리

    Expected Columns:
        event_time
        event_name
        revenue (optional)
        media_source
        campaign

    Returns:
        cleaned events df
    """

    df = df.copy()

    # 날짜 컬럼 통일
    if "event_time" in df.columns:
        df["event_date"] = pd.to_datetime(df["event_time"]).dt.date
    elif "event_date" in df.columns:
        df["event_date"] = pd.to_datetime(df["event_date"]).dt.date
    else:
        raise ValueError("event_time or event_date column required")

    # revenue 없으면 0 처리
    if "revenue" not in df.columns:
        df["revenue"] = 0

    return df