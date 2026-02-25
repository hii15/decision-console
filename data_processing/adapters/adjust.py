from __future__ import annotations

import pandas as pd

from .base import BaseMMPAdapter


class AdjustAdapter(BaseMMPAdapter):
    def normalize_installs(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(
            columns={
                "adid": "user_key",
                "installed_at": "install_time",
                "network": "media_source",
                "adgroup": "adset",
                "country": "geo",
                "os_name": "platform",
            }
        ).copy()

    def normalize_events(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(
            columns={
                "adid": "user_key",
                "created_at": "event_time",
                "name": "event_name",
                "revenue_usd": "revenue",
            }
        ).copy()

    def normalize_cost(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns={"network": "media_source", "adgroup": "campaign", "cost": "spend"}).copy()
