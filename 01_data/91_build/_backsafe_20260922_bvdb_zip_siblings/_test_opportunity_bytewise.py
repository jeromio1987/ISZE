#!/usr/bin/env python3
"""Strict check: are the old file's columns TEXT-identical in the rebuild?

Numeric equality is not enough - 25160.48 and 25160.480000000003 are numerically
equal but textually different, and the brief asks for the untouched cells to survive.
This compares raw rendered strings column by column.
"""
from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path

LIVE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
            r"\pms_opportunity_matrix.csv")
NEW = Path(tempfile.gettempdir()) / "pms_opp_rebuild_preview.csv"


def rows(p: Path):
    with p.open(encoding="utf-8-sig", newline="") as fh:
        r = csv.reader(fh)
        hdr = next(r)
        return hdr, list(r)


h_old, r_old = rows(LIVE)
h_new, r_new = rows(NEW)
keys = ["distributor_code", "pms_category", "year"]
new_by_key = {}
for r in r_new:
    new_by_key[tuple(r[h_new.index(k)] for k in keys)] = r
old_by_key = {}
for r in r_old:
    old_by_key[tuple(r[h_old.index(k)] for k in keys)] = r

print(f"old rows {len(r_old)}  new rows {len(r_new)}  "
      f"keys match: {set(old_by_key) == set(new_by_key)}")

shared = [c for c in h_old if c in h_new]
diffs: dict[str, int] = {}
examples: list[str] = []
for k, ro in old_by_key.items():
    rn = new_by_key.get(k)
    if rn is None:
        diffs["<missing row>"] = diffs.get("<missing row>", 0) + 1
        continue
    for c in shared:
        a = ro[h_old.index(c)]
        b = rn[h_new.index(c)]
        if a != b:
            diffs[c] = diffs.get(c, 0) + 1
            if len(examples) < 8:
                examples.append(f"{k} {c}: {a!r} -> {b!r}")

print(f"columns compared: {len(shared)}: {shared}")
if diffs:
    print("\nTEXT DIFFERENCES:")
    for c, n in sorted(diffs.items(), key=lambda x: -x[1]):
        print(f"   {c:26s} {n} rows")
    for e in examples:
        print("   ", e)
else:
    print("\nno text differences: every old column renders identically")

sys.exit(1 if diffs else 0)
