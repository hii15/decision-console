from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

INSTALL_COLUMNS = [
    "user_key",
    "install_time",
    "media_source",
    "campaign",
    "adset",
    "creative",
    "geo",
    "platform",
]

EVENT_COLUMNS = ["user_key", "event_time", "event_name", "revenue"]

COST_COLUMNS = ["date", "media_source", "campaign", "impressions", "clicks", "spend"]


@dataclass
class CanonicalDataBundle:
    installs: pd.DataFrame
    events: pd.DataFrame
    cost: pd.DataFrame


def _ensure_columns(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col not in out.columns:
            out[col] = pd.NA
    return out[cols]


def coerce_canonical_types(installs: pd.DataFrame, events: pd.DataFrame, cost: pd.DataFrame) -> CanonicalDataBundle:
    installs = _ensure_columns(installs, INSTALL_COLUMNS)
    events = _ensure_columns(events, EVENT_COLUMNS)
    cost = _ensure_columns(cost, COST_COLUMNS)

    installs["install_time"] = pd.to_datetime(installs["install_time"], errors="coerce")
    events["event_time"] = pd.to_datetime(events["event_time"], errors="coerce")
    cost["date"] = pd.to_datetime(cost["date"], errors="coerce").dt.date

    events["revenue"] = pd.to_numeric(events["revenue"], errors="coerce").fillna(0.0)
    cost["impressions"] = pd.to_numeric(cost["impressions"], errors="coerce").fillna(0)
    cost["clicks"] = pd.to_numeric(cost["clicks"], errors="coerce").fillna(0)
    cost["spend"] = pd.to_numeric(cost["spend"], errors="coerce").fillna(0.0)

    return CanonicalDataBundle(installs=installs, events=events, cost=cost)
