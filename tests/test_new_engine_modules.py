import unittest
import pandas as pd

from data_processing.adapters import AppsFlyerAdapter
from data_processing.canonical_schema import coerce_canonical_types
from data_processing.metrics_engine import calculate_media_metrics, calculate_cohort_curve
from data_processing.liveops_analysis import compare_liveops_impact
from data_processing.decision_engine import apply_decision_logic


class NewEngineModulesTests(unittest.TestCase):
    def test_appsflyer_adapter_maps_common_time_and_revenue_fields(self):
        installs_raw = pd.DataFrame(
            {
                "appsflyer_id": ["u1"],
                "install_time_utc": ["2026-01-01 10:00:00"],
                "media_source": ["Meta"],
                "campaign": ["C1"],
            }
        )
        events_raw = pd.DataFrame(
            {
                "appsflyer_id": ["u1"],
                "event_time_utc": ["2026-01-02 11:00:00"],
                "event_name": ["af_purchase"],
                "af_revenue_usd": [10.0],
            }
        )

        adapter = AppsFlyerAdapter()
        installs = adapter.normalize_installs(installs_raw)
        events = adapter.normalize_events(events_raw)
        canonical = coerce_canonical_types(installs, events, pd.DataFrame())

        self.assertIn("user_key", canonical.installs.columns)
        self.assertIn("install_time", canonical.installs.columns)
        self.assertIn("event_time", canonical.events.columns)
        self.assertEqual(float(canonical.events.loc[0, "revenue"]), 10.0)

    def test_metrics_only_count_purchase_events(self):
        installs = pd.DataFrame(
            {
                "user_key": ["u1", "u2"],
                "install_time": pd.to_datetime(["2026-01-01", "2026-01-01"]),
                "media_source": ["Meta", "Meta"],
                "campaign": ["C1", "C1"],
            }
        )
        events = pd.DataFrame(
            {
                "user_key": ["u1", "u2"],
                "event_time": pd.to_datetime(["2026-01-02", "2026-01-02"]),
                "event_name": ["session", "af_purchase"],
                "revenue": [999.0, 10.0],
            }
        )
        cost = pd.DataFrame(
            {
                "date": ["2026-01-01"],
                "media_source": ["Meta"],
                "campaign": ["C1"],
                "impressions": [1000],
                "clicks": [100],
                "spend": [20.0],
            }
        )

        metrics = calculate_media_metrics(installs, events, cost)
        self.assertAlmostEqual(float(metrics.loc[0, "d7_revenue"]), 10.0)
        self.assertAlmostEqual(float(metrics.loc[0, "purchase_rate"]), 0.5)

    def test_cohort_curve_keeps_media_without_events(self):
        installs = pd.DataFrame(
            {
                "user_key": ["u1", "u2"],
                "install_time": pd.to_datetime(["2026-01-01", "2026-01-01"]),
                "media_source": ["Meta", "Google"],
                "campaign": ["C1", "C1"],
            }
        )
        events = pd.DataFrame(
            {
                "user_key": ["u1"],
                "event_time": pd.to_datetime(["2026-01-02"]),
                "event_name": ["af_purchase"],
                "revenue": [10.0],
            }
        )

        curve = calculate_cohort_curve(installs, events, max_day=3)
        self.assertIn("Google", set(curve["media_source"]))
        google_ltv = curve[curve["media_source"] == "Google"]["ltv"].sum()
        self.assertAlmostEqual(float(google_ltv), 0.0)

    def test_liveops_impact_uses_purchase_only(self):
        installs = pd.DataFrame(
            {
                "user_key": ["u1", "u2"],
                "install_time": pd.to_datetime(["2026-01-10", "2026-01-03"]),
                "media_source": ["Meta", "Meta"],
                "campaign": ["C1", "C1"],
            }
        )
        events = pd.DataFrame(
            {
                "user_key": ["u1", "u2"],
                "event_time": pd.to_datetime(["2026-01-11", "2026-01-04"]),
                "event_name": ["af_purchase", "session"],
                "revenue": [10.0, 99.0],
            }
        )

        out = compare_liveops_impact(installs, events, "2026-01-10", "2026-01-10", baseline_days=1)
        self.assertAlmostEqual(float(out.loc[0, "liveops_d7_ltv"]), 10.0)
        self.assertAlmostEqual(float(out.loc[0, "baseline_d7_ltv"]), 0.0)

    def test_decision_engine_emits_reason(self):
        base = pd.DataFrame(
            {
                "media_source": ["Meta", "Google"],
                "campaign": ["C1", "C2"],
                "installs": [100, 300],
                "d7_roas": [0.8, 1.25],
            }
        )
        out = apply_decision_logic(base, target_roas=1.0, min_installs=200)
        self.assertIn("decision_reason", out.columns)
        self.assertEqual(out.loc[0, "decision"], "Hold (Low Sample)")
        self.assertEqual(out.loc[1, "decision"], "Scale Up")



if __name__ == "__main__":
    unittest.main()
