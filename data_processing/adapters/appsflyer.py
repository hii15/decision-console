from __future__ import annotations

import pandas as pd

from data_processing.adapters.base import BaseMMPAdapter, _first_existing, _to_bool
from data_processing.canonical_schema import validate_canonical_schema


class AppsflyerAdapter(BaseMMPAdapter):
    name = "appsflyer"

    def normalize_installs(self, df: pd.DataFrame) -> pd.DataFrame:
        src = df.copy()
        src.columns = [str(c).strip() for c in src.columns]

        out = pd.DataFrame(index=src.index)
        out["install_time"] = _first_existing(src, ["install_time_utc", "install_time", "install_date"])
        out["app_id"] = _first_existing(src, ["app_id", "app", "bundle_id"], default="unknown_app")
        out["geo"] = _first_existing(src, ["geo", "country", "country_code"], default="unknown")
        out["media_source"] = _first_existing(src, ["media_source", "network", "channel"], default="unknown")
        out["campaign"] = _first_existing(src, ["campaign", "campaign_name"], default="unknown")
        out["adset"] = _first_existing(src, ["adset", "adset_name", "adgroup", "ad_group"], default="unknown")
        out["creative"] = _first_existing(src, ["creative", "creative_name", "ad", "ad_name"], default="unknown")
        out["user_key"] = _first_existing(src, ["appsflyer_id", "user_id", "device_id"]) 
        out["is_reattributed"] = _to_bool(_first_existing(src, ["is_reattributed", "is_retargeting"], default=False))
        out["cost"] = pd.to_numeric(_first_existing(src, ["cost", "spend"], default=0.0), errors="coerce").fillna(0.0)

        validate_canonical_schema(out, "fact_installs")
        return out

    def normalize_events(self, df: pd.DataFrame) -> pd.DataFrame:
        src = df.copy()
        src.columns = [str(c).strip() for c in src.columns]

        out = pd.DataFrame(index=src.index)
        out["event_time"] = _first_existing(src, ["event_time_utc", "event_time", "event_date"])
        out["app_id"] = _first_existing(src, ["app_id", "app", "bundle_id"], default="unknown_app")
        out["geo"] = _first_existing(src, ["geo", "country", "country_code"], default="unknown")
        out["user_key"] = _first_existing(src, ["appsflyer_id", "user_id", "device_id"])
        out["event_name"] = _first_existing(src, ["event_name", "af_event_name"], default="unknown_event")
        out["event_value"] = _first_existing(src, ["event_value", "af_event_value"], default="")
        out["revenue"] = pd.to_numeric(_first_existing(src, ["af_revenue_usd", "event_revenue", "revenue"], default=0.0), errors="coerce").fillna(0.0)
        out["currency"] = _first_existing(src, ["currency", "af_currency"], default="USD")

        validate_canonical_schema(out, "fact_events")
        return out
