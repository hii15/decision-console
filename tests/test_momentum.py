import unittest
import pandas as pd

from data_processing.momentum import compute_momentum_metrics


class MomentumTests(unittest.TestCase):
    def test_compute_momentum_metrics_ma3_and_dod(self):
        df = pd.DataFrame(
            {
                "install_date": pd.to_datetime([
                    "2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"
                ]),
                "level_key": ["facebook", "facebook", "facebook", "facebook"],
                "d7_roas": [1.0, 1.3, 0.7, 1.0],
            }
        )

        out = compute_momentum_metrics(df)
        self.assertAlmostEqual(out.loc[0, "roas_ma3"], 1.0)
        self.assertAlmostEqual(out.loc[2, "roas_ma3"], (1.0 + 1.3 + 0.7) / 3)
        self.assertAlmostEqual(out.loc[0, "roas_dod"], 0.0)
        self.assertAlmostEqual(out.loc[1, "roas_dod"], 0.3)


if __name__ == "__main__":
    unittest.main()
