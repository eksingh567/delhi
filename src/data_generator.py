from __future__ import annotations

from dataclasses import dataclass
import random

import numpy as np
import pandas as pd


class _FallbackIdentityGenerator:
    """Minimal fallback when Faker is unavailable in the runtime."""

    def __init__(self, rng: random.Random) -> None:
        self._rng = rng
        self._cities = [
            "Kyiv",
            "Warsaw",
            "Moscow",
            "Jerusalem",
            "Delhi",
            "Taipei",
            "Seoul",
            "Boston",
            "Lviv",
            "Krakow",
        ]

    def city(self) -> str:
        return self._rng.choice(self._cities)

    def phone_number(self) -> str:
        return f"+1-202-555-{self._rng.randint(1000, 9999)}"


@dataclass(frozen=True)
class CountryProfile:
    country: str
    center_lat: float
    center_lon: float


COUNTRY_PROFILES = [
    CountryProfile("Ukraine", 49.0, 31.0),
    CountryProfile("Poland", 52.0, 19.0),
    CountryProfile("Russia", 61.0, 105.0),
    CountryProfile("Israel", 31.5, 34.8),
    CountryProfile("India", 22.0, 79.0),
    CountryProfile("Taiwan", 23.7, 121.0),
    CountryProfile("South Korea", 36.2, 127.8),
    CountryProfile("United States", 39.8, -98.6),
]

EVENT_TYPES = ["Protest", "Riots", "Battles", "Violence against civilians"]


def generate_conflict_events(start: str = "2022-01-01", months: int = 30, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    start_date = pd.to_datetime(start)
    for m in range(months):
        current = start_date + pd.DateOffset(months=m)
        for profile in COUNTRY_PROFILES:
            event_count = int(max(0, rng.normal(25, 8)))
            for _ in range(event_count):
                event_type = rng.choice(EVENT_TYPES, p=[0.35, 0.2, 0.3, 0.15])
                fatalities = int(max(0, rng.poisson(1 if event_type == "Protest" else 4)))
                rows.append(
                    {
                        "country": profile.country,
                        "event_type": event_type,
                        "fatalities": fatalities,
                        "actors_involved": rng.choice(["State forces", "Armed group", "Civilians"]),
                        "date": current + pd.Timedelta(days=int(rng.integers(0, 28))),
                        "location": f"{profile.country}-zone-{int(rng.integers(1, 10))}",
                    }
                )
    return pd.DataFrame(rows)


def generate_news_signals(conflict_df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 1)
    monthly = (
        conflict_df.assign(month=conflict_df["date"].dt.to_period("M").dt.to_timestamp())
        .groupby(["country", "month"], as_index=False)
        .agg(protests=("event_type", lambda s: (s == "Protest").sum()), battles=("event_type", lambda s: (s == "Battles").sum()))
    )
    sentiment = 0.2 - 0.01 * monthly["protests"] - 0.03 * monthly["battles"] + rng.normal(0, 0.08, len(monthly))
    monthly["news_sentiment"] = sentiment.clip(-1, 1)
    monthly["sanctions"] = (monthly["battles"] > 6).astype(int)
    monthly["border_activity"] = (monthly["battles"] + rng.integers(0, 4, len(monthly))).astype(int)
    return monthly[["country", "month", "news_sentiment", "sanctions", "border_activity"]]


def generate_social_signals(news_df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 2)
    df = news_df[["country", "month"]].copy()
    df["terror_events"] = np.maximum(0, rng.poisson(1.2, len(df)) + (news_df["sanctions"] * 2))
    df["keyword_spike"] = np.maximum(0, (rng.normal(20, 5, len(df)) + news_df["border_activity"] * 2).astype(int))
    return df


def generate_student_data(size: int = 500, seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    fallback_rng = random.Random(seed)
    try:
        from faker import Faker

        fake = Faker()
        Faker.seed(seed)
    except ModuleNotFoundError:
        fake = _FallbackIdentityGenerator(fallback_rng)

    rows = []
    universities = {
        "Ukraine": ["Kharkiv National University", "Taras Shevchenko National University"],
        "Poland": ["Warsaw University", "Jagiellonian University"],
        "Russia": ["Moscow State University", "Saint Petersburg State University"],
        "Israel": ["Hebrew University", "Tel Aviv University"],
        "India": ["Delhi University", "IIT Bombay"],
        "Taiwan": ["National Taiwan University", "NCCU"],
        "South Korea": ["Seoul National University", "KAIST"],
        "United States": ["Harvard University", "Stanford University"],
    }

    for i in range(1, size + 1):
        profile = random.choice(COUNTRY_PROFILES)
        rows.append(
            {
                "student_id": i,
                "country": profile.country,
                "university": random.choice(universities[profile.country]),
                "city": fake.city(),
                "passport_country": random.choice([p.country for p in COUNTRY_PROFILES]),
                "contact": fake.phone_number(),
                "emergency_contact": fake.phone_number(),
                "lat": profile.center_lat + random.uniform(-1.0, 1.0),
                "lon": profile.center_lon + random.uniform(-1.0, 1.0),
            }
        )
    return pd.DataFrame(rows)
