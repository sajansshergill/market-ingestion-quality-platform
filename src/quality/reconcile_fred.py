from __future__ import annotations

import json
import math
import uuid
from datetime import date, datetime

from sqlalchemy import text

from src.utils.config import Settings
from src.warehouse.db import get_engine


def _sanitize_for_json(obj: object) -> object:
    """Recursively sanitize values for JSON (NaN, Inf, date not natively serializable)."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_for_json(x) for x in obj]
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, (date, datetime)):
        return str(obj)
    return obj

DATASET = "bronze.fred_series_observations"
VENDOR2 = "bronze.fred_series_observations_vendor2"
THRESHOLD_BPS = 10 # 10 bps = 0.10%

def main() -> None:
    settings = Settings()
    engine = get_engine(settings)
    
    run_id = str(uuid.uuid4())
    
    with engine.begin() as conn:
        # Ensure vendor2 exists and has data
        v2_count = conn.execute(text(f"SELECT COUNT(*) FROM {VENDOR2};")).scalar()
        if v2_count == 0:
            print(f"Vendor2 table has 0 rows. Run: python -m src.ingest.vendor_fred_simulated")
            return
        
        divergences = conn.execute(
            text(f"""
            SELECT
                v1.series_id,
                v1.obs_date,
                v1.obs_value AS v1_value,
                v2.obs_value AS v2_value,
                (ABS(v1.obs_value - v2.obs_value) / NULLIF(ABS(v1.obs_value), 0) * 10000) AS divergence_bps
            FROM {DATASET} v1
                JOIN {VENDOR2} v2
                ON v1.series_id = v2.series_id
                AND v1.obs_date = v2.obs_date
                WHERE v1.obs_value IS NOT NULL
                AND v2.obs_value IS NOT NULL
                AND (ABS(v1.obs_value - v2.obs_value) / NULLIF(ABS(v1.obs_value), 0) * 10000) > :threshold_bps
            ORDER BY divergence_bps DESC
            LIMIT 500;
            """),
            {"threshold_bps": THRESHOLD_BPS},
        ).mappings().all()
        
        if not divergences:
            print(f"✅ No divergences found over {THRESHOLD_BPS} bps.")
            return

        rows = []
        for d in divergences:
            rows.append({
                "run_id": run_id,
                "dataset": DATASET,
                "rule_name": "cross_vendor_divergence_bps",
                "severity": "HIGH",
                "details_json": json.dumps(_sanitize_for_json(dict(d))),
            })
        
        conn.execute(
            text("""
                 INSERT INTO ops.data_issues(run_id, dataset, rule_name, severity, details_json)
                 VALUES (:run_id, :dataset, :rule_name, :severity, CAST(:details_json AS JSONB))
                 
            """),
            rows,
        )
    print(f"⚠️ Logged {len(divergences)} divergence issue(s) to ops.data_issues")
    print(f"run_id: {run_id}")
    
if __name__ == "__main__":
    main()