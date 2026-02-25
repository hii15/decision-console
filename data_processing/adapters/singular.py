from __future__ import annotations

import pandas as pd

from data_processing.adapters.base import BaseMMPAdapter, _first_existing, _to_bool
from data_processing.canonical_schema import validate_canonical_schema


class SingularAdapter(BaseMMPAdapter):
    name = "singular"

    def normalize_installs(self, df: pd.DataFrame) -> pd.DataFrame:
        src = df.copy()
        src.columns = [str(c).strip() for c in src.columns]

        out = pd.DataFrame(index=src.index)
        out["install_time"] = _first_existing(src, ["install_time", "install_date", "date"])
        out["app_id"] = _first_existing(src, ["app_id", "app", "app_name"], default="unknown_app")
        out["geo"] = _first_existing(src, ["country", "geo", "country_code"], default="unknown")
        out["media_source"] = _first_existing(src, ["source", "media_source", "network"], default="unknown")
        out["campaign"] = _first_existing(src, ["campaign_name", "campaign"], default="unknown")
        out["adset"] = _first_existing(src, ["sub_campaign_name", "adset", "ad_group"], default="unknown")
        out["creative"] = _first_existing(src, ["creative_name", "creative", "ad_name"], default="unknown")
        out["user_key"] = _first_existing(src, ["device_id", "user_id", "idfa", "gaid"])
        out["is_reattributed"] = _to_bool(_first_existing(src, ["is_reattributed", "is_reengaged"], default=False))
        out["cost"] = pd.to_numeric(_first_existing(src, ["spend", "cost"], default=0.0), errors="coerce").fillna(0.0)

        validate_canonical_schema(out, "fact_installs")
        return out

    def normalize_events(self, df: pd.DataFrame) -> pd.DataFrame:
        src = df.copy()
        src.columns = [str(c).strip() for c in src.columns]

        out = pd.DataFrame(index=src.index)
        out["event_time"] = _first_existing(src, ["event_time", "event_date", "date"])
        out["app_id"] = _first_existing(src, ["app_id", "app", "app_name"], default="unknown_app")
        out["geo"] = _first_existing(src, ["country", "geo", "country_code"], default="unknown")
        out["user_key"] = _first_existing(src, ["device_id", "user_id", "idfa", "gaid"])
        out["event_name"] = _first_existing(src, ["event_name", "event"], default="unknown_event")
        out["event_value"] = _first_existing(src, ["event_value", "event_payload"], default="")
        out["revenue"] = pd.to_numeric(_first_existing(src, ["revenue", "event_revenue"], default=0.0), errors="coerce").fillna(0.0)
        out["currency"] = _first_existing(src, ["currency"], default="USD")

        validate_canonical_schema(out, "fact_events")
        return out
