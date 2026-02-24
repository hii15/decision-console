import unittest
from pathlib import Path

import pandas as pd

from data_processing.loader import preprocess_events, preprocess_installs
from data_processing.ltv_calculator import calculate_d7_ltv
from decision.decision_engine import run_decision_engine


class PipelineSmokeTests(unittest.TestCase):
    def test_end_to_end_pipeline_with_fixture_files(self):
        root = Path(__file__).parent / "fixtures"
        installs_raw = pd.read_csv(root / "installs_sample.csv")
        events_raw = pd.read_csv(root / "events_sample.csv")

        installs = preprocess_installs(installs_raw, generate_cost_if_missing=True)
        events = preprocess_events(events_raw)

        d7 = calculate_d7_ltv(installs, events)
        out = run_decision_engine(
            d7,
            channel_map={
                "facebook": "Performance",
                "googleadwords_int": "Performance",
                "tiktok_int": "Performance",
            },
            base_target=1.0,
        )

        self.assertIn("decision", out.columns)
        self.assertIn("engine_version", out.columns)
        self.assertTrue(len(out) >= 1)


if __name__ == "__main__":
    unittest.main()
