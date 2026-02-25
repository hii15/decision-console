from __future__ import annotations

from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data_processing.loader import load_file
from data_processing.adapters import ADAPTER_REGISTRY
from data_processing.canonical_schema import coerce_canonical_types
from data_processing.metrics_engine import calculate_media_metrics
from data_processing.decision_engine import apply_decision_logic
from data_processing.liveops_analysis import compare_liveops_impact


MMP_LIST = ["AppsFlyer", "Adjust", "Singular"]


def _read_csv(path: str) -> pd.DataFrame:
    # load_file expects file-like or path string and normalizes columns.
    return load_file(path)


def run_experiments(input_root: str = "dummy_data", output_root: str = "dummy_data/experiments") -> tuple[str, str]:
    out_dir = Path(output_root)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    decision_rows = []

    for mmp in MMP_LIST:
        slug = mmp.lower()
        installs_raw = _read_csv(f"{input_root}/{slug}/installs_raw.csv")
        events_raw = _read_csv(f"{input_root}/{slug}/events_raw.csv")
        cost_raw = _read_csv(f"{input_root}/{slug}/cost_raw.csv")

        adapter = ADAPTER_REGISTRY[mmp]()
        installs = adapter.normalize_installs(installs_raw)
        events = adapter.normalize_events(events_raw)
        cost = adapter.normalize_cost(cost_raw)

        canonical = coerce_canonical_types(installs, events, cost)

        metrics = calculate_media_metrics(canonical.installs, canonical.events, canonical.cost)
        decisions = apply_decision_logic(metrics, target_roas=1.0, min_installs=200)
        liveops = compare_liveops_impact(
            canonical.installs,
            canonical.events,
            event_start="2026-01-15",
            event_end="2026-01-21",
            baseline_days=7,
        )

        summary_rows.append(
            {
                "mmp": mmp,
                "total_installs": int(metrics["installs"].sum()),
                "total_spend": float(metrics["spend"].sum()),
                "avg_d7_roas": float(metrics["d7_roas"].mean()),
                "liveops_impact": float(liveops.loc[0, "impact"]),
            }
        )

        temp = decisions[["media_source", "campaign", "installs", "d7_roas", "decision"]].copy()
        temp.insert(0, "mmp", mmp)
        decision_rows.append(temp)

    summary_df = pd.DataFrame(summary_rows)
    decision_df = pd.concat(decision_rows, ignore_index=True)

    summary_path = out_dir / "mmp_experiment_summary.csv"
    decision_path = out_dir / "mmp_decision_table.csv"

    summary_df.to_csv(summary_path, index=False)
    decision_df.to_csv(decision_path, index=False)

    return str(summary_path), str(decision_path)


if __name__ == "__main__":
    summary, decisions = run_experiments()
    print(f"summary: {summary}")
    print(f"decisions: {decisions}")
