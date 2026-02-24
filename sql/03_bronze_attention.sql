-- Bronze: raw attention / alternative data (e.g. pageviews proxy)
CREATE TABLE IF NOT EXISTS bronze.attention (
  symbol      TEXT NOT NULL,
  obs_date    DATE NOT NULL,
  raw_count   DOUBLE PRECISION NOT NULL,
  source      TEXT NOT NULL DEFAULT 'WIKIPEDIA',
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (symbol, obs_date, source)
);

CREATE INDEX IF NOT EXISTS idx_bronze_attention_symbol_date
  ON bronze.attention(symbol, obs_date);
