import streamlit as st
import pandas as pd
import re

from data_processing.loader import load_file, preprocess_installs, preprocess_events
from data_processing.ltv_calculator import calculate_d7_ltv
from data_processing.daily_metrics import compute_daily_d7_metrics
from data_processing.cohort_curve import compute_ltv_curve
from data_processing.quality import compute_data_quality_metrics
from data_processing.payback import compute_payback_days
from data_processing.momentum import compute_momentum_metrics
from data_processing.cost_join import apply_cost_report
from data_processing.filters import apply_global_filters

from decision.decision_engine import run_decision_engine, ENGINE_VERSION
from visualization.decision_table import style_decision_table
from visualization.heatmap import show_risk_heatmap
from visualization.ltv_curve import show_ltv_curve

from config.channel_config import DEFAULT_CHANNEL_MAP
from config.runtime_config import load_runtime_config
from config.rule_changelog import RULE_CHANGELOG


def _to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


@st.cache_data(show_spinner=False)
def _cached_d7_ltv(installs: pd.DataFrame, events: pd.DataFrame, min_maturity_days: int, as_of_time: pd.Timestamp) -> pd.DataFrame:
    return calculate_d7_ltv(installs, events, min_maturity_days=min_maturity_days, as_of_time=as_of_time)


@st.cache_data(show_spinner=False)
def _cached_daily(installs: pd.DataFrame, events: pd.DataFrame, level: str) -> pd.DataFrame:
    return compute_daily_d7_metrics(installs, events, level=level)


@st.cache_data(show_spinner=False)
def _cached_curve(installs: pd.DataFrame, events: pd.DataFrame, level: str, day_points: tuple, lookback_days):
    return compute_ltv_curve(
        installs, events, level=level, day_points=day_points, lookback_days=lookback_days, purchase_event_name="af_purchase"
    )


@st.cache_data(show_spinner=False)
def _cached_payback(installs: pd.DataFrame, events: pd.DataFrame, level: str, max_day: int) -> pd.DataFrame:
    return compute_payback_days(installs, events, level=level, max_day=max_day, purchase_event_name="af_purchase")


@st.cache_data(show_spinner=False)
def _cached_momentum(daily_df: pd.DataFrame) -> pd.DataFrame:
    return compute_momentum_metrics(daily_df)


st.set_page_config(layout="wide")
st.title("UA 의사결정 지원 콘솔")
st.markdown("---")
st.caption("시간 기준: UTC 업로드 데이터를 KST(UTC+9) 기준으로 변환해 분석합니다.")

# 업로드
col1, col2 = st.columns(2)
with col1:
    installs_file = st.file_uploader("인스톨 Raw 업로드 (CSV/XLSX)", type=["csv", "xlsx"])
with col2:
    events_file = st.file_uploader("이벤트 Raw 업로드 (CSV/XLSX)", type=["csv", "xlsx"])

mmp_source = st.selectbox("MMP 소스", ["appsflyer", "adjust", "singular"], index=0)
config_file = st.file_uploader("(선택) Runtime 설정 JSON", type=["json"])
cost_file = st.file_uploader("(선택) Cost Report 업로드 (CSV/XLSX)", type=["csv", "xlsx"])

if not installs_file or not events_file:
    st.info("인스톨/이벤트 파일을 모두 업로드해 주세요.")
    st.stop()

try:
    runtime_cfg = load_runtime_config(config_file)
except Exception as e:
    st.error(f"Runtime 설정 JSON 파싱 실패: {e}")
    st.stop()

try:
    installs_df = preprocess_installs(load_file(installs_file), mmp_source=mmp_source)
except Exception as e:
    st.error(f"Installs 파일 처리 실패: {e}")
    st.stop()

try:
    events_df = preprocess_events(load_file(events_file), mmp_source=mmp_source)
except Exception as e:
    st.error(f"Events 파일 처리 실패: {e}")
    st.stop()

if cost_file is not None:
    try:
        installs_df = apply_cost_report(installs_df, load_file(cost_file))
        st.success("파일 로드 완료 + Cost Report 조인 적용")
    except Exception as e:
        st.error(f"Cost Report 처리 실패: {e}")
        st.stop()
else:
    st.success("파일 로드 완료")

if "cost_source" in installs_df.columns and (installs_df["cost_source"] == "missing_default_zero").any():
    st.warning("⚠️ cost 컬럼이 없어 cost=0으로 처리되었습니다. 현재 ROAS/의사결정은 보수적으로 해석해 주세요.")


# 전역 필터
with st.expander("전역 필터", expanded=False):
    f1, f2, f3 = st.columns([1, 1, 2])

    source_options = sorted(installs_df["media_source"].astype(str).dropna().unique().tolist())
    campaign_options = sorted(installs_df["campaign"].astype(str).dropna().unique().tolist())

    with f1:
        selected_sources = st.multiselect("미디어 소스", options=source_options, default=source_options, key="gf_sources")
    with f2:
        selected_campaigns = st.multiselect("캠페인", options=campaign_options, default=campaign_options, key="gf_campaigns")
    with f3:
        dmin = pd.to_datetime(installs_df["install_date"], errors="coerce").min()
        dmax = pd.to_datetime(installs_df["install_date"], errors="coerce").max()
        selected_range = st.date_input("설치일 범위", value=(dmin, dmax), min_value=dmin, max_value=dmax, key="gf_range")

    if isinstance(selected_range, tuple) and len(selected_range) == 2:
        start_date, end_date = selected_range
    else:
        start_date = dmin
        end_date = dmax

installs_df, events_df = apply_global_filters(
    installs_df,
    events_df,
    selected_sources=selected_sources if len(selected_sources) > 0 else None,
    selected_campaigns=selected_campaigns if len(selected_campaigns) > 0 else None,
    start_date=start_date,
    end_date=end_date,
)

st.caption(f"필터 적용 결과: installs {len(installs_df):,}건 / events {len(events_df):,}건")

if installs_df.empty:
    st.warning("필터 조건에 맞는 installs 데이터가 없습니다. 전역 필터를 조정해 주세요.")
    st.stop()

with st.expander("데이터 품질 진단", expanded=False):
    dq = compute_data_quality_metrics(installs_df, events_df)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Installs 행수", f"{dq['installs_rows']:,}")
    c2.metric("Events 행수", f"{dq['events_rows']:,}")
    c3.metric("Event ID 매칭률", f"{dq['event_id_match_rate'] * 100:.1f}%")
    c4.metric("구매 이벤트 비중", f"{dq['purchase_event_coverage'] * 100:.1f}%")
    c5.metric("품질 점수", f"{dq['quality_score']:.1f}")

    dqc1, dqc2 = st.columns(2)
    dqc1.write(
        f"- installs 타임스탬프 파싱 실패: {dq['installs_invalid_ts']:,} "
        f"({dq['installs_invalid_ts_rate'] * 100:.1f}%)"
    )
    dqc2.write(
        f"- events 타임스탬프 파싱 실패: {dq['events_invalid_ts']:,} "
        f"({dq['events_invalid_ts_rate'] * 100:.1f}%)"
    )

    st.write(
        f"- 매칭된 Event ID: {dq['matched_event_id_count']:,} / {dq['event_id_count']:,} "
        f"(미매칭 {dq['unmatched_event_id_count']:,})"
    )
    st.write(
        f"- revenue 결측 이벤트: {dq['missing_revenue_count']:,} "
        f"({dq['missing_revenue_rate'] * 100:.1f}%)"
    )
    tz_warning = "UTC 컬럼 기반으로 KST 변환 적용" if dq["events_has_utc_col"] else "event_time_utc 컬럼이 없어 timezone 기준이 불명확"
    st.write(
        f"- timezone 경고: {tz_warning} (naive 비율 {dq['events_timezone_naive_rate'] * 100:.1f}%)"
    )

base_target = st.number_input(
    "기준 Target D7 ROAS (예: 1.0 = 100%)",
    min_value=0.0,
    value=float(runtime_cfg.base_target) if runtime_cfg.base_target is not None else 1.0,
    step=0.05
)

st.markdown("## 채널 타입 설정")
unique_sources = sorted(list(installs_df["media_source"].astype(str).dropna().unique()))
channel_defaults = [runtime_cfg.channel_map.get(source, DEFAULT_CHANNEL_MAP.get(source, "Performance")) for source in unique_sources]

editor_df = pd.DataFrame({"media_source": unique_sources, "channel_type": channel_defaults})
edited_channel_df = st.data_editor(
    editor_df,
    width="stretch",
    hide_index=True,
    column_config={
        "channel_type": st.column_config.SelectboxColumn(
            "channel_type",
            options=["Performance", "Hybrid", "Branding"],
            required=True,
        )
    },
    key="channel_map_editor",
)
channel_map = dict(zip(edited_channel_df["media_source"], edited_channel_df["channel_type"]))

settings_col1, settings_col2 = st.columns(2)
with settings_col1:
    min_maturity_days = st.number_input("D7 계산 최소 코호트 성숙일", min_value=0, value=7, step=1)
    max_install_time = pd.to_datetime(installs_df["install_time"], errors="coerce").max()
    as_of_date = st.date_input("코호트 성숙 기준일(as-of)", value=max_install_time.date())
with settings_col2:
    min_installs_for_scale = st.number_input(
        "Scale 최소 installs",
        min_value=1,
        value=int(runtime_cfg.min_installs_for_scale),
        step=10,
    )

st.markdown("---")

# ====== Tabs ======
tab1, tab2, tab3 = st.tabs(["의사결정", "리스크 히트맵", "LTV 커브"])

# ====== Decision View ======
with tab1:
    try:
        result_df = _cached_d7_ltv(installs_df, events_df, int(min_maturity_days), pd.Timestamp(as_of_date))
        final_df = run_decision_engine(
        result_df,
        channel_map,
        base_target,
        multiplier_map=runtime_cfg.multiplier_map,
        decision_rules=runtime_cfg.decision_rules,
        fallback_decision=runtime_cfg.fallback_decision,
        min_installs_for_scale=int(min_installs_for_scale),
        )
    except Exception as e:
        st.error(f"의사결정 계산 실패: {e}")
        st.stop()

    st.markdown("## 의사결정 테이블")
    st.caption("포트폴리오 관점: 채널별 D7 성과와 목표 대비 갭을 바탕으로 예산 증액/테스트/축소 우선순위를 빠르게 확인합니다.")
    st.caption(f"Engine version: {ENGINE_VERSION}")
    if "mature_ratio" in final_df.columns:
        st.caption(f"D7 성숙 코호트 비율 평균: {final_df['mature_ratio'].mean() * 100:.1f}%")

    payback_for_decision = _cached_payback(installs_df, events_df, level="media_source", max_day=30)
    payback_for_decision = payback_for_decision.rename(columns={"level_key": "media_source"})[["media_source", "payback_day"]]

    daily_for_decision = _cached_daily(installs_df, events_df, level="media_source")
    momentum_for_decision = _cached_momentum(daily_for_decision)
    momentum_latest = (
        momentum_for_decision.sort_values(["level_key", "install_date"])
        .groupby("level_key", as_index=False)
        .tail(1)[["level_key", "roas_ma3", "roas_dod"]]
        .rename(columns={"level_key": "media_source"})
    )

    final_df = final_df.merge(payback_for_decision, on="media_source", how="left")
    final_df = final_df.merge(momentum_latest, on="media_source", how="left")

    st.write(style_decision_table(final_df))
    with st.expander("결정 사유 분포", expanded=False):
        st.dataframe(final_df["decision_reason"].value_counts(dropna=False).rename_axis("reason").reset_index(name="count"), width="stretch")

    with st.expander("룰 버전 changelog", expanded=False):
        current = RULE_CHANGELOG.get(ENGINE_VERSION)
        if current is None:
            st.warning(f"{ENGINE_VERSION} 버전의 changelog가 등록되어 있지 않습니다.")
        else:
            st.write(f"- 현재 버전: **{ENGINE_VERSION}**")
            st.write(f"- 반영일: {current['date']}")
            st.write(f"- 요약: {current['summary']}")
            st.write("- 규칙 변경 사항:")
            for rule_line in current["rules"]:
                st.write(f"  - {rule_line}")

    st.download_button(
        "의사결정 CSV 다운로드",
        data=_to_csv_bytes(final_df),
        file_name="decision_view.csv",
        mime="text/csv",
    )

    st.markdown("## 매체별 D7 ROAS")
    chart_df = final_df.groupby("media_source")["d7_roas"].mean().reset_index()
    st.bar_chart(chart_df.set_index("media_source"))

    st.markdown("## 페이백 (v1)")
    payback_level = st.selectbox(
        "페이백 레벨",
        ["media_source", "campaign", "media_source_campaign"],
        index=0,
        key="pb_level"
    )
    payback_max_day = st.number_input("페이백 최대 탐색일", min_value=7, value=30, step=1, key="pb_max_day")

    payback_df = _cached_payback(installs_df, events_df, level=payback_level, max_day=int(payback_max_day))
    payback_show = payback_df.copy()
    payback_show["payback_day"] = payback_show["payback_day"].apply(
        lambda x: "미도달" if pd.isna(x) else str(int(x))
    )
    st.dataframe(payback_show, width="stretch")

# ====== Risk Heatmap ======
with tab2:
    st.markdown("## 리스크 히트맵 (Install Cohort 기반)")
    st.caption("포트폴리오 관점: 날짜×레벨 셀 단위로 리스크 구간을 시각화해, 변동성이 큰 구간을 빠르게 탐지합니다.")

    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])

    with c1:
        level = st.selectbox(
            "히트맵 레벨",
            ["media_source", "campaign", "media_source_campaign"],
            index=0,
            key="hm_level"
        )

    with c2:
        metric = st.selectbox(
            "지표",
            ["d7_roas", "cost", "installs", "d7_revenue"],
            index=0,
            key="hm_metric"
        )

    with c3:
        lookback = st.selectbox(
            "조회 기간",
            ["최근 14일", "최근 30일", "최근 60일", "All"],
            index=1,
            key="hm_range"
        )

    with c4:
        enable_mask = st.checkbox("저볼륨 셀 마스킹", value=True, key="hm_mask")

    min_installs = None
    min_cost = None
    if enable_mask:
        m1, m2 = st.columns(2)
        with m1:
            min_installs = st.number_input("셀당 최소 installs", min_value=0, value=30, step=10, key="hm_min_inst")
        with m2:
            min_cost = st.number_input("셀당 최소 cost", min_value=0.0, value=50.0, step=10.0, key="hm_min_cost")

    try:
        daily_df = _cached_daily(installs_df, events_df, level=level)
        daily_df["install_date"] = pd.to_datetime(daily_df["install_date"])
        max_date = daily_df["install_date"].max()
    except Exception as e:
        st.error(f"히트맵 계산 실패: {e}")
        st.stop()

    if lookback != "All":
        days = int(re.search(r"\d+", lookback).group())
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

    st.download_button(
        "히트맵 소스 CSV 다운로드",
        data=_to_csv_bytes(daily_df),
        file_name="heatmap_daily_metrics.csv",
        mime="text/csv",
        key="dl_heatmap",
    )

    st.markdown("## 트렌드 / MA3 (D7 ROAS)")
    momentum_df = _cached_momentum(daily_df)

    trend_keys = sorted(momentum_df["level_key"].unique().tolist())
    trend_default = trend_keys[: min(5, len(trend_keys))]
    selected_trend_keys = st.multiselect(
        "트렌드 시리즈 선택",
        options=trend_keys,
        default=trend_default,
        key="trend_keys",
    )

    if selected_trend_keys:
        trend_plot = momentum_df[momentum_df["level_key"].isin(selected_trend_keys)].copy()
        st.line_chart(
            trend_plot.pivot_table(
                index="install_date",
                columns="level_key",
                values="d7_roas",
                aggfunc="mean",
            )
        )
        st.line_chart(
            trend_plot.pivot_table(
                index="install_date",
                columns="level_key",
                values="roas_ma3",
                aggfunc="mean",
            )
        )

        latest = (
            trend_plot.sort_values(["level_key", "install_date"])
            .groupby("level_key", as_index=False)
            .tail(1)
            .loc[:, ["level_key", "install_date", "d7_roas", "roas_ma3", "roas_dod"]]
            .sort_values("d7_roas", ascending=False)
        )
        st.dataframe(latest, width="stretch")

    st.download_button(
        "트렌드 CSV 다운로드",
        data=_to_csv_bytes(momentum_df),
        file_name="trend_momentum.csv",
        mime="text/csv",
        key="dl_trend",
    )

# ====== LTV Curve ======
with tab3:
    st.markdown("## LTV / ROAS 커브 (Install Cohort 누적)")
    st.caption("포트폴리오 관점: 누적 수익/ROAS 곡선으로 채널의 회수 속도와 성장 잠재력을 비교합니다.")

    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])

    with c1:
        curve_level = st.selectbox(
            "커브 레벨",
            ["media_source", "campaign", "media_source_campaign"],
            index=0,
            key="cv_level"
        )

    with c2:
        curve_metric = st.selectbox(
            "지표",
            ["ltv", "roas", "revenue"],
            index=0,
            key="cv_metric"
        )

    with c3:
        curve_range = st.selectbox(
            "코호트 조회 기간",
            ["최근 14일", "최근 30일", "최근 60일", "All"],
            index=1,
            key="cv_range"
        )

    with c4:
        top_n = st.number_input("자동 선택 Top N", min_value=1, value=8, step=1, key="cv_topn")

    with c5:
        show_sample = st.checkbox("범례에 N/Cost 표시", value=True, key="cv_show_sample")

    opt1, opt2, opt3 = st.columns([1, 1, 1])
    with opt1:
        fade_small = st.checkbox("소표본 흐리게", value=True, key="cv_fade")
    with opt2:
        n_low = st.number_input("흐림 임계값 (low N)", min_value=1, value=50, step=10, key="cv_nlow")
    with opt3:
        n_high = st.number_input("진하게 임계값 (high N)", min_value=10, value=800, step=50, key="cv_nhigh")

    day_points_input = st.text_input("커브 day_points (콤마 구분)", value="0,1,3,7")
    day_points = tuple(sorted({int(x.strip()) for x in day_points_input.split(",") if x.strip().isdigit()}))
    if not day_points:
        st.warning("유효한 day_points가 없어 기본값 (0,1,3,7)을 사용합니다.")
        day_points = (0, 1, 3, 7)

    lookback_days = None
    if curve_range != "All":
        lookback_days = int(re.search(r"\d+", curve_range).group())

    try:
        curve_df = _cached_curve(
            installs_df,
            events_df,
            level=curve_level,
            day_points=day_points,
            lookback_days=lookback_days,
        )
    except Exception as e:
        st.error(f"커브 계산 실패: {e}")
        st.stop()

    if curve_df.empty:
        st.warning("커브 데이터가 없습니다. 필터를 변경해 보세요.")
        st.stop()

    last_day = max(day_points)
    if curve_metric == "revenue":
        rank = curve_df[curve_df["day"] == last_day].sort_values("revenue", ascending=False)
    elif curve_metric == "roas":
        rank = curve_df[curve_df["day"] == last_day].sort_values("roas", ascending=False)
    else:
        rank = curve_df[curve_df["day"] == last_day].sort_values("ltv", ascending=False)

    default_keys = rank["level_key"].head(int(top_n)).tolist()
    all_keys = sorted(curve_df["level_key"].unique().tolist())

    selected_keys = st.multiselect(
        "비교할 시리즈 선택",
        options=all_keys,
        default=default_keys,
        key="cv_keys"
    )

    with st.expander("시리즈 요약 (D7 기준)"):
        d_last = curve_df[curve_df["day"] == last_day].copy()
        d_last = d_last[d_last["level_key"].isin(selected_keys)].copy()
        show_cols = ["level_key", "installs", "cost", "revenue", "ltv", "roas"]
        st.dataframe(d_last[show_cols].sort_values(curve_metric, ascending=False), width="stretch")

    st.download_button(
        "커브 CSV 다운로드",
        data=_to_csv_bytes(curve_df),
        file_name="ltv_curve.csv",
        mime="text/csv",
        key="dl_curve",
    )

    title = f"Cumulative Curve ({curve_level}) - days={list(day_points)}"
    target_line = base_target if curve_metric == "roas" else None

    show_ltv_curve(
        curve_df,
        metric=curve_metric,
        selected_keys=selected_keys,
        title=title,
        show_sample_in_legend=show_sample,
        target_roas=target_line,
        fade_by_sample=fade_small,
        n_low=int(n_low),
        n_high=int(n_high),
    )
