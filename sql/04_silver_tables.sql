-- Silver: cleaned, standardized macro series (from bronze FRED)
CREATE TABLE IF NOT EXISTS silver.macro_series (
  series_id      TEXT NOT NULL,
  obs_date       DATE NOT NULL,
  obs_value      DOUBLE PRECISION NULL,
  source         TEXT NOT NULL,
  ingested_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT silver_macro_series_pk PRIMARY KEY (series_id, obs_date)
);

CREATE INDEX IF NOT EXISTS idx_silver_macro_series_date
  ON silver.macro_series(series_id, obs_date);

-- Silver: cleaned OHLCV (from bronze market data)
CREATE TABLE IF NOT EXISTS silver.ohlcv (
  symbol_id      TEXT NOT NULL,
  ts             TIMESTAMPTZ NOT NULL,
  open           DOUBLE PRECISION NOT NULL,
  high           DOUBLE PRECISION NOT NULL,
  low            DOUBLE PRECISION NOT NULL,
  close          DOUBLE PRECISION NOT NULL,
  volume         BIGINT NOT NULL DEFAULT 0,
  source         TEXT NOT NULL,
  ingested_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT silver_ohlcv_pk PRIMARY KEY (symbol_id, ts, source)
);

CREATE INDEX IF NOT EXISTS idx_silver_ohlcv_ts
  ON silver.ohlcv(symbol_id, ts);

-- Silver: attention scores (from bronze alt-data)
CREATE TABLE IF NOT EXISTS silver.attention (
  symbol_id      TEXT NOT NULL,
  obs_date       DATE NOT NULL,
  attention_score DOUBLE PRECISION NOT NULL,
  source         TEXT NOT NULL,
  ingested_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT silver_attention_pk PRIMARY KEY (symbol_id, obs_date, source)
);
