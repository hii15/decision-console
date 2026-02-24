import json
from dataclasses import dataclass

from config.channel_config import DEFAULT_CHANNEL_MAP
from config.target_config import DEFAULT_MULTIPLIER
from config.rule_config import DEFAULT_DECISION_RULES, DEFAULT_FALLBACK_DECISION


@dataclass
class RuntimeConfig:
    base_target: float | None
    channel_map: dict
    multiplier_map: dict
    decision_rules: list
    fallback_decision: str


def load_runtime_config(config_file) -> RuntimeConfig:
    """Load optional JSON config uploaded from Streamlit file_uploader."""
    if config_file is None:
        return RuntimeConfig(
            base_target=None,
            channel_map=DEFAULT_CHANNEL_MAP.copy(),
            multiplier_map=DEFAULT_MULTIPLIER.copy(),
            decision_rules=[r.copy() for r in DEFAULT_DECISION_RULES],
            fallback_decision=DEFAULT_FALLBACK_DECISION,
        )

    payload = json.load(config_file)
    if not isinstance(payload, dict):
        raise ValueError("runtime config must be a JSON object")

    base_target = payload.get("base_target")
    if base_target is not None:
        base_target = float(base_target)

    channel_map = DEFAULT_CHANNEL_MAP.copy()
    user_channel_map = payload.get("channel_map", {})
    if not isinstance(user_channel_map, dict):
        raise ValueError("channel_map must be an object")
    channel_map.update({str(k): str(v) for k, v in user_channel_map.items()})

    multiplier_map = DEFAULT_MULTIPLIER.copy()
    user_multiplier_map = payload.get("multiplier_map", {})
    if not isinstance(user_multiplier_map, dict):
        raise ValueError("multiplier_map must be an object")
    multiplier_map.update({str(k): float(v) for k, v in user_multiplier_map.items()})

    decision_rules = payload.get("decision_rules", DEFAULT_DECISION_RULES)
    if not isinstance(decision_rules, list):
        raise ValueError("decision_rules must be a list")

    normalized_rules = []
    for rule in decision_rules:
        if not isinstance(rule, dict):
            raise ValueError("each decision rule must be an object")
        normalized_rules.append(
            {
                "name": str(rule.get("name", "rule")),
                "op": str(rule.get("op", ">=")),
                "threshold": float(rule.get("threshold", 1.0)),
                "decision": str(rule.get("decision", "Test")),
                "conditions": rule.get("conditions", {}),
            }
        )

    fallback_decision = str(payload.get("fallback_decision", DEFAULT_FALLBACK_DECISION))

    return RuntimeConfig(
        base_target=base_target,
        channel_map=channel_map,
        multiplier_map=multiplier_map,
        decision_rules=normalized_rules,
        fallback_decision=fallback_decision,
    )
