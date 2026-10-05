# -*- coding: utf-8 -*-
"""Read-only probe of the four descriptions where the description join and the figure key disagree."""
import csv
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
T = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"
PH = {"", "Unknown", "Unknown Review", "nan", "None", "To Review", "Unclassified"}
want = {"BRACKET; LAMP,RR COMB", "LAMP; LICENSE PLATE", "LENS; HEADER CONSOLE", "HARNESS; HEADLAMP"}

raw_pool = {}
fixed_pool = {}
rows = []
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        d = (r.get("description") or "").strip()
        if d not in want:
            continue
        rows.append(r)
        raw = ((r["aim_l1"] or "").strip(), (r["aim_l2"] or "").strip(), (r["aim_l3"] or "").strip())
        f1 = (r["aim_l1_fixed"] or "").strip()
        f2 = (r["aim_l2_fixed"] or "").strip()
        fixed = (f1 if f1 not in PH else raw[0], f2 if f2 not in PH else raw[1], raw[2])
        if all(x and x not in PH for x in raw):
            raw_pool.setdefault(d, Counter())[raw] += 1
        if all(x and x not in PH for x in fixed):
            fixed_pool.setdefault(d, Counter())[fixed] += 1

for d in want:
    print("=" * 90)
    print(d)
    print("  raw   aim path pool:", raw_pool.get(d, Counter()).most_common(5))
    print("  fixed-precedence pool:", fixed_pool.get(d, Counter()).most_common(5))
print()
for r in rows:
    print(f"{r['part_number']:12} {r['description'][:24]:24} "
          f"raw={r['aim_l1'][:16]:16}/{r['aim_l2'][:16]:16}/{r['aim_l3'][:14]:14} "
          f"fixed={r['aim_l1_fixed'][:16]:16}/{r['aim_l2_fixed'][:16]:16} "
          f"fig={r['fig_key']:9} src={r['aim_source'][:30]}")
