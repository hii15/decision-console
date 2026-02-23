import pandas as pd
import plotly.express as px
import streamlit as st
import numpy as np


def _finviz_scale():
    # Red → White → Green (Finviz 느낌)
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
    center_value: float | None = None,
    min_installs: int | None = None,
    min_cost: float | None = None,
):
    """
    daily_df columns:
      - install_date (datetime or str)
      - level_key
      - value_col (d7_roas/cost/installs/d7_revenue)
      - installs, cost (마스킹 옵션용; 있으면 사용)

    center_value:
      - 예) d7_roas 히트맵이면 base_target(=1.0)을 center로 두고 diverging 스케일 적용
      - None이면 min~max 스케일
    min_installs / min_cost:
      - 너무 작은 셀은 NaN으로 만들어 회색(빈칸) 처리
    """

    if daily_df.empty:
        st.warning("No data to display in heatmap.")
        return

    df = daily_df.copy()
    df["install_date"] = pd.to_datetime(df["install_date"])
    df = df.sort_values("install_date")

    # ---- 노이즈 마스킹 (선택) ----
    if (min_installs is not None) and ("installs" in df.columns):
        df.loc[df["installs"] < min_installs, value_col] = np.nan
    if (min_cost is not None) and ("cost" in df.columns) and (value_col != "cost"):
        # cost 히트맵에서는 cost 자체가 기준이므로 제외
        df.loc[df["cost"] < min_cost, value_col] = np.nan

    df["install_date_str"] = df["install_date"].dt.date.astype(str)

    pivot = df.pivot_table(
        index="level_key",
        columns="install_date_str",
        values=value_col,
        aggfunc="mean"
    )

    # ---- Color range 설정 ----
    finviz_scale = _finviz_scale()

    zmin = np.nanmin(pivot.values) if np.isfinite(np.nanmin(pivot.values)) else 0.0
    zmax = np.nanmax(pivot.values) if np.isfinite(np.nanmax(pivot.values)) else 1.0

    # 값이 모두 NaN이거나 동일하면 안전하게
    if not np.isfinite(zmin):
        zmin = 0.0
    if not np.isfinite(zmax):
        zmax = 1.0
    if zmin == zmax:
        zmin = 0.0
        zmax = zmax * 1.1 + 1e-6

    # center_value가 있으면 diverging 스케일을 "기준값 중심"으로 맞춤
    # Plotly px.imshow는 zmid를 직접 지원하므로 사용
    kwargs = {}
    if center_value is not None and value_col == "d7_roas":
        kwargs["zmid"] = float(center_value)
        # 기준값 중심에서 너무 극단적으로 퍼지는 걸 방지하려면 범위를 살짝 넓혀줌
        # 예: center=1.0일 때 zmin 0이면 너무 빨강만 과해질 수 있어서
        # 데이터 분포가 이미 적절하면 그대로 둬도 OK
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
        **kwargs
    )

    # NaN(마스킹된 셀)은 회색/빈칸처럼 보이게
    fig.update_traces(hoverongaps=False)

    fig.update_layout(
        height=560,
        coloraxis_colorbar=dict(
            title=value_col,
            ticks="outside"
        ),
        margin=dict(l=10, r=10, t=50, b=10)
    )

    st.plotly_chart(fig, use_container_width=True)