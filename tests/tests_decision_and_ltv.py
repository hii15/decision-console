import unittest
import pandas as pd

from data_processing.ltv_calculator import calculate_d7_ltv
from decision.decision_engine import run_decision_engine
from data_processing.quality import compute_data_quality_metrics


class DecisionAndLTVTests(unittest.TestCase):
    def setUp(self):
        self.installs = pd.DataFrame(
            {
                "appsflyer_id": ["u1", "u2", "u3"],
                "media_source": ["facebook", "googleadwords_int", "facebook"],
                "campaign": ["c1", "c2", "c1"],
                "install_time": pd.to_datetime(["2026-01-01", "2026-01-01", "2026-01-02"]),
                "cost": [10.0, 20.0, 10.0],
            }
        )
        self.events = pd.DataFrame(
            {
                "appsflyer_id": ["u1", "u1", "u2", "uX"],
                "event_name": ["af_purchase", "af_purchase", "af_purchase", "af_purchase"],
                "event_time": pd.to_datetime(["2026-01-02", "2026-01-09", "2026-01-03", "2026-01-02"]),
                "revenue": [15.0, 20.0, 5.0, 100.0],
            }
        )

    def test_calculate_d7_ltv_filters_to_d7_and_matched_ids(self):
        out = calculate_d7_ltv(self.installs, self.events)
        row_c1 = out[(out["media_source"] == "facebook") & (out["campaign"] == "c1")].iloc[0]
        row_c2 = out[(out["media_source"] == "googleadwords_int") & (out["campaign"] == "c2")].iloc[0]

        self.assertAlmostEqual(row_c1["d7_revenue"], 15.0)
        self.assertAlmostEqual(row_c1["cost"], 20.0)
        self.assertAlmostEqual(row_c1["d7_roas"], 0.75)
        self.assertAlmostEqual(row_c2["d7_revenue"], 5.0)

    def test_run_decision_engine_applies_rule_thresholds(self):
        base = pd.DataFrame(
            {
                "media_source": ["facebook", "googleadwords_int", "tiktok_int"],
                "campaign": ["c1", "c2", "c3"],
                "d7_roas": [1.1, 0.85, 0.4],
            }
        )
        channel_map = {
            "facebook": "Performance",
            "googleadwords_int": "Performance",
            "tiktok_int": "Performance",
        }
        out = run_decision_engine(base, channel_map, base_target=1.0)
        self.assertEqual(out.loc[0, "decision"], "Scale")
        self.assertEqual(out.loc[1, "decision"], "Test")
        self.assertEqual(out.loc[2, "decision"], "Reduce")

    def test_quality_metrics(self):
        installs = self.installs.copy()
        events = self.events.copy()
        installs.loc[0, "install_time"] = pd.NaT
        events.loc[0, "event_time"] = pd.NaT

        m = compute_data_quality_metrics(installs, events)
        self.assertEqual(m["installs_rows"], 3)
        self.assertEqual(m["events_rows"], 4)
        self.assertEqual(m["installs_invalid_ts"], 1)
        self.assertEqual(m["events_invalid_ts"], 1)
        self.assertGreaterEqual(m["event_id_match_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()