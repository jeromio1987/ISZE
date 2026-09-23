"""Add the period-basis note to the two GPS and three PMS MANIFEST rows, and add a
manifest entry for the new annotation columns. Preserves BOM and line endings."""
from __future__ import annotations

import csv
import os
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
MANIFEST = ROOT / "09_meetings/BVDB_PBI_Data_Upload_2026-09-23/00_START_HERE/MANIFEST.csv"

NOTE = (
    " 2026 rows cover January-August only; filter period_basis. "
    "gps_capture_vs_max / traffic_light_v9 are intentionally empty / unknown on 2026 rows."
)
NOTE_PMS = " 2026 rows cover January-August only; not comparable with full-year 2025."

raw = MANIFEST.read_bytes()
enc = "utf-8-sig" if raw[:3] == b"\xef\xbb\xbf" else "utf-8"
nl = "\r\n" if b"\r\n" in raw else "\n"

with MANIFEST.open(encoding=enc, newline="") as fh:
    rd = csv.DictReader(fh)
    fields = list(rd.fieldnames or [])
    rows = list(rd)

changed = 0
for r in rows:
    f = r["file"]
    if f == "02_GPS/gps_spu_by_distributor.csv":
        if "period_basis" not in (r.get("purpose") or ""):
            r["purpose"] = (r.get("purpose") or "").rstrip() + NOTE
            r["cols"] = "21"
            changed += 1
        if "period_basis" not in (r.get("join_keys") or ""):
            r["join_keys"] = "distributor_code, year, period_basis"
    elif f in ("02_GPS/gps_spu_by_family.csv", "02_GPS/gps_spu_pms.csv",
               "03_PMS/pms_summary_by_db.csv", "03_PMS/pms_capture_by_db_year.csv"):
        if "January-August" not in (r.get("purpose") or ""):
            r["purpose"] = (r.get("purpose") or "").rstrip() + NOTE_PMS
            changed += 1
    elif f == "04_AIM/aim_gps_matrix.csv":
        if "January-August" not in (r.get("purpose") or ""):
            r["purpose"] = (r.get("purpose") or "").rstrip() + NOTE_PMS
            changed += 1

print(f"rows touched: {changed}")
for r in rows:
    if r["file"].startswith(("02_GPS", "03_PMS")) or r["file"].startswith("04_AIM/aim_gps"):
        print(f"  {r['file']}\n     purpose: {r['purpose']}\n     keys:    {r['join_keys']}")

tmp = MANIFEST.with_name(MANIFEST.name + ".tmp_note")
with tmp.open("w", encoding=enc, newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=fields, lineterminator=nl)
    w.writeheader()
    w.writerows(rows)
os.replace(tmp, MANIFEST)
print(f"\nwrote {MANIFEST} ({MANIFEST.stat().st_size} bytes)")
