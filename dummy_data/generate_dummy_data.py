from __future__ import annotations

import numpy as np
import pandas as pd


def generate_dummy_data(seed: int = 42):
    rng = np.random.default_rng(seed)
    media_profiles = {
        "Meta": {"cpi": 3.8, "purchase_rate": 0.12, "arppu": 18},
        "Google": {"cpi": 4.4, "purchase_rate": 0.15, "arppu": 20},
        "Unity": {"cpi": 2.7, "purchase_rate": 0.08, "arppu": 14},
        "TikTok": {"cpi": 2.9, "purchase_rate": 0.1, "arppu": 16},
    }

    start = pd.Timestamp("2026-01-01")
    days = 30
    installs_rows = []
    events_rows = []
    cost_rows = []

    uid = 1
    for day_offset in range(days):
        day = start + pd.Timedelta(days=day_offset)
        liveops_boost = 1.3 if pd.Timestamp("2026-01-15") <= day <= pd.Timestamp("2026-01-21") else 1.0

        for media, profile in media_profiles.items():
            daily_installs = int(rng.integers(80, 140))
            purchases = int(daily_installs * profile["purchase_rate"] * liveops_boost)
            revenue_total = purchases * profile["arppu"] * rng.uniform(0.9, 1.1)

            for _ in range(daily_installs):
                user_key = f"u{uid}"
                uid += 1
                installs_rows.append(
                    {
                        "user_key": user_key,
                        "install_time": day + pd.Timedelta(hours=int(rng.integers(0, 24))),
                        "media_source": media,
                        "campaign": f"{media}_C1",
                        "adset": f"{media}_A1",
                        "creative": f"{media}_CR1",
                        "geo": "US",
                        "platform": "iOS" if uid % 2 == 0 else "Android",
                    }
                )

            if purchases > 0:
                buyers = rng.choice([r["user_key"] for r in installs_rows[-daily_installs:]], size=purchases, replace=False)
                rev_per_purchase = revenue_total / purchases
                for b in buyers:
                    lag = int(rng.integers(0, 8))
                    events_rows.append(
                        {
                            "user_key": b,
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


if __name__ == "__main__":
    installs, events, cost = generate_dummy_data()
    installs.to_csv("dummy_data/installs_sample.csv", index=False)
    events.to_csv("dummy_data/events_sample.csv", index=False)
    cost.to_csv("dummy_data/cost_sample.csv", index=False)
    print("Dummy data generated in dummy_data/")
