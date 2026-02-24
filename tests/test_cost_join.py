import unittest
import pandas as pd

from data_processing.cost_join import apply_cost_report


class CostJoinTests(unittest.TestCase):
    def setUp(self):
        self.installs = pd.DataFrame(
            {
                "appsflyer_id": ["u1", "u2"],
                "install_date": ["2026-01-01", "2026-01-01"],
                "media_source": ["facebook", "facebook"],
                "campaign": ["c1", "c1"],
                "cost": [1.0, 1.0],
            }
        )

    def test_apply_cost_report_by_id(self):
        report = pd.DataFrame({"appsflyer_id": ["u1"], "cost": [5.0]})
        out = apply_cost_report(self.installs, report)
        self.assertEqual(float(out.loc[out["appsflyer_id"] == "u1", "cost"].iloc[0]), 5.0)
        self.assertEqual(float(out.loc[out["appsflyer_id"] == "u2", "cost"].iloc[0]), 1.0)

    def test_apply_cost_report_by_group(self):
        report = pd.DataFrame(
            {
                "install_date": ["2026-01-01"],
                "media_source": ["facebook"],
                "campaign": ["c1"],
                "cost": [8.0],
            }
        )
        out = apply_cost_report(self.installs, report)
        self.assertEqual(float(out.loc[0, "cost"]), 4.0)
        self.assertEqual(float(out.loc[1, "cost"]), 4.0)


if __name__ == "__main__":
    unittest.main()
