# decision/decision_engine.py

import pandas as pd
from config.target_config import DEFAULT_MULTIPLIER


def apply_channel_multiplier(df, channel_map, base_target):
    """
    media_source별 channel_type 매핑 후
    multiplier 적용 Target 계산
    """

    df = df.copy()

    df["channel_type"] = df["media_source"].map(channel_map).fillna("Performance")
    df["multiplier"] = df["channel_type"].map(DEFAULT_MULTIPLIER)

    df["adjusted_target_roas"] = base_target * df["multiplier"]

    return df


def calculate_gap(df):
    """
    ROAS - Target 차이 계산
    """

    df = df.copy()
    df["roas_gap"] = df["d7_roas"] - df["adjusted_target_roas"]

    return df


def classify_decision(df):
    """
    단순 deterministic decision rule
    """

    df = df.copy()

    def rule(row):
        if row["d7_roas"] >= row["adjusted_target_roas"]:
            return "Scale"
        elif row["d7_roas"] >= row["adjusted_target_roas"] * 0.8:
            return "Test"
        else:
            return "Reduce"

    df["decision"] = df.apply(rule, axis=1)

    return df


def run_decision_engine(df, channel_map, base_target):
    """
    전체 실행 함수
    """

    df = apply_channel_multiplier(df, channel_map, base_target)
    df = calculate_gap(df)
    df = classify_decision(df)

    return df