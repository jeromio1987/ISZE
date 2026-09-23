#!/usr/bin/env python3
"""Splice the period columns onto an already-written CSV, byte-safely.

Why a splice and not a rebuild
------------------------------
`build_bvp_p4_p5.py` round-trips its whole output through pandas. Re-running it
re-renders existing float cells at one unit in the last place (the 2026-09-22 pass
saw 195.14028776978415 become 195.14028776978412 in four 2023-2024 cells). Task 3
requires 2023-2025 to stay byte-identical, so this keeps every original byte and
appends only two fields - `period_basis` and `coverage_note` - to each line.

Line endings are detected, not assumed: these files are CRLF with a trailing CRLF
and no BOM, and the splice preserves exactly that.

Usage:
  python _add_period_columns.py <csv> [<csv> ...]            # apply
  python _add_period_columns.py --dry-run <csv> [<csv> ...]  # report only
"""
from __future__ import annotations

import csv
import io
import os
import sys
from pathlib import Path

PRISM = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism")
sys.path.insert(0, str(PRISM))
from modules.year_coverage import is_partial  # noqa: E402

PARTIAL_BASIS = "partial_year"
FULL_BASIS = "full_year"

# Identical wording to enrich_gps_spu_v9.py, so the two files read the same way and
# a reader who has seen one recognises the other. Not restyled per run.
PARTIAL_COVERAGE_NOTE = (
    "PARTIAL YEAR - covers part of the calendar year, NOT 12 months. Do not "
    "compare against a full-year row: the denominator beside it is a full-year "
    "figure. See 01_data/00_derived/_data_integrity_open_issues.md."
)
FULL_COVERAGE_NOTE = "FULL YEAR - calendar year complete."

NEW_COLUMNS = ("period_basis", "coverage_note")
OK_SUFFIXES = {
    (PARTIAL_BASIS, PARTIAL_COVERAGE_NOTE),
    (FULL_BASIS, FULL_COVERAGE_NOTE),
}


def basis_for(year: int) -> tuple[str, str]:
    return ((PARTIAL_BASIS, PARTIAL_COVERAGE_NOTE) if is_partial(year)
            else (FULL_BASIS, FULL_COVERAGE_NOTE))


def splice(path: Path, dry_run: bool) -> dict:
    raw = path.read_bytes()
    bom = raw[:3] == b"\xef\xbb\xbf"
    text = raw.decode("utf-8-sig")
    if text.endswith("\r\n"):
        ending = "\r\n"
    elif text.endswith("\n"):
        ending = "\n"
    else:
        ending = ""
    body = text[: len(text) - len(ending)] if ending else text
    orig_lines = body.split(ending)

    header = next(csv.reader(io.StringIO(orig_lines[0])), [])
    if any(c in header for c in NEW_COLUMNS):
        return {"file": path.name, "status": "already carries " + NEW_COLUMNS[0],
                "changed": False}
    if "year" not in header:
        return {"file": path.name, "status": "no year column", "changed": False}
    yidx = header.index("year")

    rows = list(csv.reader(io.StringIO(body)))[1:]
    out = io.StringIO()
    w = csv.writer(out, lineterminator=ending)
    w.writerow(header + list(NEW_COLUMNS))
    n_partial = 0
    for row in rows:
        if not row:
            continue
        basis, note = basis_for(int(str(row[yidx]).strip()))
        n_partial += basis == PARTIAL_BASIS
        w.writerow(row + [basis, note])

    new_text = out.getvalue()
    if ending and not new_text.endswith(ending):
        new_text += ending
    new_bytes = (b"\xef\xbb\xbf" if bom else b"") + new_text.encode("utf-8")

    # Integrity proof: every original line must survive as a prefix, with exactly
    # the two new fields appended and nothing else touched. If this fails we write
    # nothing and say so.
    new_lines = (new_text[: len(new_text) - len(ending)] if ending else new_text).split(ending)
    if len(orig_lines) != len(new_lines):
        return {"file": path.name, "status": "LINE COUNT CHANGED - refusing",
                "changed": False}
    for i, (a, b) in enumerate(zip(orig_lines, new_lines)):
        if i == 0:
            if b != a + "," + ",".join(NEW_COLUMNS):
                return {"file": path.name, "status": f"header mismatch: {b!r}",
                        "changed": False}
            continue
        if not b.startswith(a + ","):
            return {"file": path.name, "status": f"line {i+1} prefix changed - refusing",
                    "changed": False}
        suffix = b[len(a) + 1:]
        if suffix not in {f"{x},{y}" for x, y in OK_SUFFIXES} and tuple(
                csv.reader([b]).__next__()[-2:]) not in OK_SUFFIXES:
            return {"file": path.name,
                    "status": f"unexpected suffix on line {i+1}: {suffix[:50]!r}",
                    "changed": False}

    detail = {
        "file": path.name,
        "rows": len(rows),
        "partial_rows": n_partial,
        "bytes_before": len(raw),
        "bytes_after": len(new_bytes),
        "ending": repr(ending),
        "bom": bom,
        "status": "dry-run",
        "changed": False,
    }
    if dry_run:
        return detail

    # Truncating writes fail on files in this workspace (Errno 22); temp + replace.
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as fh:
        fh.write(new_bytes)
    os.replace(tmp, path)
    detail.update(status="applied", changed=True)
    return detail


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    rc = 0
    for a in args:
        p = Path(a)
        if not p.is_file():
            print(f"MISSING {p}")
            rc = 1
            continue
        d = splice(p, dry)
        print(f"{d['file']:26s} status={d['status']:40s} rows={d.get('rows')} "
              f"partial={d.get('partial_rows')} "
              f"{d.get('bytes_before')}->{d.get('bytes_after')} ending={d.get('ending')}")
        if d["status"] not in ("applied", "dry-run", "already carries period_basis"):
            rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
