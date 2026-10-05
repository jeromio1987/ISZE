# -*- coding: utf-8 -*-
"""Read-only: the 'Review needed' leaf, and where the 4 lamp rows' leaf sits on the master."""
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
PH = {"", "Unknown", "Unknown Review", "nan", "None", "To Review", "Unclassified"}


def mp(r):
    l1 = (r["aim_l1"] or "").strip(); l2 = (r["aim_l2"] or "").strip(); l3 = (r["aim_l3"] or "").strip()
    f1 = (r["aim_l1_fixed"] or "").strip(); f2 = (r["aim_l2_fixed"] or "").strip()
    if f1 not in PH:
        l1 = f1
    if f2 not in PH:
        l2 = f2
    return l1, l2, l3


n = 0
rows = []
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        p = mp(r)
        if p == ("Electrical", "Switch Relay Fuse", "Review needed"):
            n += 1
            rows.append(r)
print("rows on the leaf Electrical / Switch Relay Fuse / Review needed:", n)
for r in rows[:15]:
    print(f"  {r['part_number']:12} {r['description'][:28]:28} src={r['aim_source'][:34]}")

# does Lighting/Lighting/Lamp exist as a live leaf, and how big
from collections import Counter
leaf = Counter()
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        p = mp(r)
        if all(x and x not in PH for x in p):
            if p[0] in ("Lighting", "Electrical"):
                leaf[p] += 1
print("\nLighting / Electrical leaves and sizes:")
for k, v in leaf.most_common(30):
    print(f"  {v:>5}  {k}")
