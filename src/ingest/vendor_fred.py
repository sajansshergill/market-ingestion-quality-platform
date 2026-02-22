from __future__ import annotations

import math
import requests
import pandas as pd
from sqlalchemy import text
from src.utils.config import Settings
from src.warehouse.db import get_engine

FRED_API = "https://api.stlouisfed.org/fred/series/observations"

def fetch_fred_series(series_id: str, api_key: str, start_date: str = "2025-01-01") -> pd.DataFrame:
    
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start_date,
    }
    r = requests.get(FRED_API, params=params, timeout=30)
    r.raise_for_status()
    payload = r.json()
    
    obs = payload.get("observations", [])
    if not obs:
        return pd.DataFrame()
    
    df = pd.DataFrame(obs)
    
    # Normalize types
    df["series_id"] = series_id
    df["obs_date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    
    # FRED uses "." for missing values
    def parse_value(v: str) -> float | None:
        try:
            if v is None:
                return None
            if isinstance(v, str) and v.strip() == ".":
                return None
            x = float(v)
            return None if math.isinf(x) else x
        except Exception:
            return None
    
    df["obs_value"] = df["value"].apply(parse_value)
    
    # optional metadata (often present)
    if "realtime_start" in df.columns:
        df["realtime_start"] = pd.to_datetime(df["realtime_start"], errors="coerce").dt.date
    else:
        df["realtime_start"] = None
        
    if "realtime_end" in df.columns:
        df["realtime_end"] = pd.to_datetime(df["realtime_end"], errors="coerce").dt.date
    else:
        df["realtime_end"] = None
    
    # keep only target columns
    out = df[["series_id", "obs_date", "obs_value", "realtime_start", "realtime_end"]].copy()
    out["source"] = "FRED"
    return out

def upsert_fred_observations(settings: Settings, df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    
    engine = get_engine(settings)
    
    # Use a single INSERT ... ON CONFLICT for performance
    sql = text("""
            INSERT INTO bronze.fred_series_observations
            (series_id, obs_date, obs_value, realtime_start, realtime_end, source)
            VALUES
            (:series_id, :obs_date, :obs_value, :realtime_start, :realtime_end, :source)
            ON CONFLICT (series_id, obs_date)
            DO UPDATE SET
                obs_value = EXCLUDED.obs_value,
                realtime_start = EXCLUDED.realtime_start,
                realtime_end = EXCLUDED.realtime_end,
                source = EXCLUDED.source,
                ingested_at = NOW();
    """)
    
    rows = df.to_dict(orient="records")
    with engine.begin() as conn:
        conn.execute(sql, rows)
        
    return len(rows)

def main() -> None:
    settings = Settings()
    if not settings.fred_api_key:
        raise RuntimeError("Missing FRED_API_KEY. Put it in your .env (copy from .env.example).")

    # Pick 2-3 well-known macro series 
    series_list = [
        "FEDFUNDS", #Effective Federal Funds Rate
        "CPIAUCSL", # CPI (All Urban Consumers)
        "UNRATE", # Unemployment Rate
    ]
    
    total = 0
    for sid in series_list:
        df = fetch_fred_series(series_id=sid, api_key=settings.fred_api_key, start_date="2025-01-01")
        inserted = upsert_fred_observations(settings, df)
        print(f"[FRED] series={sid} rows={inserted}")
        total += inserted
        
    print(f"\n[FRED] Total rows ingested: {total}")

if __name__ == "__main__":
    main()