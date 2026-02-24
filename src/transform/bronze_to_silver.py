"""Transform bronze (raw) tables to silver (cleaned, standardized)."""
from __future__ import annotations

from sqlalchemy import text

from src.utils.config import Settings
from src.warehouse.db import get_engine


def run_macro(settings: Settings) -> int:
    """Bronze FRED -> silver.macro_series (dedupe, standardize)."""
    engine = get_engine(settings)
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO silver.macro_series (series_id, obs_date, obs_value, source, ingested_at)
                SELECT series_id, obs_date, obs_value, source, NOW()
                FROM bronze.fred_series_observations
                ON CONFLICT (series_id, obs_date)
                DO UPDATE SET
                    obs_value = EXCLUDED.obs_value,
                    source = EXCLUDED.source,
                    ingested_at = NOW()
            """)
        )
        count = conn.execute(text("SELECT COUNT(*) FROM silver.macro_series")).scalar() or 0
    return int(count)


def run_ohlcv(settings: Settings) -> int:
    """Bronze OHLCV -> silver.ohlcv (validate, standardize)."""
    engine = get_engine(settings)
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO silver.ohlcv (symbol_id, ts, open, high, low, close, volume, source, ingested_at)
                SELECT symbol AS symbol_id, ts, open, high, low, close, volume, source, NOW()
                FROM bronze.ohlcv
                WHERE close > 0 AND volume >= 0
                ON CONFLICT (symbol_id, ts, source)
                DO UPDATE SET
                    open = EXCLUDED.open, high = EXCLUDED.high,
                    low = EXCLUDED.low, close = EXCLUDED.close,
                    volume = EXCLUDED.volume, ingested_at = NOW()
            """)
        )
        count = conn.execute(text("SELECT COUNT(*) FROM silver.ohlcv")).scalar() or 0
    return int(count)


def run_attention(settings: Settings) -> int:
    """Bronze attention -> silver.attention (normalize score)."""
    engine = get_engine(settings)
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO silver.attention (symbol_id, obs_date, attention_score, source, ingested_at)
                SELECT symbol, obs_date, raw_count, source, NOW()
                FROM bronze.attention
                WHERE raw_count >= 0
                ON CONFLICT (symbol_id, obs_date, source)
                DO UPDATE SET
                    attention_score = EXCLUDED.attention_score,
                    ingested_at = NOW()
            """)
        )
        count = conn.execute(text("SELECT COUNT(*) FROM silver.attention")).scalar() or 0
    return int(count)


def main() -> None:
    settings = Settings()

    macro_rows = run_macro(settings)
    print(f"[bronze_to_silver] macro_series: {macro_rows} rows")

    try:
        ohlcv_rows = run_ohlcv(settings)
        print(f"[bronze_to_silver] ohlcv: {ohlcv_rows} rows")
    except Exception as e:
        print(f"[bronze_to_silver] ohlcv: skipped ({e})")

    try:
        attn_rows = run_attention(settings)
        print(f"[bronze_to_silver] attention: {attn_rows} rows")
    except Exception as e:
        print(f"[bronze_to_silver] attention: skipped ({e})")


if __name__ == "__main__":
    main()
