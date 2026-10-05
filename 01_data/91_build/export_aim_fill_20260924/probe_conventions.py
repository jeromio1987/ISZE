# -*- coding: utf-8 -*-
"""Read-only probe: master conventions around has_aim / aim_changed / *_fixed, and the exact
current values of the columns I intend to write on the 162."""
import csv
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
A = ROOT / "01_data" / "91_build" / "_tmp_apply_export_pr00_20260924"
F = ROOT / "01_data" / "91_build" / "export_aim_fill_20260924"
PH = {"", "Unknown", "Unknown Review", "nan", "None", "To Review", "Unclassified"}

with (F / "decision_164_final.csv").open(encoding="utf-8-sig", newline="") as fh:
    dec = list(csv.DictReader(fh))
placed = [d["pn"] for d in dec if d["chosen_l1"]]
print("placed in decision file:", len(placed))

rows = []
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    hdr = None
    for r in csv.DictReader(fh):
        rows.append(r)

# has_aim convention
c = Counter()
for r in rows:
    l1f = (r["aim_l1_fixed"] or "").strip()
    l1 = (r["aim_l1"] or "").strip()
    eff = l1f if l1f not in PH else l1
    c[(bool(eff and eff not in PH), (r["has_aim"] or "").strip())] += 1
print("\n(effective aim_l1 present?, has_aim) on the master:")
for k, v in c.most_common():
    print("  ", k, v)

print("\naim_changed distinct values:", Counter((r["aim_changed"] or "").strip() for r in rows).most_common(6))
print("aim_l1_fixed empty on rows whose aim_l1 is set:",
      sum(1 for r in rows if (r["aim_l1"] or "").strip() not in PH and (r["aim_l1_fixed"] or "").strip() in PH))
print("aim_l2_fixed empty on rows whose aim_l2 is set:",
      sum(1 for r in rows if (r["aim_l2"] or "").strip() not in PH and (r["aim_l2_fixed"] or "").strip() in PH))

by = {r["part_number"]: r for r in rows}
print("\ncurrent state of the 162 on the columns I would touch:")
cols = ["aim_l1", "aim_l2", "aim_l3", "aim_l1_fixed", "aim_l2_fixed", "has_aim",
        "aim_source", "aim_changed", "desc_ambiguous", "cat_l1", "cat_l2", "cat_l3",
        "cat_pms_flag", "has_catalogue_node", "fig_key", "fig_no", "key_no",
        "l12m_billed_eur", "eur", "description"]
for cc in cols:
    vals = Counter((by[p][cc] or "").strip() for p in placed)
    print(f"  {cc:>20}: {vals.most_common(5)}")
