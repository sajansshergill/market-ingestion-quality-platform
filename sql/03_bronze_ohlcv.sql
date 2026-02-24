-- Bronze: raw OHLCV / quote data (from market data vendor)
CREATE TABLE IF NOT EXISTS bronze.ohlcv (
  symbol      TEXT NOT NULL,
  ts          TIMESTAMPTZ NOT NULL,
  open        DOUBLE PRECISION NOT NULL,
  high        DOUBLE PRECISION NOT NULL,
  low         DOUBLE PRECISION NOT NULL,
  close       DOUBLE PRECISION NOT NULL,
  volume      BIGINT NOT NULL DEFAULT 0,
  source      TEXT NOT NULL DEFAULT 'MOCK',
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (symbol, ts, source)
);

CREATE INDEX IF NOT EXISTS idx_bronze_ohlcv_symbol_ts
  ON bronze.ohlcv(symbol, ts);
