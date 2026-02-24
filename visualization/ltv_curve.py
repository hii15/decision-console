import streamlit as st
import plotly.express as px
import pandas as pd


def show_ltv_curve(
    curve_df: pd.DataFrame,
    metric: str,
    selected_keys: list[str] | None = None,
    title: str = "LTV Curve",
):
    """
    curve_df columns:
      level_key, day, installs, cost, revenue, ltv, roas

    metric: "ltv" | "roas" | "revenue"
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

    fig = px.line(
        df,
        x="day",
        y=metric,
        color="level_key",
        markers=True,
        title=title,
        labels={
            "day": "Days since Install (cumulative)",
            metric: label_map.get(metric, metric),
            "level_key": "Source / Campaign",
        },
    )

    fig.update_layout(height=520, legend_title_text="")

    st.plotly_chart(fig, use_container_width=True)