"""PREPARED, NOT APPLIED. Re-contains the misleading 2026 rows of gps_spu_by_distributor.csv.

The 2026-09-15 containment blanked the false capture % and traffic light on the partial-year rows.
The 2026-09-21 regeneration restored values in those columns while leaving `period_basis =
partial_year` and the "do not read a capture % off this row" note intact. The columns and the note
now contradict each other.

This script restores the containment. It does NOT invent or change any sales figure: it blanks
four derived columns on the rows whose own `period_basis` already declares them unreadable.

Run with --apply to write. Without --apply it only prints what it would change.
It backs up first and can be reversed from that backup.

    python _contain_gps_2026_partial_rows_20260922.py            # dry run
    python _contain_gps_2026_partial_rows_20260922.py --apply    # write

NOT RUN as part of the 2026-09-22 schema-guard task: another workstream rebuilt the file on
21 Sep and its values are not ours to overwrite. Needs a human decision.
"""
from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path

CSV_PATH = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_spu_by_distributor.csv")
BAK = CSV_PATH.with_name(CSV_PATH.name + ".pre_contain_2026_partial_20260922.bak")
BEFORE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\gps_2026_partial_before_values_20260922.json")

# The four columns the 2026-09-15 containment blanked. `total_sales_eur`, `max_spend_eur`,
# `uio_units` and `spend_per_unit_eur` are NOT touched: the first three are raw facts, and the
# fourth is correctly computed for the part year.
BLANK_CAPTURE = "gps_capture_vs_max"
BLANK_CAPTURE_EX = "gps_capture_ex_warranty_vs_max"
BLANK_LIGHT = "traffic_light_v9"
BLANK_LIGHT_EX = "traffic_light_v9_ex_warranty"

TARGET_BASIS = "partial_year"


def main() -> int:
    apply = "--apply" in sys.argv
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    for col in (BLANK_CAPTURE, BLANK_CAPTURE_EX, BLANK_LIGHT, BLANK_LIGHT_EX):
        if col not in fieldnames:
            sys.exit(f"column {col} not in the file - refusing to guess")

    changes: list[dict] = []
    for r in rows:
        if r.get("period_basis") != TARGET_BASIS:
            continue
        row_change = {"year": r["year"], "distributor_code": r["distributor_code"], "fields": {}}
        touched = False
        for col in (BLANK_CAPTURE, BLANK_CAPTURE_EX, BLANK_LIGHT_EX):
            cur = (r.get(col) or "").strip()
            if cur != "":
                row_change["fields"][col] = {"from": cur, "to": ""}
                r[col] = ""
                touched = True
        cur_light = (r.get(BLANK_LIGHT) or "").strip()
        if cur_light not in ("", "unknown"):
            row_change["fields"][BLANK_LIGHT] = {"from": cur_light, "to": "unknown"}
            r[BLANK_LIGHT] = "unknown"
            touched = True
        if touched:
            changes.append(row_change)

    n_capture = sum(1 for c in changes if BLANK_CAPTURE in c["fields"])
    n_light = sum(1 for c in changes if BLANK_LIGHT in c["fields"])
    print(f"rows with period_basis={TARGET_BASIS}: "
          f"{sum(1 for r in rows if r.get('period_basis') == TARGET_BASIS)}")
    print(f"rows that would change: {len(changes)}")
    print(f"  {BLANK_CAPTURE} blanked on      {n_capture} rows")
    print(f"  {BLANK_LIGHT} set to unknown on  {n_light} rows")
    print()
    for c in changes:
        print(f"  {c['year']} {c['distributor_code']:14} " +
              "  ".join(f"{k}: {v['from']} -> {v['to'] or '(blank)'}"
                        for k, v in c["fields"].items()))

    if not changes:
        print("\nnothing to do")
        return 0

    if not apply:
        print("\nDRY RUN - nothing written. Re-run with --apply to contain.")
        return 0

    if not BAK.exists():
        shutil.copy2(CSV_PATH, BAK)
        print(f"\nbackup -> {BAK.name}")
    else:
        print(f"\nbackup already exists -> {BAK.name} (left as is)")

    BEFORE.write_text(json.dumps(changes, indent=2), encoding="utf-8")
    tmp = CSV_PATH.with_name(CSV_PATH.name + ".tmp_contain")
    with tmp.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    tmp.replace(CSV_PATH)
    print(f"wrote {CSV_PATH}")
    print(f"before-values record -> {BEFORE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
