#!/usr/bin/env python3
"""Account-health ops pack — triage table (internal).

Runs build_account_health + export_account_health_calibration if needed.
Writes triage markdown + CSV under 01_data/17_interactions/.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(__file__).resolve().parents[2]
INTER = ISZE / "01_data" / "17_interactions"
TOOLS = ISZE / "04_tools" / "interactions"
SRC = INTER / "account_health.parquet"
OUT_CSV = INTER / "account_health_ops_triage.csv"
OUT_MD = INTER / "ACCOUNT_HEALTH_OPS_TRIAGE_20260819.md"
OUT_META = INTER / "account_health_ops_pack.meta.json"


def _run(script: Path) -> None:
    r = subprocess.run([sys.executable, str(script)], cwd=str(ISZE), capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr or r.stdout, file=sys.stderr)
        raise RuntimeError(f"{script.name} failed")


def main() -> int:
    if not SRC.is_file():
        _run(TOOLS / "build_account_health.py")
    cal = INTER / "account_health_calibration.csv"
    if not cal.is_file():
        _run(TOOLS / "export_account_health_calibration.py")

    df = pd.read_parquet(SRC)
    latest = df["year_month"].max()
    snap = df[df["year_month"] == latest].copy()
    triage = snap[snap["alert_level"].isin(["AMBER", "RED"])].sort_values(
        ["alert_level", "db_code"], ascending=[True, True]
    )

    cols = [
        "db_code",
        "year_month",
        "alert_level",
        "alert_reasons",
        "response_latency_p50",
        "commitment_met_rate",
        "signal_to_order_lift",
        "overdue_commitments",
        "activity_drop_pct",
    ]
    cols = [c for c in cols if c in triage.columns]
    triage[cols].to_csv(OUT_CSV, index=False)

    lines = [
        "# Account health ops triage (internal · draft thresholds · 2026-08-19)",
        "",
        f"Latest month: **{latest}** · flagged: **{len(triage)}** distributors",
        "",
        "Uncalibrated thresholds per `00_docs/P4_DETERMINISTIC_SIGNALS.md`. Jerome owns calibration (4.9).",
        "",
        "| DB | Level | Reasons |",
        "|----|-------|---------|",
    ]
    for _, r in triage.iterrows():
        lines.append(f"| {r['db_code']} | {r['alert_level']} | {str(r.get('alert_reasons', ''))[:120]} |")

    lines += ["", f"Full export: `{OUT_CSV.name}` · calibration: `account_health_calibration.csv`"]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "latest_month": str(latest),
        "flagged_dbs": int(len(triage)),
        "outputs": {
            "triage_csv": str(OUT_CSV.relative_to(ISZE)),
            "triage_md": str(OUT_MD.relative_to(ISZE)),
        },
    }
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"wrote {OUT_CSV} ({len(triage)} flagged)")
    print(f"wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
