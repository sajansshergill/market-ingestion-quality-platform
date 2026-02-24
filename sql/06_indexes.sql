-- Gold fact table indexes for analytics
CREATE INDEX IF NOT EXISTS idx_fact_macro_series_date
  ON gold.fact_macro(series_id, obs_date);

CREATE INDEX IF NOT EXISTS idx_fact_prices_symbol_ts
  ON gold.fact_prices(symbol_id, ts);

CREATE INDEX IF NOT EXISTS idx_fact_prices_ts
  ON gold.fact_prices(ts);

CREATE INDEX IF NOT EXISTS idx_fact_attention_symbol_date
  ON gold.fact_attention(symbol_id, obs_date);
