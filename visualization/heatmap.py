import pandas as pd
import plotly.express as px
import streamlit as st


def show_risk_heatmap(daily_df: pd.DataFrame, value_col: str, title: str):
    """
    daily_df columns: install_date, level_key, <value_col>
    Heatmap: Y=level_key, X=install_date
    """

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

    # plotly heatmap
    fig = px.imshow(
        pivot,
        aspect="auto",
        title=title,
        labels=dict(x="Install Date", y="Source / Campaign", color=value_col),
    )

    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)