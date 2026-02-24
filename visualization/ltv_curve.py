import streamlit as st
import plotly.express as px
import pandas as pd


def show_ltv_curve(
    curve_df: pd.DataFrame,
    metric: str,
    selected_keys: list[str] | None = None,
    title: str = "LTV Curve",
    show_sample_in_legend: bool = True,
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

    # ✅ legend에 모수 추가: series명 → "series (N=..., $=...k)"
    if show_sample_in_legend:
        # day 최댓값 기준의 installs/cost를 시리즈 대표값으로 사용
        max_day = df["day"].max()
        meta = (
            df[df["day"] == max_day][["level_key", "installs", "cost"]]
            .drop_duplicates("level_key")
            .copy()
        )

        meta["installs"] = meta["installs"].fillna(0).astype(int)
        meta["cost"] = meta["cost"].fillna(0.0).astype(float)

        # 보기 좋게 cost는 k 단위로
        def fmt_cost(x):
            if x >= 1000:
                return f"{x/1000:.1f}k"
            return f"{x:.0f}"

        meta["legend_key"] = meta.apply(
            lambda r: f'{r["level_key"]} (N={r["installs"]}, $={fmt_cost(r["cost"])})',
            axis=1
        )

        mapping = dict(zip(meta["level_key"], meta["legend_key"]))
        df["legend_key"] = df["level_key"].map(mapping).fillna(df["level_key"])
        color_col = "legend_key"
    else:
        color_col = "level_key"

    # hover에 모수 같이 표시
    fig = px.line(
        df,
        x="day",
        y=metric,
        color=color_col,
        markers=True,
        title=title,
        labels={
            "day": "Days since Install (cumulative)",
            metric: label_map.get(metric, metric),
            color_col: "Series",
        },
        hover_data={
            "level_key": True,
            "installs": ":,",
            "cost": ":,.2f",
            "revenue": ":,.2f",
        }
    )

    fig.update_layout(height=520, legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)