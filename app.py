import pandas as pd
import streamlit as st

from data_processing.loader import load_file
from data_processing.adapters import ADAPTER_REGISTRY
from data_processing.canonical_schema import coerce_canonical_types
from data_processing.metrics_engine import calculate_media_metrics, calculate_cohort_curve
from data_processing.decision_engine import apply_decision_logic
from data_processing.liveops_analysis import compare_liveops_impact
from dummy_data.generate_dummy_data import get_mmp_raw_bundle, write_mmp_dummy_data
from dummy_data.run_mmp_experiments import run_experiments


st.set_page_config(layout="wide")
st.title("Game UA Decision Engine")
st.caption("MMP Raw 기반 UA 의사결정 콘솔")


def _empty_cost_template(installs: pd.DataFrame) -> pd.DataFrame:
    if installs.empty:
        return pd.DataFrame(columns=["date", "media_source", "campaign", "impressions", "clicks", "spend"])

    base = installs.copy()
    base["date"] = pd.to_datetime(base["install_time"], errors="coerce").dt.date
    grouped = base.groupby(["date", "media_source", "campaign"], as_index=False).agg(installs=("user_key", "count"))
    grouped["impressions"] = grouped["installs"] * 40
    grouped["clicks"] = grouped["installs"] * 5
    grouped["spend"] = grouped["installs"] * 3.0
    return grouped[["date", "media_source", "campaign", "impressions", "clicks", "spend"]]


def _normalize_uploaded_data(mmp: str, installs_raw: pd.DataFrame, events_raw: pd.DataFrame, cost_raw: pd.DataFrame | None):
    adapter_cls = ADAPTER_REGISTRY[mmp]
    adapter = adapter_cls()

    installs = adapter.normalize_installs(installs_raw)
    events = adapter.normalize_events(events_raw)
    cost = adapter.normalize_cost(cost_raw) if cost_raw is not None else pd.DataFrame()

    canonical = coerce_canonical_types(installs=installs, events=events, cost=cost)
    if canonical.cost.empty or canonical.cost["spend"].sum() == 0:
        canonical.cost = _empty_cost_template(canonical.installs)
    return canonical


def _run_and_load_experiment_reports(seed: int):
    write_mmp_dummy_data(output_dir="dummy_data", seed=seed)
    summary_path, decision_path, report_path = run_experiments(input_root="dummy_data", output_root="dummy_data/experiments")
    return pd.read_csv(summary_path), pd.read_csv(decision_path), report_path


tab_upload, tab_decision, tab_curve, tab_liveops, tab_experiment = st.tabs([
    "Upload Data",
    "UA Decision",
    "Cohort Curve",
    "LiveOps Impact",
    "Experiment Report",
])

with tab_upload:
    st.subheader("Upload Data")
    mmp = st.selectbox("MMP 선택", ["AppsFlyer", "Adjust", "Singular"])

    st.markdown("#### Quick Demo")
    q1, q2 = st.columns([1, 2])
    dummy_seed = q1.number_input("Dummy Seed", min_value=0, value=42, step=1)
    if q2.button("Load MMP Dummy Raw", use_container_width=True):
        installs_raw, events_raw, cost_raw = get_mmp_raw_bundle(mmp=mmp, seed=int(dummy_seed))
        canonical = _normalize_uploaded_data(mmp, installs_raw, events_raw, cost_raw)
        st.session_state["canonical"] = canonical
        st.success(f"{mmp} 더미 데이터 로드 완료")

    st.markdown("#### Manual Upload")
    c1, c2, c3 = st.columns(3)
    installs_file = c1.file_uploader("Install Raw", type=["csv", "xlsx"], key="installs")
    events_file = c2.file_uploader("Event Raw", type=["csv", "xlsx"], key="events")
    cost_file = c3.file_uploader("Cost Raw", type=["csv", "xlsx"], key="cost")

    if installs_file and events_file:
        installs_raw = load_file(installs_file)
        events_raw = load_file(events_file)
        cost_raw = load_file(cost_file) if cost_file else None

        canonical = _normalize_uploaded_data(mmp, installs_raw, events_raw, cost_raw)
        st.session_state["canonical"] = canonical

        st.success("정규화 완료")
    else:
        st.info("Install / Event 파일을 업로드하거나, 위 Dummy 버튼을 눌러 주세요.")

    canonical_preview = st.session_state.get("canonical")
    if canonical_preview is not None:
        st.write("Installs Preview")
        st.dataframe(canonical_preview.installs.head(10), use_container_width=True)
        st.write("Events Preview")
        st.dataframe(canonical_preview.events.head(10), use_container_width=True)
        st.write("Cost Preview")
        st.dataframe(canonical_preview.cost.head(10), use_container_width=True)

canonical = st.session_state.get("canonical")

with tab_decision:
    st.subheader("UA Decision")
    if canonical is None:
        st.warning("먼저 Upload Data 탭에서 데이터를 업로드하세요.")
    else:
        target_roas = st.number_input("Target ROAS", min_value=0.0, value=1.0, step=0.05)
        min_installs = st.number_input("최소 Install 기준", min_value=1, value=200, step=10)

        metrics = calculate_media_metrics(canonical.installs, canonical.events, canonical.cost)
        decision_df = apply_decision_logic(metrics, target_roas=target_roas, min_installs=int(min_installs))
        st.dataframe(decision_df, use_container_width=True)

with tab_curve:
    st.subheader("Cohort Curve")
    if canonical is None:
        st.warning("먼저 Upload Data 탭에서 데이터를 업로드하세요.")
    else:
        curve = calculate_cohort_curve(canonical.installs, canonical.events, max_day=30)
        if curve.empty:
            st.info("곡선을 계산할 데이터가 없습니다.")
        else:
            media_sources = sorted(curve["media_source"].unique().tolist())
            selected = st.multiselect("매체 선택", media_sources, default=media_sources)
            view = curve[curve["media_source"].isin(selected)]
            st.line_chart(view, x="day", y="ltv", color="media_source")

with tab_liveops:
    st.subheader("LiveOps Impact")
    if canonical is None:
        st.warning("먼저 Upload Data 탭에서 데이터를 업로드하세요.")
    else:
        col1, col2, col3 = st.columns(3)
        start = col1.date_input("이벤트 시작일")
        end = col2.date_input("이벤트 종료일")
        baseline_days = col3.number_input("비교 기간(일)", min_value=1, value=7, step=1)

        if start > end:
            st.error("시작일은 종료일보다 늦을 수 없습니다.")
        else:
            impact_df = compare_liveops_impact(
                canonical.installs,
                canonical.events,
                event_start=str(start),
                event_end=str(end),
                baseline_days=int(baseline_days),
            )
            st.dataframe(impact_df, use_container_width=True)
            st.metric("LiveOps Impact (D7 LTV Delta)", f"{impact_df.loc[0, 'impact']:.4f}")

with tab_experiment:
    st.subheader("Experiment Report")
    e1, e2 = st.columns([1, 2])
    report_seed = e1.number_input("Experiment Seed", min_value=0, value=42, step=1)
    if e2.button("Run MMP Experiments", use_container_width=True):
        summary_df, decision_df, report_path = _run_and_load_experiment_reports(int(report_seed))
        st.session_state["exp_summary"] = summary_df
        st.session_state["exp_decision"] = decision_df
        st.session_state["exp_report_path"] = report_path
        st.success("실험 리포트 생성 완료")

    summary = st.session_state.get("exp_summary")
    decisions = st.session_state.get("exp_decision")
    report_path = st.session_state.get("exp_report_path")

    if summary is None or decisions is None or report_path is None:
        st.info("Run MMP Experiments 버튼을 눌러 리포트를 생성하세요.")
    else:
        st.markdown("### Summary")
        st.dataframe(summary, use_container_width=True)

        st.markdown("### Decision Table")
        st.dataframe(decisions, use_container_width=True)

        st.markdown("### Markdown Insight")
        st.code(open(report_path, "r", encoding="utf-8").read(), language="markdown")
