import pandas as pd


def apply_cost_report(installs_df: pd.DataFrame, cost_df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply external cost report into installs data.

    Supported schemas:
    1) appsflyer_id, cost
    2) install_date, media_source, campaign, cost

    Returns installs dataframe with updated `cost`.
    """
    installs = installs_df.copy()
    cost = cost_df.copy()

    installs.columns = [str(c).strip() for c in installs.columns]
    cost.columns = [str(c).strip() for c in cost.columns]

    if {"appsflyer_id", "cost"}.issubset(cost.columns):
        merge_cols = cost[["appsflyer_id", "cost"]].copy()
        merge_cols["cost"] = pd.to_numeric(merge_cols["cost"], errors="coerce")
        out = installs.merge(merge_cols, on="appsflyer_id", how="left", suffixes=("", "_report"))
        out["cost"] = out["cost_report"].fillna(out["cost"])
        return out.drop(columns=["cost_report"])

    required = {"install_date", "media_source", "campaign", "cost"}
    if required.issubset(cost.columns):
        out = installs.copy()
        out["install_date"] = pd.to_datetime(out["install_date"], errors="coerce").dt.date

        rep = cost[list(required)].copy()
        rep["install_date"] = pd.to_datetime(rep["install_date"], errors="coerce").dt.date
        rep["cost"] = pd.to_numeric(rep["cost"], errors="coerce").fillna(0.0)

        inst_count = (
            out.groupby(["install_date", "media_source", "campaign"], as_index=False)
            .agg(installs=("appsflyer_id", "count"))
        )

        rep = rep.merge(inst_count, on=["install_date", "media_source", "campaign"], how="left")
        rep["installs"] = rep["installs"].fillna(0)
        rep["unit_cost"] = rep.apply(
            lambda r: (r["cost"] / r["installs"]) if r["installs"] > 0 else None,
            axis=1,
        )

        out = out.merge(
            rep[["install_date", "media_source", "campaign", "unit_cost"]],
            on=["install_date", "media_source", "campaign"],
            how="left",
        )
        out["cost"] = out["unit_cost"].fillna(out["cost"])
        return out.drop(columns=["unit_cost"])

    raise ValueError(
        "Cost report must contain either [appsflyer_id, cost] or "
        "[install_date, media_source, campaign, cost]"
    )
