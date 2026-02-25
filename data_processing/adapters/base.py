from __future__ import annotations

from abc import ABC, abstractmethod
import pandas as pd


class BaseMMPAdapter(ABC):
    name: str = "base"

    @abstractmethod
    def normalize_installs(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def normalize_events(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    def normalize_cost_daily(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.copy()



def _first_existing(df: pd.DataFrame, candidates: list[str], default=None):
    for col in candidates:
        if col in df.columns:
            return df[col]
    if default is None:
        return pd.Series([None] * len(df), index=df.index)
    return pd.Series([default] * len(df), index=df.index)


def _to_bool(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(str).str.lower().isin(["1", "true", "t", "yes", "y"])
