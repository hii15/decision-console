import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np


def _alpha_from_installs(n: int, n_low: int = 50, n_high: int = 800) -> float:
    """
    installs가 작으면 더 흐리게(투명)
    n_low 이하: 0.25
    n_high 이상: 1.0
    그 사이: 선형 보간
    """
    try:
        n = int(n)
    except Exception:
        return 0.6

    if n <= n_low:
        return 0.25
    if n >= n_high:
        return 1.0
    return 0.25 + (n - n_low) * (1.0 - 0.25) / (n_high - n_low)


def show_ltv_curve(
    curve_df: pd.DataFrame,
    metric: str,
    selected_keys: list[str] | None = None,
    title: str = "LTV Curve",
    show_sample_in_legend: bool = True,
    target_roas: float | None = None,   # ✅ ROAS일 때 target 라인
    fade_by_sample: bool = True,        # ✅ 모수 기반 흐리게
    n_low: int = 50,
    n_high: int = 800,
):
    """
    curve_df columns:
      level_key, day, installs, cost, revenue, ltv, roas
    metric: ltv | roas | revenue
    """

    if curve_df.empty:
        st.warning("No data to display.")
        return

    df = curve_df.copy()

    if selected_keys:
        df = df[df["level_key"].isin(selected_keys)].copy()

    if df.empty:
        st.warning("No series left after filtering. Try selecting different keys.")
        return

    label_map = {
        "ltv": "LTV (Revenue per Install)",
        "roas": "ROAS (Revenue / Cost)",
        "revenue": "Cumulative Revenue",
    }

    # legend label 구성
    max_day = df["day"].max()
    meta = (
        df[df["day"] == max_day][["level_key", "installs", "cost"]]
        .drop_duplicates("level_key")
        .copy()
    )
    meta["installs"] = meta["installs"].fillna(0).astype(int)
    meta["cost"] = meta["cost"].fillna(0.0).astype(float)

    def fmt_cost(x):
        if x >= 1000:
            return f"{x/1000:.1f}k"
        return f"{x:.0f}"

    if show_sample_in_legend:
        meta["legend_key"] = meta.apply(
            lambda r: f'{r["level_key"]} (N={r["installs"]}, $={fmt_cost(r["cost"])})',
            axis=1
        )
    else:
        meta["legend_key"] = meta["level_key"]

    mapping = dict(zip(meta["level_key"], meta["legend_key"]))
    df["legend_key"] = df["level_key"].map(mapping).fillna(df["level_key"])

    # plotly express로 기본 라인 생성
    fig = px.line(
        df,
        x="day",
        y=metric,
        color="legend_key",
        markers=True,
        title=title,
        labels={
            "day": "Days since Install (cumulative)",
            metric: label_map.get(metric, metric),
            "legend_key": "Series",
        },
        hover_data={
            "level_key": True,
            "installs": ":,",
            "cost": ":,.2f",
            "revenue": ":,.2f",
        }
    )

    # ✅ 모수 기반 흐리게 (trace별 opacity 적용)
    if fade_by_sample:
        # legend_key -> installs 매핑
        legend_to_installs = {mapping[k]: int(v) for k, v in zip(meta["level_key"], meta["installs"])}
        # 혹시 mapping이 꼬일 수 있으니 안전하게 보정
        for _, r in meta.iterrows():
            legend_to_installs[r["legend_key"]] = int(r["installs"])

        for tr in fig.data:
            n = legend_to_installs.get(tr.name, None)
            if n is None:
                continue
            tr.opacity = _alpha_from_installs(n, n_low=n_low, n_high=n_high)

    # ✅ ROAS일 때 target 라인 추가
    if metric == "roas" and target_roas is not None:
        try:
            y = float(target_roas)
            # x축 범위는 day 값 기준
            x_min = float(df["day"].min())
            x_max = float(df["day"].max())
            fig.add_trace(
                go.Scatter(
                    x=[x_min, x_max],
                    y=[y, y],
                    mode="lines",
                    name=f"Target ROAS ({y:.2f})",
                    line=dict(dash="dash"),
                )
            )
        except Exception:
            pass

    fig.update_layout(height=520, legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)