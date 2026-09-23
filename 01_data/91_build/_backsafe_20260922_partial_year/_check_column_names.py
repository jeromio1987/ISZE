"""Every technical name in HOW_TO.md must exist in the pack, so a reader is never
sent to a column that is not there."""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PACK = ROOT / "09_meetings/BVDB_PBI_Data_Upload_2026-09-23"
HOWTO = PACK / "00_START_HERE/HOW_TO.md"

# names I introduced or verified in this session
CANDIDATES = [
    "period_basis",
    "coverage_note",
    "gps_capture_vs_max",
    "gps_capture_ex_warranty_vs_max",
    "traffic_light_v9",
    "max_spend_eur",
    "total_sales_eur",
    "uio_units",
    "spend_per_unit_eur",
    "network_role",
    "excluded_non_parts",
    "is_actual",
    "is_estimate",
    "is_forecast",
    "line_type",
    "capture_rate_total_wtd",
    "target_spend_ceiling_eur",
    "parts_billed_total_eur",
    "sold_to_sap",
    "distributor_code",
    "pms_category",
    "basis",
]

# where each name is claimed to live
WHERE = {
    "period_basis": ["02_GPS/gps_spu_by_distributor.csv"],
    "coverage_note": ["02_GPS/gps_spu_by_distributor.csv"],
    "gps_capture_vs_max": ["02_GPS/gps_spu_by_distributor.csv"],
    "gps_capture_ex_warranty_vs_max": ["02_GPS/gps_spu_by_distributor.csv"],
    "traffic_light_v9": ["02_GPS/gps_spu_by_distributor.csv"],
    "max_spend_eur": ["02_GPS/gps_spu_by_distributor.csv"],
    "total_sales_eur": ["02_GPS/gps_spu_by_distributor.csv"],
    "uio_units": ["02_GPS/gps_spu_by_distributor.csv", "01_UIO/fact_uio_by_distributor_year.csv"],
    "spend_per_unit_eur": ["02_GPS/gps_spu_by_distributor.csv"],
    "network_role": ["01_UIO/dim_distributor.csv"],
    "excluded_non_parts": ["01_UIO/dim_distributor.csv"],
    "is_actual": ["01_UIO/fact_uio_by_distributor_year.csv"],
    "is_estimate": ["01_UIO/fact_uio_by_distributor_year.csv"],
    "is_forecast": ["01_UIO/fact_uio_by_distributor_year.csv"],
    "line_type": ["03_PMS/pms_capture_by_db_year.csv"],
    "capture_rate_total_wtd": ["03_PMS/pms_summary_by_db.csv"],
    "target_spend_ceiling_eur": ["02_GPS/target_spend_waterfall.csv"],
    "parts_billed_total_eur": ["02_GPS/target_spend_waterfall.csv"],
    "sold_to_sap": ["01_UIO/dim_distributor.csv"],
    "distributor_code": ["01_UIO/fact_uio_by_distributor_year.csv"],
    "pms_category": ["04_AIM/dim_pms_category.csv"],
    "basis": ["01_UIO/fact_uio_by_market_type_year.csv"],
}

howto = HOWTO.read_text(encoding="utf-8")
print("Every name must appear in HOW_TO.md AND in the file claimed:")
problems = []
for name in CANDIDATES:
    in_doc = bool(re.search(r"\b" + re.escape(name) + r"\b", howto))
    found_where = []
    for rel in WHERE.get(name, []):
        p = PACK / rel
        if not p.exists():
            problems.append(f"{name}: claimed file missing {rel}")
            continue
        raw = p.read_bytes()
        enc = "utf-8-sig" if raw[:3] == b"\xef\xbb\xbf" else "utf-8"
        with p.open(encoding=enc, newline="") as fh:
            rows = list(csv.DictReader(fh))
        cols = list(rows[0].keys()) if rows else []
        if name in cols:
            found_where.append(rel)
        elif any(name in (r.get(c) or "") for r in rows for c in cols):
            found_where.append(f"{rel} (as a VALUE of another column)")
    status = "OK" if (in_doc and found_where) else "PROBLEM"
    if status == "PROBLEM":
        problems.append(f"{name}: in_doc={in_doc} found_in={found_where}")
    print(f"  {status:8} {name:34} in_doc={in_doc!s:5} found_in={found_where}")

print()
if problems:
    print("PROBLEMS:")
    for p in problems:
        print("  -", p)
    raise SystemExit(1)
print("every name is real and is documented")
