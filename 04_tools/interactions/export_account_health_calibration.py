"""Export P4 account_health.parquet for Jerome's threshold calibration pass (task 4.9).

Reads  : 01_data/17_interactions/account_health.parquet
Writes : 01_data/17_interactions/account_health_calibration.csv
         01_data/17_interactions/account_health_latest_flagged.csv

internal only — draft thresholds, not a KPI.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(os.environ.get("ISZE_ROOT", r"C:\Users\jerom\Desktop\claude\ISZE"))
IN_DIR = ROOT / "01_data" / "17_interactions"
SRC = IN_DIR / "account_health.parquet"
OUT_ALL = IN_DIR / "account_health_calibration.csv"
OUT_FLAGGED = IN_DIR / "account_health_latest_flagged.csv"

SIGNAL_COLS = [
    "response_latency_p50",
    "response_latency_p90",
    "n_replies",
    "commitment_met_rate",
    "n_commitments_scored",
    "signal_to_order_days",
    "signal_to_order_lift",
    "n_pn_mentions",
    "stakeholder_churn_pct",
    "n_stakeholder_pool",
    "escalation_cadence",
    "n_threads_30d",
    "topic_entropy",
    "activity_volume_per_day",
    "activity_drop_pct",
    "n_30d",
    "overdue_commitments",
]


def main() -> int:
    if not SRC.is_file():
        print(f"MISSING: {SRC}\nRun build_account_health.py first.", file=sys.stderr)
        return 1

    df = pd.read_parquet(SRC)
    cols = ["db_code", "year_month", "alert_level", "alert_reasons", "is_partial_month"] + SIGNAL_COLS
    cols = [c for c in cols if c in df.columns]
    meta_cols = [c for c in ("as_of", "thresholds_calibrated", "builder_version") if c in df.columns]
    export = df[cols + meta_cols].sort_values(["year_month", "db_code"])

    export.to_csv(OUT_ALL, index=False)
    latest = export["year_month"].max()
    snap = export[export["year_month"] == latest].copy()
    flagged = snap[snap["alert_level"].isin(["AMBER", "RED"])].sort_values(
        ["alert_level", "db_code"]
    )
    flagged.to_csv(OUT_FLAGGED, index=False)

    print(f"wrote {OUT_ALL} ({len(export):,} rows, {export['year_month'].nunique()} months)")
    print(f"latest={latest}  NONE={int((snap['alert_level']=='NONE').sum())}  "
          f"AMBER={int((snap['alert_level']=='AMBER').sum())}  "
          f"RED={int((snap['alert_level']=='RED').sum())}")
    print(f"flagged snapshot -> {OUT_FLAGGED} ({len(flagged)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
