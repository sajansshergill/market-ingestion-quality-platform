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
```bash
docker compose up -d postgres
# Or with Airflow: docker compose up -d  (requires FRED_API_KEY in env or .env)
```

Expected: Postgres on port 5440 (avoids conflict with local Postgres).
- Postgres
- Kafka (+ Zookeeper or KRaft)
- Airflow webserver/scheduler
- Grafana (+ Prometheus)

3) Initialize Database
```bash
# Run all SQL migrations (or use scripts/init_db.sh)
docker exec -i hedge_postgres psql -U postgres -d warehouse < sql/00_create_schemas.sql
docker exec -i hedge_postgres psql -U postgres -d warehouse < sql/01_bronze_tables.sql
docker exec -i hedge_postgres psql -U postgres -d warehouse < sql/02_ops_tables.sql
docker exec -i hedge_postgres psql -U postgres -d warehouse < sql/03_bronze_vendor2.sql
docker exec -i hedge_postgres psql -U postgres -d warehouse < sql/03_bronze_ohlcv.sql
docker exec -i hedge_postgres psql -U postgres -d warehouse < sql/03_bronze_attention.sql
docker exec -i hedge_postgres psql -U postgres -d warehouse < sql/04_silver_tables.sql
docker exec -i hedge_postgres psql -U postgres -d warehouse < sql/05_gold_star_schema.sql
docker exec -i hedge_postgres psql -U postgres -d warehouse < sql/06_indexes.sql
```

Set `PGPORT=5440` in `.env` (Postgres binds to 5440 to avoid conflicts with local Postgres).

4) Run pipelines

**Option A — One-command (recommended):**
```bash
pip install -r requirements.txt
./scripts/run_full_pipeline.sh
```
Runs init DB (if needed), ingest, transform, DQ, reconciliation.

**Option B — Airflow:**
```bash
docker compose --env-file .env up -d   # Pass FRED_API_KEY to Airflow
```
- Open Airflow UI at http://localhost:8080 (login: admin/admin)
- Trigger DAG `market_macro_pipeline` (ingest → transform → DQ → reconcile)

**Option C — CLI scripts (step by step):**
```bash
python -m src.ingest.vendor_fred           # Macro (FRED)
python -m src.ingest.vendor_fred_simulated # Simulated vendor2
python -m src.ingest.vendor_ohlcv_mock     # Mock OHLCV
python -m src.ingest.vendor_attention_mock # Mock attention
python -m src.transform.bronze_to_silver
python -m src.transform.silver_to_gold
python -m src.quality.run_checks
python -m src.quality.reconciliation
```

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
