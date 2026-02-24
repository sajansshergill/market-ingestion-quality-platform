"""Run reconciliation checks. Entry point for CLI/Airflow."""
from __future__ import annotations

from src.quality.reconcile_fred import main as reconcile_fred_main


def main() -> None:
    reconcile_fred_main()
    # Extend with price reconciliation, bar gap checks, etc. as needed


if __name__ == "__main__":
    main()
