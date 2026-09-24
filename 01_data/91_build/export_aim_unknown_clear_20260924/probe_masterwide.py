# -*- coding: utf-8 -*-
"""Read-only probe 4: master-wide marker count, so the report can state the measured
figure rather than assume 4,934 / 4,935.
"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
WHY = ROOT / "01_data" / "91_build" / "export_aim_open_why_20260924"

MARK = {"unknown", "unknown review", "to review", "unclassified"}


def bl(s):
    return (s or "").strip()


def is_marker(s):
    t = bl(s).lower()
    return t in MARK or t.startswith("unknown")


master = []
with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    master = list(csv.DictReader(fh))
print("master rows:", len(master))

l1_marker = [r for r in master if is_marker(r["aim_l1"])]
l1f_marker = [r for r in master if is_marker(r["aim_l1_fixed"])]
any_marker = [r for r in master if any(
    is_marker(r.get(c)) for c in ("aim_l1", "aim_l2", "aim_l3", "aim_l1_fixed", "aim_l2_fixed"))]
print("master-wide rows with aim_l1 a marker      :", len(l1_marker))
print("master-wide rows with aim_l1_fixed a marker:", len(l1f_marker))
print("master-wide rows with any AIM column marker :", len(any_marker))
print("master-wide, exact l1 strings:",
      dict(Counter(bl(r["aim_l1"]) for r in l1_marker)))

print("")
print("master-wide marker rows by aim_source:")
for k, v in Counter(bl(r["aim_source"]) for r in any_marker).most_common():
    print(f"   {k!r:26s} {v}")

print("")
print("master-wide marker rows by has_aim:")
for k, v in Counter(bl(r["has_aim"]) for r in any_marker).most_common():
    print(f"   {k!r:6s} {v}")

# price-list subset + non-subset
opn = set()
with (WHY / "open_parts_classified.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        opn.add(bl(r["pnk"]).upper())

on_list = [r for r in any_marker if bl(r["part_number"]) in opn]
off_list = [r for r in any_marker if bl(r["part_number"]) not in opn]
print("")
print("marker rows whose part number is on the IE40 open list :", len(on_list))
print("marker rows NOT on the list (must keep their marker)   :", len(off_list))
print("sum:", len(on_list) + len(off_list))

print("")
print("the brief's arithmetic")
print("   4,934 claimed master-wide  |  819 claimed on-list  -> others 4,115")
print(f"   measured master-wide {len(any_marker)}  |  measured on-list {len(on_list)}  -> others {len(off_list)}")

# 5,000-ish check on the old overlay number quoted in the brief
ov = 0
with (DER / "aim_pn_classification_20260920.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        if any(is_marker(r.get(c)) for c in ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed")):
            ov += 1
print("")
print("overlay rows carrying a marker in aim_l*_fixed :", ov)
