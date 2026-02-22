-- bronze FRED observations (raw-ish, lightly typed)
CREATE TABLE IF NOT EXISTS bronze.fred_series_observations (
  series_id      TEXT NOT NULL,
  obs_date       DATE NOT NULL,
  obs_value      DOUBLE PRECISION NULL,
  realtime_start DATE NULL,
  realtime_end   DATE NULL,
  units          TEXT NULL,
  frequency      TEXT NULL,
  source         TEXT NOT NULL DEFAULT 'FRED',
  ingested_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT fred_series_observations_pk PRIMARY KEY (series_id, obs_date)
);

CREATE INDEX IF NOT EXISTS idx_fred_series_date
  ON bronze.fred_series_observations(series_id, obs_date);