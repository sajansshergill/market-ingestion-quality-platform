CREATE SCHEMA IF NOT EXISTS ops;

-- one row per pipeline run
CREATE TABLE IF NOT EXISTS ops.pipeline_runs (
  run_id        TEXT PRIMARY KEY,
  pipeline_name TEXT NOT NULL,
  git_sha       TEXT NULL,
  started_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ended_at      TIMESTAMPTZ NULL,
  status        TEXT NOT NULL DEFAULT 'RUNNING',
  row_count     BIGINT NULL,
  dq_pass_rate  DOUBLE PRECISION NULL,
  notes         TEXT NULL
);

-- one row per data issue detected
CREATE TABLE IF NOT EXISTS ops.data_issues (
  issue_id     BIGSERIAL PRIMARY KEY,
  run_id       TEXT NULL,
  dataset      TEXT NOT NULL,
  rule_name    TEXT NOT NULL,
  severity     TEXT NOT NULL CHECK (severity IN ('LOW','MEDIUM','HIGH','CRITICAL')),
  observed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  details_json JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_data_issues_dataset_time
  ON ops.data_issues(dataset, observed_at DESC);