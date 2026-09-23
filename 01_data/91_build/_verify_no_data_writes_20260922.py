"""Confirm nothing in 01_data/00_derived was written during this task, and show the schema checks."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

REPO = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = REPO / "01_data" / "00_derived"

print("=== schema_required checks in the report ===")
rep = json.loads((DERIVED / "_verification_report.json").read_text(encoding="utf-8"))
print("SUMMARY:", rep["summary"])
print()
for c in rep["checks"]:
    if c["id"].startswith("schema."):
        print(f"[{c['status']:4}] {c['id']}")
        print(f"         {c['message'][:190]}")
print()
print("=== non-pass checks ===")
for c in rep["checks"]:
    if c["status"] != "pass":
        print(f"[{c['status']}] {c['id']}: {c['message'][:220]}")
print()
print("=== the six named files: mtime (should predate this task, ~17:00-17:5x) ===")
names = [
    "gps_spu_by_distributor.csv", "lost_sales_model.csv", "nseries_tonnage_evolution.csv",
    "epc_decode_nseries_banded.csv", "pms_capture_by_db_year.csv", "metrics_snapshot.json",
]
for n in names:
    p = DERIVED / n
    mt = datetime.fromtimestamp(p.stat().st_mtime)
    print(f"  {n:34} {mt:%Y-%m-%d %H:%M:%S}")

print()
print("=== files written by this task (expected only in 01_data/91_build and prism) ===")
cut = datetime(2026, 9, 22, 17, 0, 0).timestamp()
for p in sorted(DERIVED.glob("*")):
    if p.is_file() and p.stat().st_mtime >= cut:
        mt = datetime.fromtimestamp(p.stat().st_mtime)
        print(f"  {p.name:50} {mt:%H:%M:%S}")
