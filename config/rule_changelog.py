"""Rule engine version changelog for reproducibility and governance."""

RULE_CHANGELOG = {
    "deterministic_v1.0": {
        "date": "2026-01-01",
        "summary": "기본 deterministic 규칙(Scale/Test/Reduce) 도입",
        "rules": [
            "ratio >= 1.0 -> Scale",
            "ratio >= 0.8 -> Test",
            "else -> Reduce",
        ],
    },
    "deterministic_v1.1": {
        "date": "2026-02-10",
        "summary": "engine_version 컬럼/표시 추가, multiplier runtime 주입",
        "rules": [
            "v1.0 규칙 유지",
            "multiplier_map runtime override 지원",
        ],
    },
    "deterministic_v1.2": {
        "date": "2026-02-24",
        "summary": "rule-table + 조건부 rule(conditions) + KST 기준 운영",
        "rules": [
            "decision_rules 테이블 평가",
            "conditions(country/app/os 등) 매칭 지원",
            "fallback_decision 설정 지원",
        ],
    },
}
