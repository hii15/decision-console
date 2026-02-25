from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd


MEDIA_PROFILES = {
    "Meta": {"cpi": 3.8, "purchase_rate": 0.12, "arppu": 18},
    "Google": {"cpi": 4.4, "purchase_rate": 0.15, "arppu": 20},
    "Unity": {"cpi": 2.7, "purchase_rate": 0.08, "arppu": 14},
    "TikTok": {"cpi": 2.9, "purchase_rate": 0.10, "arppu": 16},
}


def generate_canonical_dummy_data(seed: int = 42):
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2026-01-01")
    days = 30

    installs_rows, events_rows, cost_rows = [], [], []
    uid = 1

    for day_offset in range(days):
        day = start + pd.Timedelta(days=day_offset)
        liveops_boost = 1.3 if pd.Timestamp("2026-01-15") <= day <= pd.Timestamp("2026-01-21") else 1.0

        for media, profile in MEDIA_PROFILES.items():
            daily_installs = int(rng.integers(80, 140))
            purchases = int(daily_installs * profile["purchase_rate"] * liveops_boost)
            revenue_total = purchases * profile["arppu"] * rng.uniform(0.9, 1.1)

            install_user_keys = []
            for _ in range(daily_installs):
                user_key = f"u{uid}"
                uid += 1
                install_user_keys.append(user_key)
                installs_rows.append(
                    {
                        "user_key": user_key,
                        "install_time": day + pd.Timedelta(hours=int(rng.integers(0, 24))),
                        "media_source": media,
                        "campaign": f"{media}_C1",
                        "adset": f"{media}_A1",
                        "creative": f"{media}_CR1",
                        "geo": "KR",
                        "platform": "iOS" if uid % 2 == 0 else "Android",
                    }
                )

            if purchases > 0:
                buyers = rng.choice(install_user_keys, size=purchases, replace=False)
                rev_per_purchase = revenue_total / purchases
                for buyer in buyers:
                    lag = int(rng.integers(0, 8))
                    events_rows.append(
                        {
                            "user_key": buyer,
                            "event_time": day + pd.Timedelta(days=lag, hours=int(rng.integers(0, 24))),
                            "event_name": "af_purchase",
                            "revenue": round(float(rev_per_purchase * rng.uniform(0.8, 1.2)), 2),
                        }
                    )

            cost_rows.append(
                {
                    "date": day.date(),
                    "media_source": media,
                    "campaign": f"{media}_C1",
                    "impressions": int(daily_installs * rng.integers(25, 45)),
                    "clicks": int(daily_installs * rng.integers(4, 8)),
                    "spend": round(daily_installs * profile["cpi"] * rng.uniform(0.9, 1.1), 2),
                }
            )

    return pd.DataFrame(installs_rows), pd.DataFrame(events_rows), pd.DataFrame(cost_rows)


def to_appsflyer_raw(installs: pd.DataFrame, events: pd.DataFrame, cost: pd.DataFrame):
    installs_raw = installs.rename(
        columns={
            "user_key": "appsflyer_id",
            "install_time": "install_time_utc",
            "geo": "country_code",
        }
    )
    events_raw = events.rename(
        columns={
            "user_key": "appsflyer_id",
            "event_time": "event_time_utc",
            "revenue": "af_revenue_usd",
        }
    )
    cost_raw = cost.rename(columns={"spend": "cost", "campaign": "campaign_name"})
    return installs_raw, events_raw, cost_raw


def to_adjust_raw(installs: pd.DataFrame, events: pd.DataFrame, cost: pd.DataFrame):
    installs_raw = installs.rename(
        columns={
            "user_key": "adid",
            "install_time": "installed_at",
            "media_source": "network",
            "adset": "adgroup",
            "geo": "country",
            "platform": "os_name",
        }
    )
    events_raw = events.rename(
        columns={
            "user_key": "adid",
            "event_time": "created_at",
            "event_name": "name",
            "revenue": "revenue_usd",
        }
    )
    cost_raw = cost.rename(columns={"media_source": "network", "campaign": "adgroup", "spend": "cost"})
    return installs_raw, events_raw, cost_raw


def to_singular_raw(installs: pd.DataFrame, events: pd.DataFrame, cost: pd.DataFrame):
    installs_raw = installs.rename(
        columns={
            "user_key": "device_id",
            "install_time": "install_time_utc",
            "media_source": "source",
            "adset": "ad_group",
            "creative": "creative_name",
            "geo": "country_iso",
            "platform": "platform_name",
        }
    )
    events_raw = events.rename(
        columns={
            "user_key": "device_id",
            "event_time": "event_time_utc",
            "event_name": "event",
            "revenue": "revenue_amount",
        }
    )
    cost_raw = cost.rename(columns={"media_source": "source", "campaign": "ad_group", "spend": "spend_usd"})
    return installs_raw, events_raw, cost_raw


MMP_CONVERTERS = {
    "AppsFlyer": to_appsflyer_raw,
    "Adjust": to_adjust_raw,
    "Singular": to_singular_raw,
}


def get_mmp_raw_bundle(mmp: str, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if mmp not in MMP_CONVERTERS:
        raise ValueError(f"Unsupported MMP: {mmp}")
    installs, events, cost = generate_canonical_dummy_data(seed=seed)
    return MMP_CONVERTERS[mmp](installs, events, cost)


def write_mmp_dummy_data(output_dir: str = "dummy_data", seed: int = 42) -> dict[str, tuple[str, str, str]]:
    base = Path(output_dir)
    base.mkdir(parents=True, exist_ok=True)

    installs, events, cost = generate_canonical_dummy_data(seed=seed)

    written = {}
    for mmp, converter in MMP_CONVERTERS.items():
        slug = mmp.lower()
        mmp_dir = base / slug
        mmp_dir.mkdir(parents=True, exist_ok=True)

        i_raw, e_raw, c_raw = converter(installs, events, cost)

        i_path = mmp_dir / "installs_raw.csv"
        e_path = mmp_dir / "events_raw.csv"
        c_path = mmp_dir / "cost_raw.csv"

        i_raw.to_csv(i_path, index=False)
        e_raw.to_csv(e_path, index=False)
        c_raw.to_csv(c_path, index=False)
        written[slug] = (str(i_path), str(e_path), str(c_path))

    return written


if __name__ == "__main__":
    outputs = write_mmp_dummy_data(output_dir="dummy_data", seed=42)
    for mmp, paths in outputs.items():
        print(f"[{mmp}] installs={paths[0]} events={paths[1]} cost={paths[2]}")
