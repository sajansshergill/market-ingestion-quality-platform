#!/usr/bin/env bash
# Run the full pipeline locally (no Airflow).
# Prereqs: Docker with postgres running, .env configured, pip install -r requirements.txt
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

export PYTHONPATH="$PROJECT_DIR"

echo "=== 1. Init DB (if needed) ==="
docker exec -i hedge_postgres psql -U postgres -d warehouse -c "SELECT 1 FROM bronze.fred_series_observations LIMIT 1" 2>/dev/null || {
  echo "Initializing database..."
  for f in sql/00_create_schemas.sql sql/01_bronze_tables.sql sql/02_ops_tables.sql sql/03_bronze_vendor2.sql sql/03_bronze_ohlcv.sql sql/03_bronze_attention.sql sql/04_silver_tables.sql sql/05_gold_star_schema.sql sql/06_indexes.sql; do
    [ -f "$f" ] && echo "  $f" && docker exec -i hedge_postgres psql -U postgres -d warehouse < "$f" 2>/dev/null || true
  done
}

echo ""
echo "=== 2. Ingest ==="
python -m src.ingest.vendor_fred
python -m src.ingest.vendor_fred_simulated
python -m src.ingest.vendor_ohlcv_mock
python -m src.ingest.vendor_attention_mock

echo ""
echo "=== 3. Transform ==="
python -m src.transform.bronze_to_silver
python -m src.transform.silver_to_gold

echo ""
echo "=== 4. Quality & Reconciliation ==="
python -m src.quality.run_checks
python -m src.quality.reconciliation

echo ""
echo "=== Full pipeline complete ==="
