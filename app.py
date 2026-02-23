import streamlit as st

from data_processing.loader import load_file, preprocess_installs, preprocess_events
from data_processing.ltv_calculator import calculate_d7_ltv
from decision.decision_engine import run_decision_engine
from visualization.decision_table import style_decision_table
from config.channel_config import DEFAULT_CHANNEL_MAP


st.set_page_config(layout="wide")
st.title("UA Decision Support Console")
st.markdown("---")

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

# KPI 계산
result_df = calculate_d7_ltv(installs_df, events_df)

# Decision Engine
final_df = run_decision_engine(result_df, channel_map, base_target)

st.markdown("## Decision Table")
st.write(style_decision_table(final_df))

st.markdown("## D7 ROAS by Media Source")
chart_df = final_df.groupby("media_source")["d7_roas"].mean().reset_index()
st.bar_chart(chart_df.set_index("media_source"))