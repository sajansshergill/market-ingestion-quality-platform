"""Mock attention/alt-data vendor: Wikipedia pageviews proxy."""
from __future__ import annotations

import random
from datetime import date, timedelta
from sqlalchemy import text

from src.utils.config import Settings
from src.warehouse.db import get_engine

SYMBOLS = ["AAPL", "MSFT", "GOOGL"]
SOURCE = "WIKIPEDIA"


def main() -> None:
    settings = Settings()
    engine = get_engine(settings)

    start = date(2025, 1, 1)
    end = date(2026, 1, 1)
    inserts = []

    curr = start
    while curr <= end:
        for symbol in SYMBOLS:
            raw = random.randint(50000, 500000) + random.random()
            inserts.append({
                "symbol": symbol,
                "obs_date": curr,
                "raw_count": raw,
                "source": SOURCE,
            })
        curr += timedelta(days=1)

    with engine.begin() as conn:
        for row in inserts:
            conn.execute(
                text("""
                    INSERT INTO bronze.attention (symbol, obs_date, raw_count, source, ingested_at)
                    VALUES (:symbol, :obs_date, :raw_count, :source, NOW())
                    ON CONFLICT (symbol, obs_date, source)
                    DO UPDATE SET raw_count=EXCLUDED.raw_count, ingested_at=NOW()
                """),
                row,
            )

    print(f"✅ Inserted/Updated {len(inserts)} attention rows into bronze.attention")


if __name__ == "__main__":
    main()
