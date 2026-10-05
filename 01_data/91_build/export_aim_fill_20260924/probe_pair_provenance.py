# -*- coding: utf-8 -*-
"""Read-only: why the pair's aim_source for the 162 is not the fill stamp."""
import csv
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
F = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\export_aim_fill_20260924")

with (F / "decision_164_final.csv").open(encoding="utf-8-sig", newline="") as fh:
    placed = [d["pn"] for d in csv.DictReader(fh) if d["chosen_l1"]]
S = set(placed)

ov = {}
with (D / "aim_pn_classification_20260920.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        if r["part_number"] in S:
            ov[r["part_number"]] = r["aim_source"]
print(f"of the 162, rows present in the classification overlay: {len(ov)}")
print("their overlay aim_source:", Counter(ov.values()).most_common(6))

pair = {}
with (D / "AIM_Master_PN_Categories_Figkey_20260924.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        if r["part_number"] in S:
            pair[r["part_number"]] = r["aim_source"]
print("pair aim_source:", Counter(pair.values()).most_common(6))
mismatch = [p for p in S if ov.get(p) != pair.get(p)]
print(f"rows where the pair's source differs from the overlay's: {len(mismatch)}")
print("sample:", [(p, ov.get(p), pair.get(p)) for p in mismatch[:5]])
