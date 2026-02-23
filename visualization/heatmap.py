import pandas as pd
import plotly.express as px
import streamlit as st
import numpy as np


def show_risk_heatmap(daily_df: pd.DataFrame, value_col: str, title: str):
    if daily_df.empty:
        st.warning("No data to display in heatmap.")
        return

    df = daily_df.copy()
    df["install_date"] = pd.to_datetime(df["install_date"]).dt.date.astype(str)

    pivot = df.pivot_table(
        index="level_key",
        columns="install_date",
        values=value_col,
        aggfunc="mean"
    )

    # ---- 컬러 스케일 설정 ----
    # Finviz 스타일 Red → White → Green
    finviz_scale = [
        [0.0, "#8b0000"],   # dark red
        [0.25, "#ff4d4d"],  # red
        [0.5, "#ffffff"],   # neutral
        [0.75, "#4caf50"],  # green
        [1.0, "#006400"],   # dark green
    ]

    zmin = np.nanmin(pivot.values)
    zmax = np.nanmax(pivot.values)

    # 값이 모두 동일한 경우 대비
    if zmin == zmax:
        zmin = 0
        zmax = zmax * 1.1 + 1e-6

    fig = px.imshow(
        pivot,
        aspect="auto",
        title=title,
        color_continuous_scale=finviz_scale,
        zmin=zmin,
        zmax=zmax,
        labels=dict(x="Install Date", y="Source / Campaign", color=value_col),
    )

    fig.update_layout(
        height=550,
        coloraxis_colorbar=dict(
            title=value_col,
            ticks="outside"
        )
    )

    st.plotly_chart(fig, use_container_width=True)