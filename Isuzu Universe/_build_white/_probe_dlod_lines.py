# -*- coding: utf-8 -*-
r"""Read the DLOD / DLAD lines out of the raw billing extracts and report exactly what is there.

Read-only. Reports the header, the stated line, and a case-insensitive sweep for the labels so the
search is not itself case-sensitive - the label appears as DLOD, dlod and DLAD.
"""
import csv
import io
import os
import re
import sys

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
sys.stdout.reconfigure(encoding="utf-8")

TARGETS = [
    ("cy2023_2024.csv", [173794, 72635, 129873]),
    ("order_headers_from_Order_Detail.csv", [9914, 9976]),
    ("cy2026_q1.csv", [19696]),
]

for fn, lines in TARGETS:
    p = os.path.join(ROOT, fn)
    print("=" * 100)
    print(fn, "  size", "{:,}".format(os.path.getsize(p)))
    with io.open(p, encoding="utf-8-sig", errors="replace", newline="") as fh:
        rdr = csv.reader(fh)
        header = next(rdr)
        print("  columns:", header)
        n = 0
        want = {}
        for i, row in enumerate(rdr, start=1):
            n = i
            if i in lines:
                want[i] = row
            if i > max(lines):
                break
    for ln in lines:
        row = want.get(ln)
        if row is None:
            print("  line {} NOT REACHED".format(ln))
            continue
        print("  --- csv data-line {} (i.e. file line {}) ---".format(ln, ln + 1))
        for k, v in zip(header, row):
            if v not in ("", None):
                print("      {:>22} = {}".format(k, v[:120]))
    print("  rows read:", n)

print()
print("=" * 100)
print("CASE-INSENSITIVE SWEEP for dlod / dlad in the reference-ish text columns")
for fn in ("cy2023_2024.csv", "order_headers_from_Order_Detail.csv", "cy2026_q1.csv"):
    p = os.path.join(ROOT, fn)
    hits = []
    with io.open(p, encoding="utf-8-sig", errors="replace", newline="") as fh:
        rdr = csv.reader(fh)
        header = next(rdr)
        for i, row in enumerate(rdr, start=1):
            joined = " | ".join(row)
            if re.search(r"\bdl[oa]d\b", joined, re.I):
                hits.append((i, row))
            if len(hits) >= 12:
                break
    print()
    print("--", fn, "hits:", len(hits))
    for i, row in hits:
        print("   line {}".format(i))
        for k, v in zip(header, row):
            if v not in ("", None):
                print("        {:>22} = {}".format(k, v[:110]))
