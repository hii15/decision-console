from config.target_config import DEFAULT_MULTIPLIER


def run_decision_engine(df, channel_map, base_target):
    """
    Deterministic decision engine v1
    - channel_type -> multiplier -> adjusted_target_roas
    - decision: Scale/Test/Reduce
    """
    out = df.copy()

    out["channel_type"] = out["media_source"].map(channel_map).fillna("Performance")
    out["multiplier"] = out["channel_type"].map(DEFAULT_MULTIPLIER).fillna(1.0)
    out["adjusted_target_roas"] = base_target * out["multiplier"]

    out["roas_gap"] = out["d7_roas"] - out["adjusted_target_roas"]

    def rule(row):
        if row["d7_roas"] >= row["adjusted_target_roas"]:
            return "Scale"
        elif row["d7_roas"] >= row["adjusted_target_roas"] * 0.8:
            return "Test"
        return "Reduce"

    out["decision"] = out.apply(rule, axis=1)

    return out