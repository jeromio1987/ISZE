# -*- coding: utf-8 -*-
"""Read-only probe: are the workbook's catalogue buckets AIM families at all?"""
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
A = ROOT / "01_data" / "91_build" / "_tmp_apply_export_pr00_20260924"
PH = {"", "Unknown", "Unknown Review", "nan", "None", "To Review", "Unclassified"}

master_l1 = Counter()
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        l1 = (r["aim_l1_fixed"] or "").strip()
        if l1 in PH:
            l1 = (r["aim_l1"] or "").strip()
        if l1 and l1 not in PH:
            master_l1[l1] += 1

print("AIM L1 values on the master:")
for k, v in master_l1.most_common():
    print(f"  {v:>7}  {k}")

print("\nworkbook catalogue L1 values, and whether the master uses each as an AIM L1:")
cat_l1 = Counter()
aim_seen = Counter()
with (D / "aim_pn_classification_20260920.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        c = (r.get("catalog_l1") or "").strip()
        if c:
            cat_l1[c] += 1
        a = (r.get("aim_l1_fixed") or "").strip()
        if a and a not in PH:
            aim_seen[a] += 1
for k, v in cat_l1.most_common():
    print(f"  {v:>7}  {k:<26} in AIM domain: {k in master_l1}")
print("\nworkbook AIM-axis L1 values (populated rows):")
for k, v in aim_seen.most_common():
    print(f"  {v:>7}  {k}")
print("\nworkbook rows with an AIM axis fully populated:",
      sum(1 for _ in ()) if False else "")
n_aim = 0
with (D / "aim_pn_classification_20260920.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        a = [(r.get(k) or "").strip() for k in ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed")]
        if all(x and x not in PH for x in a):
            n_aim += 1
print("  fully populated:", n_aim)

free = [l.strip() for l in (A / "would_land_free.txt").read_text().splitlines() if l.strip()]
blocked = [l.strip() for l in (A / "carried_out_blocked_precedence.txt").read_text().splitlines() if l.strip()]
have_aim = set()
with (D / "aim_pn_classification_20260920.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        a1 = (r.get("aim_l1_fixed") or "").strip()
        if a1 and a1 not in PH:
            have_aim.add((r.get("part_number") or "").strip())
print(f"\nof the 164, workbook rows carrying any AIM axis: {sum(1 for p in free if p in have_aim)}")
print(f"of the 92 blocked, workbook rows carrying any AIM axis: {sum(1 for p in blocked if p in have_aim)}")
