from __future__ import annotations

import pandas as pd

from .base import BaseMMPAdapter


class SingularAdapter(BaseMMPAdapter):
    def normalize_installs(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(
            columns={
                "device_id": "user_key",
                "install_time_utc": "install_time",
                "source": "media_source",
                "ad_group": "adset",
                "creative_name": "creative",
                "country_iso": "geo",
                "platform_name": "platform",
            }
        ).copy()

    def normalize_events(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(
            columns={
                "device_id": "user_key",
                "event_time_utc": "event_time",
                "event": "event_name",
                "revenue_amount": "revenue",
            }
        ).copy()

    def normalize_cost(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns={"source": "media_source", "ad_group": "campaign", "spend_usd": "spend"}).copy()
