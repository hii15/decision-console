"""Decision rule table defaults for deterministic engine."""

DEFAULT_DECISION_RULES = [
    {"name": "scale", "op": ">=", "threshold": 1.0, "decision": "Scale"},
    {"name": "test", "op": ">=", "threshold": 0.8, "decision": "Test"},
]

DEFAULT_FALLBACK_DECISION = "Reduce"
