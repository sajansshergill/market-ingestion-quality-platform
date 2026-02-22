# Market + Alternative Data Ingestion & Quality Platform

A mini "hedge fund-style" data engineering platform that ingests **daily + intraday + streaming** datasets, runs **data quality + reconciliation**, and serves **analytics-ready tables** with **monitoring dashboards.**

This project is designed to closelt match the responsibilities in a buy-side (hedge fund / multi-strategy) Data Engineering role:
- ETL/ELT pipelines (batch + near-real-time)
- Data validation, monitoring, reconciliation
- SQL modeling (star schema)
- Cloud-ready infrastructure (local-first via Docker)
- Strong enginering practices (tests, CI, tools)

---

## What This Builds
### Data Sources (sumulated "vendors")
- **Market data:** OHLCV / quotes (e.g., Alpha Vantage / IEX / mock vendor adapter)
- **Macro data:** FRED (rates, CPI, etc..)
- **Alternatuve data:** EDGAR metadata or Wikipedia pageviews (proxy for attention)

### Data Modes
- **Daily Batch** (EOD snapshots)
- **Intraday batch** (every 5-15 minutes)
- **Streaming** (Kafka topic for quote ticks; consumer lands raw events)

### Pipeline layers
- **Bronze (raw):** vendor payloads as-is
- **Silver (clean):** standardized schema, dedupe, type casting, time normalization
- **Gold (marts):** star schema tables for analytics and research

### Data quality + reconciliation
- Great Expectations (or Soda) checks:
  - completeness, uniqueness, valid ranges, schema drift, timeliness (freshness SLA)
- Cross-source reconciliation:
  - price divergence detection
  - missing bars / gaps
  - row-count anomalies

### Observability
- Metrics exported for:
  - pipeline success rate
  - data freshness lag
  - DQ pass/fail rates
- **Grafana dashboard** for operational monitoring (optional alerting)

---

## Tech Stack
- **Python** (modern practices + type hints)
- **SQL** + **PosgreSQL** (warehouse)
- **Orchestration**: **Airflow** (or Dagster; roadmap includes Dagster assets)
- **Streaming : Kafka**
- **Data Quality: Great Expectations**
- **Containers: Docker compose**
- **CI: Github Actions**
- **Monitoring: Prometheus + Grafana**

---

## Architecture (High Level)
1. Ingest from vendors -> land raw payloads (Bronze)
2. Transform + standardize -> Silver
3. Build marts + indices -> Gold
4. Run DQ suites and reconciliation checks
5. Emit metrics + store run metadata (lineage/versioning lite)
6. Visualize health via Grafana

---

## Repo Structure
<img width="358" height="1408" alt="image" src="https://github.com/user-attachments/assets/951de360-8ca6-4336-9dc1-d875e3d15c59" />

---

## Data Model (Gold / Star Schema)
**Dimensions**
- `dim_symbol(symbol_id, ticker, exchange, asset_class, currency)`
- `dim_source(source_id, vendor_name, feed_type)`

**Facts**
- `fact_prices(symbol_id, ts, open, high, low, close, volume, source_id)`
- `fact_macro(series_id, date, value, source_id)`
- `fact_attention(symbo_id, date, attention_score, source_id)` (alt-data-proxy)

**Ops / Metadata**
- `pipeline_runs(run_id, dag_id, task_id, git_sha, schema_hash, row_count, dq_pass_rate, started_at, ended_at)`
- `data_issues(issue_id, dataset, rule_name, severity, observed_at, details_json)`

# Quickstart (Local)
### 0) Prereqs
- Docker + Docker Compose
- Python 3.10+ (optional if you run everything inside containers)

### 1) Clone & configure
```bash
git clone <your-repo-url>
cd market-altdata-platform
cp .env.example .env

Add API keys as needed:
ALPHA_VANTAGE_API_KEY=...
FRED_API_KEY=...
```
2) Start services
docker compose up -d
Expected services (depending on your compose file):
- Postgres
- Kafka (+ Zookeeper or KRaft)
- Airflow webserver/scheduler
- Grafana (+ Prometheus)

3) Initialize Database
docker compose exec postgres psql -U postgres -d warehouse -f /sql/00_create_schemas.sql
docker compose exec postgres psql -U postgres -d warehouse -f /sql/01_bronze_tables.sql
docker compose exec postgres psql -U postgres -d warehouse -f /sql/02_silver_tables.sql
docker compose exec postgres psql -U postgres -d warehouse -f /sql/03_gold_star_schema.sql
docker compose exec postgres psql -U postgres -d warehouse -f /sql/04_indexes.sql

4) Run pipelines
Option A — Airflow:
- Open Airflow UI at http://localhost:8080
- Trigger DAGs in this order:
  1. daily_market_ingest
  2. intraday_quotes_ingest
  3. transform_to_silver
  4. build_gold_marts
  5. dq_and_reconciliation

Option B — CLI scripts (for dev):
python -m src.ingest.vendor_fred
python -m src.transform.bronze_to_silver
python -m src.transform.silver_to_gold
python -m src.quality.run_checks
python -m src.quality.reconciliation

5) Monitoring
- Grafana: http://localhost:3000
- Dashboard tracks:
  - pipeline success rate
  - ingestion lag (freshness SLA)
  - DQ failures over time
  - reconciliation divergence

## Data Quality Rules (Example)
This project enforces quality like a financial data platform:
**Prices**
- close > 0
- volume ≥ 0
- uniqueness on (symbol, ts, source)
- completeness for required columns
- timeliness SLA: last tick within X minutes (intraday)

**Macro**
- no missing dates for expected cadence
- stable schema (drift detection)

**Reconciliation**
- if Vendor A vs Vendor B close price diverges > threshold_bps, write to data_issues
- if bar gaps > expected frequency, flag missing intervals

## Engineering Practices
- Type hints + linting (ruff recommended)
- Unit + integration tests
- CI runs:
  - formatiing + lint
  - tests
  - basic DQ suite smoke test
- Documentation:
  - data dictionary
  - lineage notes
  - SLA definitions
- Security hygiene:
  - API keys only via .env / secrets
  - no secrets committed

## Contact
If you're reviewing this as a recruiter/hiring manager: this repo is intentionally modeled after a buy-side data engineering environment (market data vendors, alternative data, validation, reconciliation, observability).
sajansshergill@gmail.com
