# -*- coding: utf-8 -*-
"""Read-only: the numbers the report needs."""
import csv
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
T = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"
F = ROOT / "01_data" / "91_build" / "export_aim_fill_20260924"

with (F / "decision_164_final.csv").open(encoding="utf-8-sig", newline="") as fh:
    dec = list(csv.DictReader(fh))
placed = [d for d in dec if d["chosen_l1"]]
unplaced = [d for d in dec if not d["chosen_l1"]]

print(f"placed {len(placed)} | unplaced {len(unplaced)}")
print(f"list EUR placed: {sum(float(d['list_eur']) for d in placed):,.2f}")
print(f"list EUR unplaced: {sum(float(d['list_eur']) for d in unplaced):,.2f}")

sup = sorted(int(d["support_master"]) for d in placed)
print(f"master support: min {sup[0]} median {sup[len(sup)//2]} max {sup[-1]}")
print(f"distinct master support values: {Counter(sup).most_common()}")
print(f"rows where the workbook's AIM axis also carried the path: "
      f"{sum(1 for d in placed if int(d['support_classified_workbook']) > 0)}")

key_bad = [d for d in placed if d["fig_key_disagrees"] == "True"]
print(f"figure key top path differs from chosen path: {len(key_bad)}")
print("  ", [(d["pn"], d["fig_key"], d["chosen_l1"], d["fig_key_top_path"]) for d in key_bad])
no_key_ev = [d for d in placed if int(d["fig_key_n"]) == 0]
print(f"figure key with no master/workbook evidence at all: {len(no_key_ev)} "
      f"{[(d['pn'], d['fig_key']) for d in no_key_ev]}")

print("\nby AIM L1:")
for k, n in Counter(d["chosen_l1"] for d in placed).most_common():
    print(f"  {n:>4}  {k}")

l2 = Counter(d["chosen_l2"] for d in placed)
odd = [k for k in l2 if any(w in k.lower() for w in ("review", "other", "misc", "unclass"))]
print(f"\nL2 buckets that read like a holding pen: {[(k, l2[k]) for k in odd]}")

print("\nthe 2 unplaced:")
for d in unplaced:
    print(f"  {d['pn']}  {d['description']}  list EUR {d['list_eur']}  fig {d['fig_key']}  "
          f"reason: {d['unplaced_reason']}")
    print(f"     {d['evidence']}")

info = {}
with (T / "tierA_audited.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        info[r["pn"]] = r
print("\ntiering flags for the 2 unplaced:")
for d in unplaced:
    t = info[d["pn"]]
    print(f"  {d['pn']} tierA={t['tierA']} undefendable={t['undefendable']} convention={t['convention']} "
          f"d_l1={t['d_l1']} d_n={t['d_n']} f_l1={t['f_l1']} f_n={t['f_n']}")

master_rows = None
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    rd = csv.DictReader(fh)
    by = {r["part_number"]: r for r in rd}
print("\nthe 162 in the master now:")
print("  aim_source:", Counter(by[d["pn"]]["aim_source"] for d in placed).most_common(3))
print("  aim_changed:", Counter(by[d["pn"]]["aim_changed"] for d in placed).most_common(3))
print("  has_aim:", Counter(by[d["pn"]]["has_aim"] for d in placed).most_common(3))
print("  cat_l1 kept:", Counter(by[d["pn"]]["cat_l1"] for d in placed).most_common(3))
print("  cat_pms_flag kept:", Counter(by[d["pn"]]["cat_pms_flag"] for d in placed).most_common(3))
print("  cat_l2 non-PMS on rows whose cat_pms_flag is 0:",
      sum(1 for d in placed if by[d["pn"]]["cat_pms_flag"] == "0"))
