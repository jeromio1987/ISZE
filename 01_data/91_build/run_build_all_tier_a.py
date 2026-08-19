#!/usr/bin/env python3
"""BUILD ALL Tier A — aftermarket BI orchestrator (2026-08-19).

Runs A1–A14 in dependency order. No Book A/B alloc.
Writes 01_data/91_build/BUILD_ALL_TIER_A_20260819.meta.json
"""

from __future__ import annotations

import json
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

ISZE = Path(__file__).resolve().parents[2]
OUT_META = Path(__file__).resolve().parent / "BUILD_ALL_TIER_A_20260819.meta.json"


def run_step(item: str, script: Path, extra: list[str] | None = None) -> dict:
    cmd = [sys.executable, str(script)] + (extra or [])
    t0 = datetime.now(timezone.utc)
    try:
        r = subprocess.run(cmd, cwd=str(ISZE), capture_output=True, text=True, timeout=900)
        ok = r.returncode == 0
        return {
            "item": item,
            "status": "done" if ok else "failed",
            "script": str(script.relative_to(ISZE)),
            "returncode": r.returncode,
            "stdout_tail": (r.stdout or "")[-2000:],
            "stderr_tail": (r.stderr or "")[-2000:],
            "started_at": t0.isoformat(timespec="seconds"),
        }
    except Exception as exc:
        return {
            "item": item,
            "status": "failed",
            "script": str(script.relative_to(ISZE)),
            "error": str(exc),
            "traceback": traceback.format_exc()[-2000:],
            "started_at": t0.isoformat(timespec="seconds"),
        }


def main() -> int:
    steps: list[tuple[str, Path, list[str] | None]] = [
        ("A1", ISZE / "04_tools" / "forecast" / "build_forecast_baseline.py", None),
        ("A2", ISZE / "04_tools" / "forecast" / "build_forecast_final.py", None),
        ("A5", ISZE / "01_data" / "91_build" / "build_db_dlr_commercial_stack.py", None),
        ("A6", ISZE / "01_data" / "91_build" / "build_revision_book_b_pack.py", None),
        ("A4", ISZE / "01_data" / "91_build" / "build_book_b_review_workbook.py", None),
        ("A3", ISZE / "02_dashboards" / "sales" / "_build" / "build_db_dlr_replenishment_cy2025.py", None),
        ("A7", ISZE / "01_data" / "91_build" / "build_supersession_delta.py", None),
        ("A14", ISZE / "01_data" / "91_build" / "build_pricing_history_findings.py", None),
        ("A8", ISZE / "01_data" / "91_build" / "build_list_to_pocket_validation.py", None),
        ("A9", ISZE / "01_data" / "91_build" / "build_account_health_ops_pack.py", None),
        ("A10", ISZE / "01_data" / "91_build" / "build_portfolio_triage.py", None),
        ("A11_ITUK", ISZE / "04_tools" / "db_operating_dashboard" / "build_ledger.py", ["--db", "ITUK"]),
        ("A11_UTI", ISZE / "04_tools" / "db_operating_dashboard" / "build_ledger.py", ["--db", "UTI"]),
        ("A13", ISZE / "09_meetings" / "PMS_BVP_Regain_2026" / "_build_dashboard.py", None),
    ]

    log: list[dict] = []
    for item, script, extra in steps:
        print(f"\n=== {item} ===")
        if not script.is_file():
            log.append({"item": item, "status": "failed", "error": f"missing {script}"})
            print(f"MISSING {script}")
            continue
        res = run_step(item, script, extra)
        log.append(res)
        print(res.get("stdout_tail") or res.get("stderr_tail") or res.get("error", ""))

    # A12 — skipped unless explicit next DB
    log.append(
        {
            "item": "A12",
            "status": "skipped",
            "reason": "No explicit next db_sales_review DB in brief; profiles exist for IUK/ITUK/UTI/UMI etc.",
        }
    )

    # A2 PRISM page is static file — mark done if forecast outputs exist
    fc = ISZE / "01_data" / "00_derived" / "forecast_final.parquet"
    prism = ISZE / "03_analytics" / "Isuzu" / "prism" / "pages" / "19_Forecast.py"
    log.append(
        {
            "item": "A2_prism",
            "status": "done" if fc.is_file() and prism.is_file() else "failed",
            "outputs": [str(fc.relative_to(ISZE)), str(prism.relative_to(ISZE))],
        }
    )

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "authority": "BUILD ALL Tier A — no alloc",
        "steps": log,
        "summary": {
            "done": sum(1 for s in log if s["status"] == "done"),
            "failed": sum(1 for s in log if s["status"] == "failed"),
            "skipped": sum(1 for s in log if s["status"] == "skipped"),
        },
    }
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"\n=== meta -> {OUT_META} ===")
    print(meta["summary"])
    return 0 if meta["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
