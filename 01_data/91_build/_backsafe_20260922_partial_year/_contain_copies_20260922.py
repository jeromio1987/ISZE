"""Contain the three shared/export copies of gps_spu_by_distributor.csv.

Rule, applied identically to all three:
  1. RE-ANNOTATE FIRST - add the `period_basis` and `coverage_note` columns that
     the 2026-09-21 regeneration dropped, so the reader is told why the number
     went away. Blanking a number without the note leaves a silent gap.
  2. CONTAIN SECOND - on rows whose `period_basis` is `partial_year`, blank
     `gps_capture_vs_max` and `gps_capture_ex_warranty_vs_max` and set
     `traffic_light_v9` / `traffic_light_v9_ex_warranty` to `unknown`.

`total_sales_eur`, `max_spend_eur`, `uio_units` and `spend_per_unit_eur` are NOT
touched in any copy. Neither is any other column, and no row is added or removed.

  python _contain_copies_20260922.py            # dry run
  python _contain_copies_20260922.py --apply    # write
"""
from __future__ import annotations

import csv
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")

COPIES = [
    ROOT / "01_data/15_gpt_safe/gps_spu_by_distributor.csv",
    ROOT / "03_analytics/Isuzu/prism/evidence-app/data/derived/gps_spu_by_distributor.csv",
    ROOT / "09_meetings/BVDB_PBI_Data_Upload_2026-09-23/02_GPS/gps_spu_by_distributor.csv",
]

PARTIAL_BASIS = "partial_year"
FULL_BASIS = "full_year"

PARTIAL_NOTE = (
    "PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. "
    "Do not compare against a full-year row, and do not read a capture % or traffic "
    "light off this row: the max-spend target is a full-year figure. Basis not "
    "reconcilable to a clean quarter from sales_fact; see "
    "01_data/00_derived/_data_integrity_open_issues.md."
)
FULL_NOTE = "FULL YEAR - calendar year complete."

CAPTURE_COLS = ("gps_capture_vs_max", "gps_capture_ex_warranty_vs_max")
LIGHT_COLS = ("traffic_light_v9", "traffic_light_v9_ex_warranty")
PROTECTED = ("total_sales_eur", "max_spend_eur", "uio_units", "spend_per_unit_eur")

# Fallback when a row carries no basis and the caller did not supply one.
PARTIAL_YEARS = {"2026"}


def read_rows(path: Path) -> tuple[list[str], list[dict], str, bytes]:
    raw = path.read_bytes()
    bom = raw[:3] == b"\xef\xbb\xbf"
    encoding = "utf-8-sig" if bom else "utf-8"
    with path.open(encoding=encoding, newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    nl = "\r\n" if b"\r\n" in raw else "\n"
    return fieldnames, rows, ("utf-8-sig" if bom else "utf-8"), nl


def main() -> int:
    apply = "--apply" in sys.argv
    grand_changes: list[str] = []

    for path in COPIES:
        rel = path.relative_to(ROOT)
        print("=" * 96)
        print(rel)
        fieldnames, rows, encoding, nl = read_rows(path)
        had_basis = "period_basis" in fieldnames
        had_note = "coverage_note" in fieldnames

        before = [dict(r) for r in rows]
        before_fields = list(fieldnames)

        # ---- 1. re-annotate -------------------------------------------------
        if not had_basis:
            fieldnames.append("period_basis")
        if not had_note:
            fieldnames.append("coverage_note")
        n_annot = 0
        for r in rows:
            basis = (r.get("period_basis") or "").strip()
            if not basis:
                basis = PARTIAL_BASIS if r["year"] in PARTIAL_YEARS else FULL_BASIS
                r["period_basis"] = basis
                n_annot += 1
            note = (r.get("coverage_note") or "").strip()
            if not note:
                r["coverage_note"] = PARTIAL_NOTE if basis == PARTIAL_BASIS else FULL_NOTE
                if note != r["coverage_note"]:
                    n_annot += 1
        print(f"  re-annotate: added_basis_col={not had_basis} added_note_col={not had_note} "
              f"cells_filled={n_annot}")

        # ---- 2. contain -----------------------------------------------------
        n_cap = n_light = 0
        for r in rows:
            if (r.get("period_basis") or "").strip() != PARTIAL_BASIS:
                continue
            for c in CAPTURE_COLS:
                if c in fieldnames and (r.get(c) or "").strip():
                    r[c] = ""
                    n_cap += 1
            for c in LIGHT_COLS:
                if c in fieldnames:
                    v = (r.get(c) or "").strip()
                    if v not in ("", "unknown"):
                        r[c] = "unknown"
                        n_light += 1
        print(f"  contain:     capture cells blanked={n_cap} light cells set unknown={n_light}")

        # ---- guard: protected columns must be untouched ----------------------
        for old, new in zip(before, rows):
            assert (old["year"], old["distributor_code"]) == (
                new["year"], new["distributor_code"]
            ), "row order changed"
            for c in PROTECTED:
                if c in before_fields and (old.get(c) or "") != (new.get(c) or ""):
                    raise SystemExit(f"refusing: {c} changed on {old['year']} {old['distributor_code']}")
        # every other non-derived column must also be untouched
        allowed = set(CAPTURE_COLS) | set(LIGHT_COLS) | {"period_basis", "coverage_note"}
        for old, new in zip(before, rows):
            for c in before_fields:
                if c in allowed:
                    continue
                if (old.get(c) or "") != (new.get(c) or ""):
                    raise SystemExit(
                        f"refusing: unexpected change to {c} on "
                        f"{old['year']} {old['distributor_code']}"
                    )

        if not apply:
            print("  DRY RUN - nothing written")
            grand_changes.append(str(rel))
            continue

        # ---- write atomically, preserving BOM + line endings ----------------
        tmp = path.with_name(path.name + ".tmp_contain")
        with tmp.open("w", encoding=encoding, newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator=nl)
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, path)
        print(f"  wrote {path.stat().st_size} bytes")
        grand_changes.append(str(rel))

    print("=" * 96)
    print(f"{'WROTE' if apply else 'WOULD WRITE'} {len(grand_changes)} copies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
