import streamlit as st
import pandas as pd

# ===== 내부 모듈 =====
from data_processing.loader import load_file, preprocess_installs, preprocess_events
from data_processing.ltv_calculator import calculate_d7_ltv
from decision.decision_engine import run_decision_engine
from visualization.decision_table import style_decision_table
from config.channel_config import DEFAULT_CHANNEL_MAP


st.set_page_config(layout="wide")
st.title("UA Decision Support Console")

st.markdown("---")

# =============================
# 1️⃣ 파일 업로드
# =============================

col1, col2 = st.columns(2)

with col1:
    installs_file = st.file_uploader("Upload Installs Raw (CSV/XLSX)", type=["csv", "xlsx"])

with col2:
    events_file = st.file_uploader("Upload Events Raw (CSV/XLSX)", type=["csv", "xlsx"])

if installs_file and events_file:

    # =============================
    # 2️⃣ 데이터 로딩
    # =============================
    installs_df = preprocess_installs(load_file(installs_file))
    events_df = preprocess_events(load_file(events_file))

    st.success("Files Loaded Successfully")

    # =============================
    # 3️⃣ Base Target 입력
    # =============================
    base_target = st.number_input(
        "Base Target D7 ROAS (예: 1.0 = 100%)",
        min_value=0.0,
        value=1.0,
        step=0.05
    )

    # =============================
    # 4️⃣ Channel Type 수정 UI
    # =============================
    st.markdown("### Channel Type Configuration")

    unique_sources = installs_df["media_source"].unique()

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

    # =============================
    # 5️⃣ LTV 계산
    # =============================
    result_df = calculate_d7_ltv(installs_df, events_df)

    # =============================
    # 6️⃣ Decision Engine 실행
    # =============================
    final_df = run_decision_engine(result_df, channel_map, base_target)

    # =============================
    # 7️⃣ 결과 테이블 출력
    # =============================
    st.markdown("## Decision Table")

    styled_table = style_decision_table(final_df)
    st.write(styled_table)

    # =============================
    # 8️⃣ 기본 시각화
    # =============================
    st.markdown("## D7 ROAS by Media Source")

    chart_df = final_df.groupby("media_source")["d7_roas"].mean().reset_index()

    st.bar_chart(
        chart_df.set_index("media_source")
    )

else:
    st.info("Please upload both installs and events files.")