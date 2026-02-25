import unittest
import pandas as pd

from data_processing.adapters import get_adapter
from data_processing.loader import preprocess_installs, preprocess_events


class MMPAdapterTests(unittest.TestCase):
    def test_get_adapter_supported(self):
        self.assertEqual(get_adapter("appsflyer").name, "appsflyer")
        self.assertEqual(get_adapter("adjust").name, "adjust")
        self.assertEqual(get_adapter("singular").name, "singular")

    def test_adjust_installs_normalize(self):
        df = pd.DataFrame(
            {
                "installed_at": ["2026-01-01 00:00:00"],
                "network": ["meta"],
                "tracker_name": ["campaign_a"],
                "adid": ["u1"],
                "country": ["KR"],
                "cost": [1.2],
            }
        )
        out = preprocess_installs(df, mmp_source="adjust")
        self.assertEqual(out.loc[0, "media_source"], "meta")
        self.assertEqual(out.loc[0, "campaign"], "campaign_a")
        self.assertEqual(out.loc[0, "appsflyer_id"], "u1")

    def test_singular_events_normalize(self):
        df = pd.DataFrame(
            {
                "event_time": ["2026-01-01 00:00:00"],
                "event": ["purchase"],
                "event_revenue": [3.5],
                "device_id": ["u2"],
            }
        )
        out = preprocess_events(df, mmp_source="singular")
        self.assertEqual(out.loc[0, "event_name"], "purchase")
        self.assertEqual(float(out.loc[0, "revenue"]), 3.5)
        self.assertEqual(out.loc[0, "appsflyer_id"], "u2")


if __name__ == "__main__":
    unittest.main()
