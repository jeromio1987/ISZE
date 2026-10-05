#!/usr/bin/env python3
"""Add the period / like-for-like columns to pms_opportunity_matrix.csv, byte-safely.

Same splice principle as _add_period_columns.py: keep every original byte and append
fields, so the pre-2026 rows (and every existing 2026 field) survive byte-identical.
This file needs five new fields rather than two, so the field list is passed in.

The values written here are what the patched build_pms_opportunity_matrix.py emits,
from the same helper and the same wording. If the builder runs, they match.

Usage: python _add_opportunity_columns.py [--dry-run]
"""
from __future__ import annotations

import csv
import io
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PRISM = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism")
sys.path.insert(0, str(PRISM))
from modules.year_coverage import is_partial, year_coverage  # noqa: E402

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PACK = ROOT / "09_meetings" / "BVDB_PBI_Data_Upload_2026-09-23"

PARTIAL_BASIS = "partial_year"
FULL_BASIS = "full_year"
PARTIAL_COVERAGE_NOTE = (
    "PARTIAL YEAR - actual_qty covers part of the calendar year, NOT 12 months, "
    "while expected_qty is a full year. revenue_gap_eur is therefore the gap against "
    "the FULL YEAR expectation and is larger than a like-for-like gap; "
    "gap_eur_like_for_like puts the expectation on the same period. See "
    "01_data/00_derived/_data_integrity_open_issues.md."
)
FULL_COVERAGE_NOTE = "FULL YEAR - calendar year complete."
L4L_ASSUMPTION_PARTIAL = (
    "Sets expected_qty to coverage x expected_qty, where coverage is the share of the "
    "calendar year the billing data reaches (from modules.year_coverage). ASSUMES the "
    "year's expectation falls evenly across months, which it does not - filters and "
    "brakes are seasonal. A comparator, not a replacement for revenue_gap_eur."
)
L4L_ASSUMPTION_FULL = "No pro-rating: a full-year row needs none. Equals revenue_gap_eur."

NEW = ["gap_eur_like_for_like", "period_basis", "coverage_note",
       "like_for_like_assumption", "year_coverage_pct"]


def splicer(path: Path, dry_run: bool) -> dict:
    raw = path.read_bytes()
    bom = raw[:3] == b"\xef\xbb\xbf"
    text = raw.decode("utf-8-sig")
    ending = "\r\n" if text.endswith("\r\n") else ("\n" if text.endswith("\n") else "")
    body = text[: len(text) - len(ending)] if ending else text
    orig_lines = body.split(ending)

    header = next(csv.reader(io.StringIO(orig_lines[0])), [])
    if any(c in header for c in NEW):
        return {"file": path.name, "status": "already annotated", "changed": False}
    need = {"year", "expected_qty", "actual_qty", "revenue_gap_eur", "avg_sp_eur"}
    if not need.issubset(header):
        return {"file": path.name,
                "status": f"missing required columns: {sorted(need - set(header))}",
                "changed": False}

    cov = year_coverage()
    rows = list(csv.reader(io.StringIO(body)))[1:]
    out = io.StringIO()
    w = csv.writer(out, lineterminator=ending)
    w.writerow(header + NEW)
    n_partial = n_full = 0
    for row in rows:
        if not row:
            continue
        rec = dict(zip(header, row))
        year = int(str(rec["year"]).strip())
        partial = is_partial(year)
        coverage = float(cov.get(year, 1.0))
        exp = float(rec["expected_qty"])
        act = float(rec["actual_qty"])
        sp = float(rec["avg_sp_eur"])
        l4l = round(max(exp * coverage - act, 0.0) * sp, 2)
        if partial:
            n_partial += 1
        else:
            n_full += 1
            if abs(l4l - float(rec["revenue_gap_eur"])) > 0.01:
                return {"file": path.name,
                        "status": f"full-year row {year}/{rec.get('pms_category')} "
                                  f"would move ({l4l} vs {rec['revenue_gap_eur']})",
                        "changed": False}
        w.writerow(row + [repr(l4l), PARTIAL_BASIS if partial else FULL_BASIS,
                          PARTIAL_COVERAGE_NOTE if partial else FULL_COVERAGE_NOTE,
                          L4L_ASSUMPTION_PARTIAL if partial else L4L_ASSUMPTION_FULL,
                          repr(round(coverage, 4))])

    new_text = out.getvalue()
    if ending and not new_text.endswith(ending):
        new_text += ending
    new_lines = (new_text[: len(new_text) - len(ending)] if ending else new_text).split(ending)
    if len(orig_lines) != len(new_lines):
        return {"file": path.name, "status": "LINE COUNT CHANGED - refusing",
                "changed": False}
    for i, (a, b) in enumerate(zip(orig_lines, new_lines)):
        if i == 0:
            if b != a + "," + ",".join(NEW):
                return {"file": path.name, "status": f"header mismatch: {b[:80]!r}",
                        "changed": False}
            continue
        if not b.startswith(a + ","):
            return {"file": path.name, "status": f"line {i+1} prefix changed - refusing",
                    "changed": False}
        parsed = csv.reader([b]).__next__()
        if len(parsed) != len(header) + len(NEW):
            return {"file": path.name, "status": f"line {i+1} field count wrong",
                    "changed": False}

    new_bytes = (b"\xef\xbb\xbf" if bom else b"") + new_text.encode("utf-8")
    detail = {"file": path.name, "rows": len(rows), "partial_rows": n_partial,
              "full_rows": n_full, "bytes_before": len(raw), "bytes_after": len(new_bytes),
              "status": "dry-run", "changed": False}
    if dry_run:
        return detail
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as fh:
        fh.write(new_bytes)
    os.replace(tmp, path)
    detail.update(status="applied", changed=True)
    return detail


def main() -> int:
    dry = "--dry-run" in sys.argv
    rc = 0
    for p in (DER / "pms_opportunity_matrix.csv",
              PACK / "03_PMS" / "pms_opportunity_matrix.csv"):
        if not p.is_file():
            print("MISSING", p)
            rc = 1
            continue
        d = splicer(p, dry)
        print(f"{d['file']:34s} status={d['status']:34s} rows={d.get('rows')} "
              f"partial={d.get('partial_rows')} full={d.get('full_rows')} "
              f"{d.get('bytes_before')}->{d.get('bytes_after')}")
        if d["status"] not in ("applied", "dry-run", "already annotated"):
            rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
