"""Mock OHLCV vendor: generates sample daily bars for demo."""
from __future__ import annotations

import random
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import text

from src.utils.config import Settings
from src.warehouse.db import get_engine

SYMBOLS = ["AAPL", "MSFT", "GOOGL"]
SOURCE = "MOCK"


def main() -> None:
    settings = Settings()
    engine = get_engine(settings)

    start = date(2025, 1, 1)
    end = date(2026, 1, 1)
    inserts = []
    base_prices = {"AAPL": 185.0, "MSFT": 380.0, "GOOGL": 140.0}

    for symbol in SYMBOLS:
        base = base_prices[symbol]
        curr = date(2025, 1, 1)
        while curr <= end:
            ts = datetime.combine(curr, datetime.min.time(), tzinfo=timezone.utc)
            change = random.gauss(0, 0.02)
            o = base
            c = base * (1 + change)
            h = max(o, c) * (1 + random.uniform(0, 0.01))
            l = min(o, c) * (1 - random.uniform(0, 0.01))
            v = random.randint(10_000_000, 80_000_000)
            inserts.append({
                "symbol": symbol,
                "ts": ts,
                "open": round(o, 2),
                "high": round(h, 2),
                "low": round(l, 2),
                "close": round(c, 2),
                "volume": v,
            })
            base = c
            curr += timedelta(days=1)

    with engine.begin() as conn:
        for row in inserts:
            conn.execute(
                text("""
                    INSERT INTO bronze.ohlcv (symbol, ts, open, high, low, close, volume, source, ingested_at)
                    VALUES (:symbol, :ts, :open, :high, :low, :close, :volume, :source, NOW())
                    ON CONFLICT (symbol, ts, source)
                    DO UPDATE SET open=EXCLUDED.open, high=EXCLUDED.high, low=EXCLUDED.low,
                        close=EXCLUDED.close, volume=EXCLUDED.volume, ingested_at=NOW()
                """),
                {**row, "source": SOURCE},
            )

    print(f"✅ Inserted/Updated {len(inserts)} OHLCV rows into bronze.ohlcv")


if __name__ == "__main__":
    main()
