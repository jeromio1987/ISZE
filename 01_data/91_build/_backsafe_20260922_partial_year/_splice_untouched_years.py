"""Restore byte-identity for the untouched years in the source GPS file.

The builder round-trips the whole file through pandas, which re-renders four
spend_per_unit_eur cells in 2023-2024 at one unit in the last place (2.8e-14)
without changing their value. Task 6 asks for 2023-2025 to be byte-identical.

This keeps every non-2026 line exactly as it was in the backup, and takes the
2026 lines (the only ones the guard touches) from the builder's output. The
result carries exactly the same values, but the older years are the original
bytes.

  python _splice_untouched_years.py            # dry run
  python _splice_untouched_years.py --apply
"""
from __future__ import annotations

import csv
import io
import math
import os
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HERE = Path(__file__).resolve().parent
BACKUP = HERE / "original/01_data/00_derived/gps_spu_by_distributor.csv"
CURRENT = ROOT / "01_data/00_derived/gps_spu_by_distributor.csv"

apply = "--apply" in sys.argv

raw_backup = BACKUP.read_bytes()
raw_current = CURRENT.read_bytes()
nl = b"\r\n" if b"\r\n" in raw_backup else b"\n"
assert (b"\r\n" in raw_current) == (b"\r\n" in raw_backup), "line endings differ"
assert (raw_backup[:3] == b"\xef\xbb\xbf") == (raw_current[:3] == b"\xef\xbb\xbf"), "BOM differs"

backup_lines = raw_backup.splitlines(keepends=True)
current_lines = raw_current.splitlines(keepends=True)
print(f"lines backup={len(backup_lines)} current={len(current_lines)}")
assert len(backup_lines) == len(current_lines), "line count changed"

# header must be identical
assert backup_lines[0] == current_lines[0], "header changed"

out = [backup_lines[0]]
swapped = kept = 0
for a, b in zip(backup_lines[1:], current_lines[1:]):
    ya = a.split(b",", 1)[0]
    yb = b.split(b",", 1)[0]
    assert ya == yb, f"row order changed at {ya!r} vs {yb!r}"
    if ya == b"2026":
        out.append(b)
        swapped += 1
    else:
        out.append(a)
        kept += 1

print(f"2026 lines taken from the builder: {swapped}")
print(f"older lines kept as the original bytes: {kept}")

result = b"".join(out)

# prove the result parses to the same values as the builder output
def parse(txt: bytes):
    enc = "utf-8-sig" if txt[:3] == b"\xef\xbb\xbf" else "utf-8"
    return list(csv.DictReader(io.StringIO(txt.decode(enc), newline="")))


def numeric_equal(x: str, y: str) -> bool:
    try:
        return math.isclose(float(x), float(y), rel_tol=1e-12, abs_tol=1e-12)
    except (TypeError, ValueError):
        return False


cur_rows = parse(raw_current)
new_rows = parse(result)
assert len(cur_rows) == len(new_rows)
text_diffs = value_diffs = 0
for x, y in zip(cur_rows, new_rows):
    assert (x["year"], x["distributor_code"]) == (y["year"], y["distributor_code"])
    is_2026 = y["year"] == "2026"
    for k in x:
        if x[k] == y[k]:
            continue
        text_diffs += 1
        if not numeric_equal(x[k], y[k]):
            print(f"  VALUE DIFF {y['year']} {y['distributor_code']} {k}: {x[k]!r} -> {y[k]!r}")
            value_diffs += 1
        elif is_2026:
            print(f"  UNEXPECTED text change on a 2026 row: {y['distributor_code']} {k}")
            value_diffs += 1
print(f"text differences vs the builder output: {text_diffs} "
      f"(all numeric-equivalent: {text_diffs - value_diffs})")
print(f"value differences vs the builder output: {value_diffs}")
assert value_diffs == 0, "splice would change a value"
if text_diffs:
    print("  ^ these are the last-digit renderings restored to the original bytes, not value changes")

if not apply:
    print("\nDRY RUN - nothing written. Re-run with --apply.")
    raise SystemExit(0)

tmp = CURRENT.with_name(CURRENT.name + ".tmp_splice")
tmp.write_bytes(result)
os.replace(tmp, CURRENT)
print(f"\nwrote {CURRENT} ({CURRENT.stat().st_size} bytes)")
