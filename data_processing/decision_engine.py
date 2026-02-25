from __future__ import annotations

import pandas as pd


def apply_decision_logic(
    metrics_df: pd.DataFrame,
    target_roas: float,
    min_installs: int = 200,
    upper_buffer: float = 1.15,
    lower_buffer: float = 0.9,
) -> pd.DataFrame:
    out = metrics_df.copy()

    def _decide(row: pd.Series) -> str:
        if row["installs"] < min_installs:
            return "Hold (Low Sample)"
        if row["d7_roas"] > target_roas * upper_buffer:
            return "Scale Up"
        if row["d7_roas"] < target_roas * lower_buffer:
            return "Scale Down"
        return "Maintain"

    out["decision"] = out.apply(_decide, axis=1)
    return out
