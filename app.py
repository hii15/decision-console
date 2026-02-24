import streamlit as st
import pandas as pd

from data_processing.loader import load_file, preprocess_installs, preprocess_events
from data_processing.ltv_calculator import calculate_d7_ltv
from data_processing.daily_metrics import compute_daily_d7_metrics
from data_processing.cohort_curve import compute_ltv_curve

from decision.decision_engine import run_decision_engine
from visualization.decision_table import style_decision_table
from visualization.heatmap import show_risk_heatmap
from visualization.ltv_curve import show_ltv_curve

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
tab1, tab2, tab3 = st.tabs(["Decision View", "Risk Heatmap", "LTV Curve"])

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

    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])

    with c1:
        level = st.selectbox(
            "Heatmap Level",
            ["media_source", "campaign", "media_source_campaign"],
            index=0,
            key="hm_level"
        )

    with c2:
        metric = st.selectbox(
            "Metric",
            ["d7_roas", "cost", "installs", "d7_revenue"],
            index=0,
            key="hm_metric"
        )

    with c3:
        lookback = st.selectbox(
            "Date Range",
            ["Last 14 days", "Last 30 days", "Last 60 days", "All"],
            index=1,
            key="hm_range"
        )

    with c4:
        enable_mask = st.checkbox("Mask low volume cells", value=True, key="hm_mask")

    min_installs = None
    min_cost = None
    if enable_mask:
        m1, m2 = st.columns(2)
        with m1:
            min_installs = st.number_input("Min installs per cell", min_value=0, value=30, step=10, key="hm_min_inst")
        with m2:
            min_cost = st.number_input("Min cost per cell", min_value=0.0, value=50.0, step=10.0, key="hm_min_cost")

    daily_df = compute_daily_d7_metrics(installs_df, events_df, level=level)
    daily_df["install_date"] = pd.to_datetime(daily_df["install_date"])
    max_date = daily_df["install_date"].max()

    if lookback != "All":
        days = int(lookback.split()[1])
        start_date = max_date - pd.Timedelta(days=days - 1)
        daily_df = daily_df[daily_df["install_date"] >= start_date].copy()

    title_map = {
        "d7_roas": "D7 ROAS Heatmap (centered at Target)",
        "cost": "Cost Heatmap",
        "installs": "Installs Heatmap",
        "d7_revenue": "D7 Revenue Heatmap",
    }

    center_value = base_target if metric == "d7_roas" else None

    show_risk_heatmap(
        daily_df,
        value_col=metric,
        title=title_map.get(metric, "Heatmap"),
        center_value=center_value,
        min_installs=int(min_installs) if enable_mask else None,
        min_cost=float(min_cost) if enable_mask else None,
    )

# ====== LTV Curve ======
with tab3:
    st.markdown("## LTV / ROAS Curve (Install Cohort 누적)")

    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])

    with c1:
        curve_level = st.selectbox(
            "Curve Level",
            ["media_source", "campaign", "media_source_campaign"],
            index=0,
            key="cv_level"
        )

    with c2:
        curve_metric = st.selectbox(
            "Metric",
            ["ltv", "roas", "revenue"],
            index=0,
            key="cv_metric"
        )

    with c3:
        curve_range = st.selectbox(
            "Install Cohort Range",
            ["Last 14 days", "Last 30 days", "Last 60 days", "All"],
            index=1,
            key="cv_range"
        )

    with c4:
        top_n = st.number_input("Auto-select Top N", min_value=1, value=8, step=1, key="cv_topn")

    # day points (고정 프리셋)
    day_points = (0, 1, 3, 7)

    # lookback_days 변환
    lookback_days = None
    if curve_range != "All":
        lookback_days = int(curve_range.split()[1])

    curve_df = compute_ltv_curve(
        installs_df,
        events_df,
        level=curve_level,
        day_points=day_points,
        lookback_days=lookback_days,
        purchase_event_name="af_purchase",
    )

    if curve_df.empty:
        st.warning("No curve data. Try changing filters.")
        st.stop()

    # 기본 선택: metric에 따라 "의미 있는" 기준으로 상위 N 자동 선택
    if curve_metric == "revenue":
        rank = curve_df[curve_df["day"] == max(day_points)].sort_values("revenue", ascending=False)
    elif curve_metric == "roas":
        rank = curve_df[curve_df["day"] == max(day_points)].sort_values("roas", ascending=False)
    else:
        rank = curve_df[curve_df["day"] == max(day_points)].sort_values("ltv", ascending=False)

    default_keys = rank["level_key"].head(int(top_n)).tolist()
    all_keys = sorted(curve_df["level_key"].unique().tolist())

    selected_keys = st.multiselect(
        "Select series to compare",
        options=all_keys,
        default=default_keys,
        key="cv_keys"
    )

    # 작은 표본 노이즈 참고용 요약
    with st.expander("Series Summary (D7 기준)"):
        d_last = curve_df[curve_df["day"] == max(day_points)].copy()
        d_last = d_last[d_last["level_key"].isin(selected_keys)].copy()
        show_cols = ["level_key", "installs", "cost", "revenue", "ltv", "roas"]
        st.dataframe(d_last[show_cols].sort_values(curve_metric, ascending=False), use_container_width=True)

    title = f"Cumulative Curve ({curve_level}) - days={list(day_points)}"
    show_ltv_curve(curve_df, metric=curve_metric, selected_keys=selected_keys, title=title)