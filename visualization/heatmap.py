import pandas as pd
import plotly.express as px
import streamlit as st
import numpy as np


def _finviz_scale():
    return [
        [0.0, "#8b0000"],   # dark red
        [0.25, "#ff4d4d"],  # red
        [0.5, "#ffffff"],   # neutral
        [0.75, "#4caf50"],  # green
        [1.0, "#006400"],   # dark green
    ]


def show_risk_heatmap(
    daily_df: pd.DataFrame,
    value_col: str,
    title: str,
    center_value=None,
    min_installs=None,
    min_cost=None,
):
    if daily_df.empty:
        st.warning("No data to display in heatmap.")
        return

    df = daily_df.copy()
    df["install_date"] = pd.to_datetime(df["install_date"])
    df = df.sort_values("install_date")

    # ---- 노이즈 마스킹 ----
    if (min_installs is not None) and ("installs" in df.columns):
        df.loc[df["installs"] < int(min_installs), value_col] = np.nan

    if (min_cost is not None) and ("cost" in df.columns) and (value_col != "cost"):
        df.loc[df["cost"] < float(min_cost), value_col] = np.nan

    df["install_date_str"] = df["install_date"].dt.date.astype(str)

    pivot = df.pivot_table(
        index="level_key",
        columns="install_date_str",
        values=value_col,
        aggfunc="mean"
    )

    # ---- 색상 범위 설정 ----
    finviz_scale = _finviz_scale()

    # 전부 NaN일 수도 있으니 안전 처리
    vals = pivot.values
    if np.all(np.isnan(vals)):
        st.warning("All cells are masked (NaN). Try lowering thresholds or changing date range.")
        return

    zmin = float(np.nanmin(vals))
    zmax = float(np.nanmax(vals))

    if zmin == zmax:
        zmin = 0.0
        zmax = zmax * 1.1 + 1e-6

    # ROAS 기준 center가 있으면 범위를 중심 기준으로 적절히 넓힘
    if center_value is not None and value_col == "d7_roas":
        center_value = float(center_value)
        zmin = min(zmin, center_value * 0.6)
        zmax = max(zmax, center_value * 1.4)

    fig = px.imshow(
        pivot,
        aspect="auto",
        title=title,
        color_continuous_scale=finviz_scale,
        zmin=zmin,
        zmax=zmax,
        labels=dict(x="Install Date", y="Source / Campaign", color=value_col),
    )

    # ✅ 버전 호환: zmid 대신 coloraxis_cmid 사용
    if center_value is not None and value_col == "d7_roas":
        fig.update_layout(coloraxis_cmid=float(center_value))

    fig.update_traces(hoverongaps=False)

    fig.update_layout(
        height=560,
        coloraxis_colorbar=dict(title=value_col, ticks="outside"),
        margin=dict(l=10, r=10, t=50, b=10),
    )

    st.plotly_chart(fig, use_container_width=True)