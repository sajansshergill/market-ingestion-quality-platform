"""Full market + macro + alt-data pipeline. Runs in Docker or local Airflow."""
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import os

# Works in Docker (/opt/airflow/project) or override via env
PROJECT_DIR = os.environ.get("AIRFLOW_PROJECT_DIR", "/opt/airflow/project")
PYTHON_CMD = "python"

default_args = {
    "owner": "hedge_team",
    "start_date": datetime(2025, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

# Load .env if present (for FRED_API_KEY when running in Docker)
run_cmd = f"cd {PROJECT_DIR} && export PYTHONPATH={PROJECT_DIR} && (set -a && [ -f .env ] && . ./.env && set +a) ; {PYTHON_CMD} -m"

with DAG(
    dag_id="market_macro_pipeline",
    default_args=default_args,
    schedule="@daily",
    catchup=False,
    tags=["ingestion", "macro", "quality"],
) as dag:

    ingest_fred = BashOperator(
        task_id="ingest_fred",
        bash_command=f"{run_cmd} src.ingest.vendor_fred",
    )

    ingest_vendor2 = BashOperator(
        task_id="ingest_vendor2",
        bash_command=f"{run_cmd} src.ingest.vendor_fred_simulated",
    )

    ingest_ohlcv = BashOperator(
        task_id="ingest_ohlcv",
        bash_command=f"{run_cmd} src.ingest.vendor_ohlcv_mock",
    )

    ingest_attention = BashOperator(
        task_id="ingest_attention",
        bash_command=f"{run_cmd} src.ingest.vendor_attention_mock",
    )

    bronze_to_silver = BashOperator(
        task_id="bronze_to_silver",
        bash_command=f"{run_cmd} src.transform.bronze_to_silver",
    )

    silver_to_gold = BashOperator(
        task_id="silver_to_gold",
        bash_command=f"{run_cmd} src.transform.silver_to_gold",
    )

    run_dq = BashOperator(
        task_id="run_dq",
        bash_command=f"{run_cmd} src.quality.run_checks",
    )

    reconcile = BashOperator(
        task_id="reconcile",
        bash_command=f"{run_cmd} src.quality.reconciliation",
    )

    # Ingest: fred first (vendor2 simulates from fred), ohlcv/attention in parallel
    ingest_fred >> ingest_vendor2
    ingest_fred >> [ingest_ohlcv, ingest_attention]

    # Transforms depend on all bronze ingests
    [ingest_vendor2, ingest_ohlcv, ingest_attention] >> bronze_to_silver >> silver_to_gold

    # DQ and reconciliation
    silver_to_gold >> run_dq >> reconcile
