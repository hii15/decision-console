import streamlit as st

from data_processing.loader import load_file, preprocess_installs, preprocess_events
from data_processing.ltv_calculator import calculate_d7_ltv
from data_processing.daily_metrics import compute_daily_d7_metrics

from decision.decision_engine import run_decision_engine
from visualization.decision_table import style_decision_table
from visualization.heatmap import show_risk_heatmap

from config.channel_config import DEFAULT_CHANNEL_MAP


st.set_page_config(layout="wide")
st.title("UA Decision Support Console")
st.markdown("---")

# 업로드
col1, col2 = st.columns(2)
with col1:
    installs_file = st.file_uploader("Upload Installs Raw (CSV/XLSX)", type=["csv", "xlsx"])
with col2:
    events_file = st.file_uploader("Upload Events Raw (CSV/XLSX)", type=["csv", "xlsx"])

if not installs_file or not events_file:
    st.info("Please upload both installs and events files.")
    st.stop()

installs_df = preprocess_installs(load_file(installs_file), generate_cost_if_missing=True)
events_df = preprocess_events(load_file(events_file))
st.success("Files Loaded Successfully")

base_target = st.number_input(
    "Base Target D7 ROAS (예: 1.0 = 100%)",
    min_value=0.0,
    value=1.0,
    step=0.05
)

st.markdown("## Channel Type Configuration")
unique_sources = list(installs_df["media_source"].unique())

channel_map = {}
for source in unique_sources:
    default_type = DEFAULT_CHANNEL_MAP.get(source, "Performance")
    channel_type = st.selectbox(
        f"{source}",
        ["Performance", "Hybrid", "Branding"],
        index=["Performance", "Hybrid", "Branding"].index(default_type)
    )
    channel_map[source] = channel_type

st.markdown("---")

# ====== Tabs ======
tab1, tab2 = st.tabs(["Decision View", "Risk Heatmap"])

# ====== Decision View ======
with tab1:
    result_df = calculate_d7_ltv(installs_df, events_df)
    final_df = run_decision_engine(result_df, channel_map, base_target)

    st.markdown("## Decision Table")
    st.write(style_decision_table(final_df))

    st.markdown("## D7 ROAS by Media Source")
    chart_df = final_df.groupby("media_source")["d7_roas"].mean().reset_index()
    st.bar_chart(chart_df.set_index("media_source"))

# ====== Risk Heatmap ======
with tab2:
    st.markdown("## Risk Heatmap (Install Cohort 기반)")

    col_a, col_b = st.columns([1, 1])
    with col_a:
        level = st.selectbox(
            "Heatmap Level",
            ["media_source", "campaign", "media_source_campaign"],
            index=0
        )
    with col_b:
        metric = st.selectbox(
            "Metric",
            ["d7_roas", "cost", "installs", "d7_revenue"],
            index=0
        )

    daily_df = compute_daily_d7_metrics(installs_df, events_df, level=level)

    # metric별 title
    title_map = {
        "d7_roas": "D7 ROAS Heatmap",
        "cost": "Cost Heatmap",
        "installs": "Installs Heatmap",
        "d7_revenue": "D7 Revenue Heatmap",
    }

    show_risk_heatmap(daily_df, value_col=metric, title=title_map.get(metric, "Heatmap"))