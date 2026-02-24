#!/usr/bin/env bash
# Initialize database schemas. Run from host: ./scripts/init_db.sh
# Or inside postgres container: psql -U postgres -d warehouse -f /path/to/sql/00_create_schemas.sql

set -e
POSTGRES_CMD="${POSTGRES_CMD:-docker exec -i hedge_postgres psql -U postgres -d warehouse}"
SQL_DIR="$(cd "$(dirname "$0")/../sql" && pwd)"

for f in 00_create_schemas 01_bronze_tables 02_ops_tables 03_bronze_vendor2 03_bronze_ohlcv 03_bronze_attention 04_silver_tables 05_gold_star_schema 06_indexes; do
  path="$SQL_DIR/${f}.sql"
  if [ -f "$path" ]; then
    echo "Running $f..."
    $POSTGRES_CMD < "$path" || true
  fi
done
echo "Database init complete."
