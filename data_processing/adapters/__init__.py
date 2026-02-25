from data_processing.adapters.base import BaseMMPAdapter
from data_processing.adapters.appsflyer import AppsflyerAdapter
from data_processing.adapters.adjust import AdjustAdapter
from data_processing.adapters.singular import SingularAdapter


_ADAPTERS: dict[str, type[BaseMMPAdapter]] = {
    "appsflyer": AppsflyerAdapter,
    "adjust": AdjustAdapter,
    "singular": SingularAdapter,
}


def get_adapter(mmp_source: str | None) -> BaseMMPAdapter:
    key = (mmp_source or "appsflyer").strip().lower()
    if key not in _ADAPTERS:
        raise ValueError(f"unsupported mmp_source: {mmp_source}. supported={list(_ADAPTERS)}")
    return _ADAPTERS[key]()
