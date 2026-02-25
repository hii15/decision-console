from __future__ import annotations

import pandas as pd

from data_processing.adapters.base import BaseMMPAdapter, _first_existing, _to_bool
from data_processing.canonical_schema import validate_canonical_schema


class AdjustAdapter(BaseMMPAdapter):
    name = "adjust"

    def normalize_installs(self, df: pd.DataFrame) -> pd.DataFrame:
        src = df.copy()
        src.columns = [str(c).strip() for c in src.columns]

        out = pd.DataFrame(index=src.index)
        out["install_time"] = _first_existing(src, ["installed_at", "install_time", "install_date"])
        out["app_id"] = _first_existing(src, ["app_id", "app_token", "bundle_id"], default="unknown_app")
        out["geo"] = _first_existing(src, ["country", "country_code", "geo"], default="unknown")
        out["media_source"] = _first_existing(src, ["network", "media_source", "partner_name"], default="unknown")
        out["campaign"] = _first_existing(src, ["campaign", "campaign_name", "tracker_name"], default="unknown")
        out["adset"] = _first_existing(src, ["adgroup", "adgroup_name", "adset"], default="unknown")
        out["creative"] = _first_existing(src, ["creative", "creative_name", "ad"], default="unknown")
        out["user_key"] = _first_existing(src, ["adid", "idfa", "gps_adid", "device_id", "user_id"])
        out["is_reattributed"] = _to_bool(_first_existing(src, ["is_reattributed", "reattributed"], default=False))
        out["cost"] = pd.to_numeric(_first_existing(src, ["cost", "spend"], default=0.0), errors="coerce").fillna(0.0)

        validate_canonical_schema(out, "fact_installs")
        return out

    def normalize_events(self, df: pd.DataFrame) -> pd.DataFrame:
        src = df.copy()
        src.columns = [str(c).strip() for c in src.columns]

        out = pd.DataFrame(index=src.index)
        out["event_time"] = _first_existing(src, ["created_at", "event_time", "event_date"])
        out["app_id"] = _first_existing(src, ["app_id", "app_token", "bundle_id"], default="unknown_app")
        out["geo"] = _first_existing(src, ["country", "country_code", "geo"], default="unknown")
        out["user_key"] = _first_existing(src, ["adid", "idfa", "gps_adid", "device_id", "user_id"])
        out["event_name"] = _first_existing(src, ["event_name", "activity_kind"], default="unknown_event")
        out["event_value"] = _first_existing(src, ["event_value", "event_properties"], default="")
        out["revenue"] = pd.to_numeric(_first_existing(src, ["revenue", "event_revenue"], default=0.0), errors="coerce").fillna(0.0)
        out["currency"] = _first_existing(src, ["currency"], default="USD")

        validate_canonical_schema(out, "fact_events")
        return out
