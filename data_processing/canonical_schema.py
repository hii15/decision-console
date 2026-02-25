from __future__ import annotations

import pandas as pd

CANONICAL_SCHEMAS: dict[str, dict[str, list[str]]] = {
    "fact_cost_daily": {
        "required": [
            "date",
            "app_id",
            "geo",
            "media_source",
            "campaign",
            "adset",
            "creative",
            "impressions",
            "clicks",
            "spend",
        ],
        "optional": [],
    },
    "fact_installs": {
        "required": [
            "install_time",
            "app_id",
            "geo",
            "media_source",
            "campaign",
            "adset",
            "creative",
            "user_key",
            "is_reattributed",
        ],
        "optional": ["cost"],
    },
    "fact_events": {
        "required": [
            "event_time",
            "app_id",
            "geo",
            "user_key",
            "event_name",
            "event_value",
            "revenue",
            "currency",
        ],
        "optional": [],
    },
}


def validate_canonical_schema(df: pd.DataFrame, table_name: str) -> None:
    if table_name not in CANONICAL_SCHEMAS:
        raise ValueError(f"unknown canonical table: {table_name}")

    required = CANONICAL_SCHEMAS[table_name]["required"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{table_name} missing required columns: {missing}")
