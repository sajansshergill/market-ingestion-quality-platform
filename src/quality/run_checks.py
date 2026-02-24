"""Run all data quality checks. Entry point for CLI/Airflow."""
from __future__ import annotations

from src.quality.dq_fred import main as dq_fred_main


def main() -> None:
    dq_fred_main()
    # Extend with dq_ohlcv, dq_attention, etc. as needed


if __name__ == "__main__":
    main()
