import unittest
import pandas as pd

from data_processing.ltv_calculator import calculate_d7_ltv
from data_processing.loader import preprocess_installs, preprocess_events
from decision.decision_engine import run_decision_engine, ENGINE_VERSION
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
        self.assertTrue((out["engine_version"] == ENGINE_VERSION).all())

    def test_run_decision_engine_with_rule_table(self):
        base = pd.DataFrame(
            {
                "media_source": ["facebook", "googleadwords_int"],
                "campaign": ["c1", "c2"],
                "d7_roas": [0.95, 0.55],
            }
        )
        out = run_decision_engine(
            base,
            channel_map={"facebook": "Performance", "googleadwords_int": "Performance"},
            base_target=1.0,
            decision_rules=[
                {"op": ">=", "threshold": 0.9, "decision": "Scale"},
                {"op": ">=", "threshold": 0.6, "decision": "Test"},
            ],
            fallback_decision="Reduce",
        )
        self.assertEqual(out.loc[0, "decision"], "Scale")
        self.assertEqual(out.loc[1, "decision"], "Reduce")


    def test_loader_converts_utc_to_kst(self):
        installs_raw = pd.DataFrame({
            "appsflyer_id": ["u1"],
            "install_time_utc": ["2026-01-01 00:00:00"],
            "media_source": ["facebook"],
            "campaign": ["c1"],
            "cost": [1.0],
        })
        events_raw = pd.DataFrame({
            "appsflyer_id": ["u1"],
            "event_time_utc": ["2026-01-01 00:00:00"],
            "event_name": ["af_purchase"],
            "af_revenue_usd": [1.0],
        })

        installs = preprocess_installs(installs_raw)
        events = preprocess_events(events_raw)
        self.assertEqual(installs.loc[0, "install_time"].hour, 9)
        self.assertEqual(events.loc[0, "event_time"].hour, 9)


    def test_run_decision_engine_rule_conditions(self):
        base = pd.DataFrame(
            {
                "media_source": ["facebook", "facebook"],
                "campaign": ["c1", "c2"],
                "country": ["KR", "US"],
                "d7_roas": [0.92, 0.92],
            }
        )
        out = run_decision_engine(
            base,
            channel_map={"facebook": "Performance"},
            base_target=1.0,
            decision_rules=[
                {"op": ">=", "threshold": 0.9, "decision": "Scale", "conditions": {"country": "KR"}},
                {"op": ">=", "threshold": 0.9, "decision": "Test"},
            ],
            fallback_decision="Reduce",
        )
        self.assertEqual(out.loc[0, "decision"], "Scale")
        self.assertEqual(out.loc[1, "decision"], "Test")

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
        self.assertIn("quality_score", m)
        self.assertIn("matched_event_id_count", m)
        self.assertIn("events_timezone_naive_rate", m)
        self.assertIn("events_has_utc_col", m)


if __name__ == "__main__":
    unittest.main()
