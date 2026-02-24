from config.target_config import DEFAULT_MULTIPLIER


ENGINE_VERSION = "deterministic_v1.1"


def run_decision_engine(df, channel_map, base_target, multiplier_map=None):
    """
    Deterministic decision engine v1
    - channel_type -> multiplier -> adjusted_target_roas
    - decision: Scale/Test/Reduce
    """
    out = df.copy()

    out["channel_type"] = out["media_source"].map(channel_map).fillna("Performance")
    effective_multiplier = multiplier_map if multiplier_map is not None else DEFAULT_MULTIPLIER
    out["multiplier"] = out["channel_type"].map(effective_multiplier).fillna(1.0)
    out["adjusted_target_roas"] = base_target * out["multiplier"]

    out["roas_gap"] = out["d7_roas"] - out["adjusted_target_roas"]

    def rule(row):
        if row["d7_roas"] >= row["adjusted_target_roas"]:
            return "Scale"
        elif row["d7_roas"] >= row["adjusted_target_roas"] * 0.8:
            return "Test"
        return "Reduce"

    out["decision"] = out.apply(rule, axis=1)
    out["engine_version"] = ENGINE_VERSION

    return out