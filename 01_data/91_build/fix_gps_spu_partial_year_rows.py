"""
Fix the misleading partial-year rows in gps_spu_by_distributor.csv.

Defect (found 2026-09-15):
  The file carries rows for the current year (2026) whose total_sales_eur covers only part
  of that year, while max_spend_eur is a FULL-YEAR target. The file therefore computes
  gps_capture_vs_max = partial_year_sales / full_year_target, which lands at ~0.10-0.30 for
  every distributor and sets traffic_light_v9 = "red" across the whole network. A reader who
  compares spend_per_unit_eur across years concludes the business halved (~-43%).

This script does NOT invent a correction. It:
  1. backs up the original,
  2. adds explicit period_basis / coverage_note columns so the partial rows are self-describing,
  3. blanks the false capture % and traffic light on partial rows (leaving the raw sales intact),
  4. leaves 2023-2025 (full years) untouched.

Reversible: restore from the .pre_partial_year_fix.bak alongside the file.
"""
from __future__ import annotations

import csv
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CSV = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_spu_by_distributor.csv")
BAK = CSV.with_suffix(".csv.pre_partial_year_fix.bak")

PARTIAL_YEAR = "2026"          # the year whose rows are not a full 12 months
PARTIAL_NOTE = (
    "PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. "
    "Do not compare against a full-year row, and do not read a capture % or traffic light "
    "off this row: the max-spend target is a full-year figure. Basis not reconcilable to a "
    "clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
)
FULL_NOTE = "FULL YEAR - calendar year complete."

if not CSV.exists():
    sys.exit(f"missing {CSV}")

if not BAK.exists():
    shutil.copy2(CSV, BAK)
    print(f"backup written -> {BAK.name}")
else:
    print(f"backup already exists -> {BAK.name} (left as is)")

with CSV.open(encoding="utf-8-sig", newline="") as fh:
    rows = list(csv.DictReader(fh))
fieldnames = list(rows[0].keys())
print(f"read {len(rows)} rows, {len(fieldnames)} columns")

for col in ("period_basis", "coverage_note"):
    if col not in fieldnames:
        fieldnames.append(col)

n_partial = 0
for r in rows:
    if r["year"] == PARTIAL_YEAR:
        r["period_basis"] = "partial_year"
        r["coverage_note"] = PARTIAL_NOTE
        # blank the mis-derived fields: a full-year denominator must not yield a "capture"
        r["gps_capture_vs_max"] = ""
        r["traffic_light_v9"] = "unknown"
        r["gps_capture_ex_warranty_vs_max"] = ""
        r["traffic_light_v9_ex_warranty"] = ""
        n_partial += 1
    else:
        r["period_basis"] = "full_year"
        r["coverage_note"] = FULL_NOTE

with CSV.open("w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

print(f"rewrote {len(rows)} rows ({n_partial} partial-year rows flagged)")

# ── verify ────────────────────────────────────────────────────────────────────
with CSV.open(encoding="utf-8-sig", newline="") as fh:
    chk = list(csv.DictReader(fh))
assert "period_basis" in chk[0], "period_basis column missing"
p = [r for r in chk if r["period_basis"] == "partial_year"]
fy = [r for r in chk if r["period_basis"] == "full_year"]
bad = [r for r in p if r["traffic_light_v9"] != "unknown" or r["gps_capture_vs_max"] != ""]
print(f"CHECK partial={len(p)} full_year={len(fy)} rows_still_claiming_a_capture={len(bad)}")
print("CHECK 2025 rows still carry capture:",
      sum(1 for r in fy if r["year"] == "2025" and r["gps_capture_vs_max"] != ""), "of",
      sum(1 for r in fy if r["year"] == "2025"))
print("OK" if not bad else "FAIL")
