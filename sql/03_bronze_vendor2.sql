CREATE TABLE IF NOT EXISTS bronze.fred_series_observations_vendor2 (
    series_id TEXT NOT NULL,
    obs_date DATE NOT NULL,
    obs_value DOUBLE PRECISION NULL,
    source TEXT NOT NULL DEFAULT 'FRED_VENDOR2',
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (series_id, obs_date)
);

CREATE INDEX IF NOT EXISTS idx_fred_series_date_vendor2
    ON bronze.fred_series_observations_vendor2(series_id, obs_date);