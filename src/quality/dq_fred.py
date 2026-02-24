from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone, date
from typing import Any

from sqlalchemy import text

from src.utils.config import Settings
from src.warehouse.db import get_engine


DATASET = "bronze.fred_series_observations"


@dataclass(frozen=True)
class Issue:
    rule_name: str
    severity: str  # LOW/MEDIUM/HIGH/CRITICAL
    details: dict[str, Any]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def start_run(settings: Settings, pipeline_name: str) -> str:
    run_id = str(uuid.uuid4())
    engine = get_engine(settings)
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO ops.pipeline_runs(run_id, pipeline_name, status, started_at)
                VALUES (:run_id, :pipeline_name, 'RUNNING', NOW())
            """),
            {"run_id": run_id, "pipeline_name": pipeline_name},
        )
    return run_id


def end_run(settings: Settings, run_id: str, status: str, row_count: int | None, dq_pass_rate: float | None, notes: str | None = None) -> None:
    engine = get_engine(settings)
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE ops.pipeline_runs
                SET ended_at = NOW(),
                    status = :status,
                    row_count = :row_count,
                    dq_pass_rate = :dq_pass_rate,
                    notes = :notes
                WHERE run_id = :run_id
            """),
            {
                "run_id": run_id,
                "status": status,
                "row_count": row_count,
                "dq_pass_rate": dq_pass_rate,
                "notes": notes,
            },
        )


def log_issues(settings: Settings, run_id: str, issues: list[Issue]) -> None:
    if not issues:
        return
    engine = get_engine(settings)
    rows = [
        {
            "run_id": run_id,
            "dataset": DATASET,
            "rule_name": i.rule_name,
            "severity": i.severity,
            "details_json": json.dumps(i.details),
        }
        for i in issues
    ]
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO ops.data_issues(run_id, dataset, rule_name, severity, details_json)
                VALUES (:run_id, :dataset, :rule_name, :severity, CAST(:details_json AS JSONB))
            """),
            rows,
        )


def run_dq_checks(settings: Settings, freshness_days: int = 14) -> tuple[int, list[Issue]]:
    """
    Returns: (row_count, issues)
    """
    engine = get_engine(settings)
    issues: list[Issue] = []

    with engine.begin() as conn:
        # 1) Row count sanity
        row_count = conn.execute(text(f"SELECT COUNT(*) FROM {DATASET};")).scalar_one()
        if row_count == 0:
            issues.append(Issue(
                rule_name="row_count_nonzero",
                severity="CRITICAL",
                details={"row_count": row_count, "expected": ">= 1"},
            ))

        # 2) Null checks for PK fields
        null_pk = conn.execute(text(f"""
            SELECT
              SUM(CASE WHEN series_id IS NULL THEN 1 ELSE 0 END) AS null_series,
              SUM(CASE WHEN obs_date IS NULL THEN 1 ELSE 0 END) AS null_date
            FROM {DATASET};
        """)).mappings().one()
        if null_pk["null_series"] > 0 or null_pk["null_date"] > 0:
            issues.append(Issue(
                rule_name="pk_not_null",
                severity="CRITICAL",
                details=dict(null_pk),
            ))

        # 3) Duplicate PK check (should be impossible with PK, but useful if schema changes)
        dupes = conn.execute(text(f"""
            SELECT COUNT(*) AS dup_groups
            FROM (
              SELECT series_id, obs_date, COUNT(*) c
              FROM {DATASET}
              GROUP BY 1,2
              HAVING COUNT(*) > 1
            ) t;
        """)).scalar_one()
        if dupes > 0:
            issues.append(Issue(
                rule_name="pk_unique",
                severity="HIGH",
                details={"dup_groups": dupes},
            ))

                # 4) Series-aware sanity ranges (loose but meaningful)
        # FEDFUNDS: 0..25 is already very generous
        # UNRATE: 0..40 generous
        # CPIAUCSL: >0 and <1000 generous
        range_fail = conn.execute(text(f"""
            SELECT series_id, COUNT(*) AS bad_rows
            FROM {DATASET}
            WHERE obs_value IS NOT NULL AND (
                (series_id = 'FEDFUNDS' AND (obs_value < 0 OR obs_value > 25)) OR
                (series_id = 'UNRATE'   AND (obs_value < 0 OR obs_value > 40)) OR
                (series_id = 'CPIAUCSL' AND (obs_value <= 0 OR obs_value > 1000))
            )
            GROUP BY series_id
            ORDER BY series_id;
        """)).mappings().all()

        if range_fail:
            issues.append(Issue(
                rule_name="obs_value_series_ranges",
                severity="MEDIUM",
                details={"violations": [dict(r) for r in range_fail]},
            ))

                # 5) Freshness SLA: series-aware thresholds (monthly vs daily-ish)
        # These thresholds are intentionally generous to avoid false alarms.
        freshness_threshold_days = {
            "CPIAUCSL": 45,   # monthly; allow lag
            "UNRATE": 45,     # monthly; allow lag
            "FEDFUNDS": 10,   # should be more frequent, but allow some lag
        }

        freshness = conn.execute(text(f"""
            SELECT series_id, MAX(obs_date) AS max_date
            FROM {DATASET}
            GROUP BY series_id
            ORDER BY series_id;
        """)).mappings().all()

        today = date.today()
        stale = []
        for r in freshness:
            sid = r["series_id"]
            max_date = r["max_date"]
            threshold = freshness_threshold_days.get(sid, freshness_days)

            if max_date is None:
                stale.append({"series_id": sid, "max_date": None, "days_lag": None, "threshold_days": threshold})
                continue

            lag = (today - max_date).days
            if lag > threshold:
                stale.append({"series_id": sid, "max_date": str(max_date), "days_lag": lag, "threshold_days": threshold})

        if stale:
            issues.append(Issue(
                rule_name="freshness_sla_per_series",
                severity="HIGH",
                details={"stale": stale},
            ))
            
    return int(row_count), issues


def main() -> None:
    settings = Settings()

    run_id = start_run(settings, pipeline_name="dq_fred_bronze")
    try:
        row_count, issues = run_dq_checks(settings, freshness_days=14)
        log_issues(settings, run_id, issues)

        passed = len(issues) == 0
        dq_pass_rate = 1.0 if passed else 0.0  # simple for now; can refine to % rules passed

        end_run(
            settings,
            run_id=run_id,
            status="SUCCESS" if passed else "WARN",
            row_count=row_count,
            dq_pass_rate=dq_pass_rate,
            notes=None if passed else f"{len(issues)} issue(s) detected",
        )

        if passed:
            print(f"✅ DQ PASS — rows={row_count} run_id={run_id}")
        else:
            print(f"⚠️  DQ WARN — rows={row_count} issues={len(issues)} run_id={run_id}")
            for i in issues:
                print(f" - {i.severity}: {i.rule_name} :: {i.details}")

    except Exception as e:
        end_run(settings, run_id=run_id, status="FAILED", row_count=None, dq_pass_rate=None, notes=str(e))
        raise


if __name__ == "__main__":
    main()