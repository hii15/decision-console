import unittest
import pandas as pd

from data_processing.payback import compute_payback_days


class PaybackTests(unittest.TestCase):
    def test_payback_reached_and_not_reached(self):
        installs = pd.DataFrame(
            {
                "appsflyer_id": ["u1", "u2", "u3"],
                "media_source": ["facebook", "facebook", "googleadwords_int"],
                "campaign": ["c1", "c1", "c2"],
                "install_time": pd.to_datetime(["2026-01-01", "2026-01-01", "2026-01-01"]),
                "cost": [5.0, 5.0, 20.0],
            }
        )
        events = pd.DataFrame(
            {
                "appsflyer_id": ["u1", "u2", "u3"],
                "event_name": ["af_purchase", "af_purchase", "af_purchase"],
                "event_time": pd.to_datetime(["2026-01-01", "2026-01-03", "2026-01-02"]),
                "revenue": [6.0, 5.0, 3.0],
            }
        )

        out = compute_payback_days(installs, events, level="media_source", max_day=7)
        fb = out[out["level_key"] == "facebook"].iloc[0]
        gg = out[out["level_key"] == "googleadwords_int"].iloc[0]

        self.assertEqual(int(fb["payback_day"]), 2)
        self.assertTrue(pd.isna(gg["payback_day"]))


if __name__ == "__main__":
    unittest.main()
