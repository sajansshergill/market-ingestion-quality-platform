from __future__ import annotations

import random
from sqlalchemy import text

from src.utils.config import Settings
from src.warehouse.db import get_engine


def main() -> None:
    settings = Settings()
    engine = get_engine(settings)

    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT series_id, obs_date, obs_value
            FROM bronze.fred_series_observations
        """)).mappings().all()

        if not rows:
            print("No source data found in bronze.fred_series_observations. Run vendor_fred first.")
            return

        inserts = []
        for r in rows:
            v = r["obs_value"]

            # Simulate a second vendor:
            # - most rows identical
            # - ~10% rows get a small +/- 0.5% drift
            if v is not None and random.random() < 0.10:
                v = v * (1 + random.uniform(-0.005, 0.005))

            inserts.append({
                "series_id": r["series_id"],
                "obs_date": r["obs_date"],
                "obs_value": v,
            })

        conn.execute(
            text("""
                INSERT INTO bronze.fred_series_observations_vendor2
                  (series_id, obs_date, obs_value, source)
                VALUES
                  (:series_id, :obs_date, :obs_value, 'FRED_VENDOR2')
                ON CONFLICT (series_id, obs_date)
                DO UPDATE SET
                  obs_value = EXCLUDED.obs_value,
                  source = EXCLUDED.source,
                  ingested_at = NOW();
            """),
            inserts,
        )

    print(f"✅ Inserted/Updated {len(inserts)} rows into bronze.fred_series_observations_vendor2")


if __name__ == "__main__":
    main()