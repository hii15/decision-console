import pandas as pd


def compute_momentum_metrics(daily_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute DoD(delta) and MA3 metrics from daily cohort ROAS data.

    Required columns:
      install_date, level_key, d7_roas

    Returns:
      input + roas_ma3, roas_dod
    """
    df = daily_df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    required = ["install_date", "level_key", "d7_roas"]
    for col in required:
        if col not in df.columns:
            raise KeyError(f"[momentum] missing column: {col}")

    df["install_date"] = pd.to_datetime(df["install_date"], errors="coerce")
    df = df[~df["install_date"].isna()].copy()

    df = df.sort_values(["level_key", "install_date"]).reset_index(drop=True)
    df["roas_ma3"] = (
        df.groupby("level_key")["d7_roas"]
        .rolling(3, min_periods=1)
        .mean()
        .reset_index(level=0, drop=True)
    )
    df["roas_dod"] = df.groupby("level_key")["d7_roas"].diff().fillna(0.0)
    return df
