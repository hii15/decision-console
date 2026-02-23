# visualization/decision_table.py

import pandas as pd


def format_percentage(x):
    try:
        return f"{x:.2%}"
    except:
        return x


def format_number(x):
    try:
        return f"{x:,.2f}"
    except:
        return x


def style_decision_table(df):
    """
    Decision 결과 테이블 스타일링
    - ROAS / Target % 포맷
    - LTV 숫자 포맷
    - Decision 컬러 구분
    """

    df = df.copy()

    # 포맷 적용용 복사
    display_df = df.copy()

    percentage_cols = ["d7_roas", "adjusted_target_roas", "roas_gap"]
    number_cols = ["d7_ltv", "d7_revenue", "cost"]

    for col in percentage_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(format_percentage)

    for col in number_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(format_number)

    def highlight_decision(val):
        if val == "Scale":
            return "background-color: #1f8b4c; color: white;"
        elif val == "Test":
            return "background-color: #f0ad4e; color: black;"
        elif val == "Reduce":
            return "background-color: #d9534f; color: white;"
        return ""

    styled = display_df.style.applymap(
        highlight_decision,
        subset=["decision"]
    )

    return styled