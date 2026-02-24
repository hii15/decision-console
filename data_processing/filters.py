import pandas as pd


def apply_global_filters(
    installs_df: pd.DataFrame,
    events_df: pd.DataFrame,
    selected_sources: list[str] | None = None,
    selected_campaigns: list[str] | None = None,
    start_date=None,
    end_date=None,
):
    installs = installs_df.copy()
    events = events_df.copy()

    installs.columns = [str(c).strip() for c in installs.columns]
    events.columns = [str(c).strip() for c in events.columns]

    if selected_sources:
        installs = installs[installs["media_source"].astype(str).isin(selected_sources)].copy()

    if selected_campaigns:
        installs = installs[installs["campaign"].astype(str).isin(selected_campaigns)].copy()

    if start_date is not None and end_date is not None and "install_date" in installs.columns:
        d = pd.to_datetime(installs["install_date"], errors="coerce")
        installs = installs[(d >= pd.to_datetime(start_date)) & (d <= pd.to_datetime(end_date))].copy()

    if "appsflyer_id" in installs.columns and "appsflyer_id" in events.columns:
        valid_ids = set(installs["appsflyer_id"].dropna().astype(str))
        events = events[events["appsflyer_id"].astype(str).isin(valid_ids)].copy()

    return installs, events
