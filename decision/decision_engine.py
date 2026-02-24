from config.target_config import DEFAULT_MULTIPLIER
from config.rule_config import DEFAULT_DECISION_RULES, DEFAULT_FALLBACK_DECISION


ENGINE_VERSION = "deterministic_v1.2"


def _match_conditions(row, conditions: dict | None) -> bool:
    if not conditions:
        return True
    for key, expected in conditions.items():
        actual = row.get(key)
        if isinstance(expected, list):
            if actual not in expected:
                return False
        else:
            if actual != expected:
                return False
    return True


def run_decision_engine(df, channel_map, base_target, multiplier_map=None, decision_rules=None, fallback_decision=None):
    """
    Deterministic decision engine
    - channel_type -> multiplier -> adjusted_target_roas
    - decision via rule table on roas ratio
    """
    out = df.copy()

    out["channel_type"] = out["media_source"].map(channel_map).fillna("Performance")
    effective_multiplier = multiplier_map if multiplier_map is not None else DEFAULT_MULTIPLIER
    out["multiplier"] = out["channel_type"].map(effective_multiplier).fillna(1.0)
    out["adjusted_target_roas"] = base_target * out["multiplier"]

    out["roas_gap"] = out["d7_roas"] - out["adjusted_target_roas"]

    rules = decision_rules if decision_rules is not None else DEFAULT_DECISION_RULES
    fallback = fallback_decision if fallback_decision is not None else DEFAULT_FALLBACK_DECISION

    def rule(row):
        ratio = row["d7_roas"] / row["adjusted_target_roas"] if row["adjusted_target_roas"] > 0 else 0.0
        for r in rules:
            threshold = float(r.get("threshold", 1.0))
            op = r.get("op", ">=")
            decision_label = r.get("decision", "Test")
            conditions = r.get("conditions")

            if not _match_conditions(row, conditions):
                continue

            if (op == ">=" and ratio >= threshold) or (op == ">" and ratio > threshold):
                return decision_label
        return fallback

    out["decision"] = out.apply(rule, axis=1)
    out["engine_version"] = ENGINE_VERSION

    return out
