import tempfile
import unittest
from pathlib import Path

import pandas as pd

from data_processing.adapters import ADAPTER_REGISTRY
from data_processing.canonical_schema import coerce_canonical_types
from data_processing.metrics_engine import calculate_media_metrics
from dummy_data.generate_dummy_data import write_mmp_dummy_data
from dummy_data.run_mmp_experiments import run_experiments


class DummyMMPPipelineTests(unittest.TestCase):
    def test_generated_raw_files_cover_three_mmps(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            written = write_mmp_dummy_data(output_dir=tmpdir, seed=7)
            self.assertEqual(set(written.keys()), {"appsflyer", "adjust", "singular"})

            for slug, paths in written.items():
                for p in paths:
                    self.assertTrue(Path(p).exists(), f"missing generated file: {slug} {p}")

    def test_raw_to_canonical_and_metrics_runs_for_each_mmp(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            write_mmp_dummy_data(output_dir=tmpdir, seed=11)

            for mmp in ["AppsFlyer", "Adjust", "Singular"]:
                slug = mmp.lower()
                installs_raw = pd.read_csv(f"{tmpdir}/{slug}/installs_raw.csv")
                events_raw = pd.read_csv(f"{tmpdir}/{slug}/events_raw.csv")
                cost_raw = pd.read_csv(f"{tmpdir}/{slug}/cost_raw.csv")

                adapter = ADAPTER_REGISTRY[mmp]()
                canonical = coerce_canonical_types(
                    adapter.normalize_installs(installs_raw),
                    adapter.normalize_events(events_raw),
                    adapter.normalize_cost(cost_raw),
                )
                metrics = calculate_media_metrics(canonical.installs, canonical.events, canonical.cost)

                self.assertGreater(len(metrics), 0)
                self.assertIn("d7_roas", metrics.columns)

    def test_experiment_report_outputs_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_root = f"{tmpdir}/dummy"
            exp_root = f"{tmpdir}/exp"
            write_mmp_dummy_data(output_dir=data_root, seed=99)
            summary_path, decision_path = run_experiments(input_root=data_root, output_root=exp_root)

            self.assertTrue(Path(summary_path).exists())
            self.assertTrue(Path(decision_path).exists())

            summary = pd.read_csv(summary_path)
            self.assertEqual(set(summary["mmp"]), {"AppsFlyer", "Adjust", "Singular"})


if __name__ == "__main__":
    unittest.main()
