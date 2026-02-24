"""Transform silver (cleaned) tables to gold (star schema marts)."""
from __future__ import annotations

from sqlalchemy import text

from src.utils.config import Settings
from src.warehouse.db import get_engine


def _ensure_sources(conn) -> None:
    """Ensure dim_source has required vendors."""
    for name, feed in [('FRED', 'daily'), ('FRED_VENDOR2', 'daily'), ('MOCK', 'daily'), ('WIKIPEDIA', 'daily')]:
        conn.execute(
            text("""
                INSERT INTO gold.dim_source (vendor_name, feed_type)
                VALUES (:name, :feed)
                ON CONFLICT (vendor_name) DO NOTHING
            """),
            {"name": name, "feed": feed},
        )


def run_macro(settings: Settings) -> int:
    """Silver macro -> gold.fact_macro."""
    engine = get_engine(settings)
    with engine.begin() as conn:
        _ensure_sources(conn)
        conn.execute(
            text("""
                INSERT INTO gold.fact_macro (series_id, obs_date, value, source_id, ingested_at)
                SELECT s.series_id, s.obs_date, s.obs_value, src.source_id, NOW()
                FROM silver.macro_series s
                JOIN gold.dim_source src ON src.vendor_name = s.source
                ON CONFLICT (series_id, obs_date, source_id) DO UPDATE SET
                    value = EXCLUDED.value, ingested_at = NOW()
            """)
        )
        count = conn.execute(text("SELECT COUNT(*) FROM gold.fact_macro")).scalar() or 0
    return int(count)


def run_prices(settings: Settings) -> int:
    """Silver OHLCV -> gold.fact_prices (with dim_symbol upsert)."""
    engine = get_engine(settings)
    with engine.begin() as conn:
        _ensure_sources(conn)
        conn.execute(
            text("""
                INSERT INTO gold.dim_symbol (ticker, exchange, asset_class, currency)
                SELECT DISTINCT o.symbol_id, 'NYSE', 'equity', 'USD'
                FROM silver.ohlcv o
                WHERE NOT EXISTS (SELECT 1 FROM gold.dim_symbol g WHERE g.ticker = o.symbol_id)
                ON CONFLICT (ticker) DO NOTHING
            """)
        )
        conn.execute(
            text("""
                INSERT INTO gold.fact_prices (symbol_id, ts, open, high, low, close, volume, source_id, ingested_at)
                SELECT sym.symbol_id, o.ts, o.open, o.high, o.low, o.close, o.volume, src.source_id, NOW()
                FROM silver.ohlcv o
                JOIN gold.dim_symbol sym ON sym.ticker = o.symbol_id
                JOIN gold.dim_source src ON src.vendor_name = o.source
                ON CONFLICT (symbol_id, ts, source_id) DO UPDATE SET
                    open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
                    close = EXCLUDED.close, volume = EXCLUDED.volume, ingested_at = NOW()
            """)
        )
        count = conn.execute(text("SELECT COUNT(*) FROM gold.fact_prices")).scalar() or 0
    return int(count)


def run_attention(settings: Settings) -> int:
    """Silver attention -> gold.fact_attention."""
    engine = get_engine(settings)
    with engine.begin() as conn:
        _ensure_sources(conn)
        conn.execute(
            text("""
                INSERT INTO gold.dim_symbol (ticker, exchange, asset_class, currency)
                SELECT DISTINCT a.symbol_id, 'NYSE', 'equity', 'USD'
                FROM silver.attention a
                WHERE NOT EXISTS (SELECT 1 FROM gold.dim_symbol g WHERE g.ticker = a.symbol_id)
                ON CONFLICT (ticker) DO NOTHING
            """)
        )
        conn.execute(
            text("""
                INSERT INTO gold.fact_attention (symbol_id, obs_date, attention_score, source_id, ingested_at)
                SELECT sym.symbol_id, a.obs_date, a.attention_score, src.source_id, NOW()
                FROM silver.attention a
                JOIN gold.dim_symbol sym ON sym.ticker = a.symbol_id
                JOIN gold.dim_source src ON src.vendor_name = a.source
                ON CONFLICT (symbol_id, obs_date, source_id) DO UPDATE SET
                    attention_score = EXCLUDED.attention_score, ingested_at = NOW()
            """)
        )
        count = conn.execute(text("SELECT COUNT(*) FROM gold.fact_attention")).scalar() or 0
    return int(count)


def main() -> None:
    settings = Settings()

    macro_rows = run_macro(settings)
    print(f"[silver_to_gold] fact_macro: {macro_rows} rows")

    try:
        prices_rows = run_prices(settings)
        print(f"[silver_to_gold] fact_prices: {prices_rows} rows")
    except Exception as e:
        print(f"[silver_to_gold] fact_prices: skipped ({e})")

    try:
        attn_rows = run_attention(settings)
        print(f"[silver_to_gold] fact_attention: {attn_rows} rows")
    except Exception as e:
        print(f"[silver_to_gold] fact_attention: skipped ({e})")


if __name__ == "__main__":
    main()
