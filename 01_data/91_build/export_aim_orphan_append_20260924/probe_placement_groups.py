# -*- coding: utf-8 -*-
"""Read-only: the 32 placed parts grouped by the AIM path they now sit on."""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\export_aim_orphan_append_20260924")

with (OUT / "decision_orphans.csv").open(encoding="utf-8-sig", newline="") as fh:
    dec = list(csv.DictReader(fh))
placed = [d for d in dec if d["place"].strip().lower() == "true"]
unplaced = [d for d in dec if d["place"].strip().lower() != "true"]

print(f"placed {len(placed)} | unplaced {len(unplaced)}\n")
c = Counter((d["chosen_l1"], d["chosen_l2"], d["chosen_l3"]) for d in placed)
for k, n in c.most_common():
    print(f"{n:>3}  {k[0]} > {k[1]} > {k[2]}")
print(f"\ndistinct paths: {len(c)}")
print(f"distinct Level 1: {sorted({d['chosen_l1'] for d in placed})}\n")
for d in sorted(placed, key=lambda x: x["pn"]):
    print(f"{d['pn']:12} {d['description'][:38]:38} -> "
          f"{d['chosen_l1']} > {d['chosen_l2']} > {d['chosen_l3']}   [{d['epc_fig_name']}]")
print()
print("all chosen paths already existed on the master:", all(
    d["route_a_triple"] and d["route"] == "a" for d in placed))
