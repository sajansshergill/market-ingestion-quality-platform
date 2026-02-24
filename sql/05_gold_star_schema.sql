-- Gold: Star schema for analytics

-- Dimensions
CREATE TABLE IF NOT EXISTS gold.dim_symbol (
  symbol_id   SERIAL PRIMARY KEY,
  ticker      TEXT NOT NULL UNIQUE,
  exchange    TEXT NULL,
  asset_class TEXT NULL DEFAULT 'equity',
  currency    TEXT NULL DEFAULT 'USD'
);

CREATE TABLE IF NOT EXISTS gold.dim_source (
  source_id   SERIAL PRIMARY KEY,
  vendor_name TEXT NOT NULL UNIQUE,
  feed_type   TEXT NULL  -- 'daily' | 'intraday' | 'streaming'
);

-- Facts
CREATE TABLE IF NOT EXISTS gold.fact_macro (
  series_id   TEXT NOT NULL,
  obs_date    DATE NOT NULL,
  value       DOUBLE PRECISION NULL,
  source_id   INT NOT NULL REFERENCES gold.dim_source(source_id),
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (series_id, obs_date, source_id)
);

CREATE TABLE IF NOT EXISTS gold.fact_prices (
  symbol_id   INT NOT NULL REFERENCES gold.dim_symbol(symbol_id),
  ts         TIMESTAMPTZ NOT NULL,
  open       DOUBLE PRECISION NOT NULL,
  high       DOUBLE PRECISION NOT NULL,
  low        DOUBLE PRECISION NOT NULL,
  close      DOUBLE PRECISION NOT NULL,
  volume     BIGINT NOT NULL DEFAULT 0,
  source_id  INT NOT NULL REFERENCES gold.dim_source(source_id),
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (symbol_id, ts, source_id)
);

CREATE TABLE IF NOT EXISTS gold.fact_attention (
  symbol_id       INT NOT NULL REFERENCES gold.dim_symbol(symbol_id),
  obs_date        DATE NOT NULL,
  attention_score DOUBLE PRECISION NOT NULL,
  source_id       INT NOT NULL REFERENCES gold.dim_source(source_id),
  ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (symbol_id, obs_date, source_id)
);
