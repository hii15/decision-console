import unittest
import pandas as pd

from data_processing.filters import apply_global_filters


class FilterTests(unittest.TestCase):
    def test_apply_global_filters_source_campaign_date(self):
        installs = pd.DataFrame(
            {
                "appsflyer_id": ["u1", "u2", "u3"],
                "install_date": ["2026-01-01", "2026-01-02", "2026-01-03"],
                "media_source": ["facebook", "googleadwords_int", "facebook"],
                "campaign": ["c1", "c2", "c3"],
            }
        )
        events = pd.DataFrame(
            {
                "appsflyer_id": ["u1", "u2", "u3", "uX"],
                "event_name": ["af_purchase", "af_purchase", "af_purchase", "af_purchase"],
            }
        )

        fi, fe = apply_global_filters(
            installs,
            events,
            selected_sources=["facebook"],
            selected_campaigns=["c3"],
            start_date="2026-01-02",
            end_date="2026-01-03",
        )

        self.assertEqual(len(fi), 1)
        self.assertEqual(fi.iloc[0]["appsflyer_id"], "u3")
        self.assertEqual(len(fe), 1)
        self.assertEqual(fe.iloc[0]["appsflyer_id"], "u3")


if __name__ == "__main__":
    unittest.main()
