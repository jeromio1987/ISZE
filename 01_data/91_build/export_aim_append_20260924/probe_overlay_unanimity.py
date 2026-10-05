# -*- coding: utf-8 -*-
"""Read-only: overlay membership + unanimity of demand type / core / catalogue path for the 44."""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
T = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"
A = ROOT / "01_data" / "91_build" / "_tmp_apply_export_pr00_20260924"
PH = {"", "Unknown", "Unknown Review", "Not on AIM spine", "nan", "None", "To Review",
      "Unclassified"}

pns = [l.strip() for l in (A / "carried_out_not_in_master.txt").read_text().splitlines() if l.strip()]
info = {}
with (T / "tierA_audited.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        if r["pn"] in pns:
            info[r["pn"]] = r

# ---- overlay membership ----
overlay = {}
with (D / "aim_pn_classification_20260920.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        if r["part_number"] in pns:
            overlay[r["part_number"]] = r
print(f"of the 44, present in the classification overlay: {len(overlay)}")
for pn, r in overlay.items():
    print("   ", pn, "| aim_fixed:", (r.get("aim_l1_fixed"), r.get("aim_l2_fixed"), r.get("aim_l3_fixed")),
          "| aim_source:", r.get("aim_source"), "| line_kind:", r.get("line_kind"),
          "| fig_key:", r.get("fig_key"), "| catalog:", (r.get("catalog_l1"), r.get("catalog_l2"), r.get("catalog_l3")))

# ---- supporting evidence pools ----
def mp(r):
    l1 = (r.get("aim_l1") or "").strip()
    l2 = (r.get("aim_l2") or "").strip()
    l3 = (r.get("aim_l3") or "").strip()
    f1 = (r.get("aim_l1_fixed") or "").strip()
    f2 = (r.get("aim_l2_fixed") or "").strip()
    if f1 not in PH:
        l1 = f1
    if f2 not in PH:
        l2 = f2
    return l1, l2, l3


M_by_desc = defaultdict(list)
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        M_by_desc[(r.get("description") or "").strip()].append(r)

C_by_desc = defaultdict(list)
with (D / "aim_pn_classification_20260920.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        C_by_desc[(r.get("description_norm") or "").strip()].append(r)

print("\n--- per PN: unanimity of aim_demand_type, aim_core_noncore, cat path ---")
for pn in pns:
    desc = (info[pn]["Description"] or "").strip()
    mrows = [r for r in M_by_desc.get(desc, []) if all(x and x not in PH for x in mp(r))]
    crows = C_by_desc.get(desc, [])
    dt = Counter((r.get("aim_demand_type") or "").strip() for r in mrows)
    cn = Counter((r.get("aim_core_noncore") or "").strip() for r in mrows)
    cat = Counter(
        ((r.get("catalog_l1") or "").strip(), (r.get("catalog_l2") or "").strip(),
         (r.get("catalog_l3") or "").strip())
        for r in crows if (r.get("catalog_l1") or "").strip()
    )
    pms = Counter((r.get("cat_pms_flag") or "").strip() for r in crows if (r.get("catalog_l1") or "").strip())
    print(f"\n{pn} | {desc}")
    print(f"   master rows usable: {len(mrows)}  demand_type {dt.most_common(4)}  core {cn.most_common(4)}")
    print(f"   classification rows: {len(crows)}  cat {cat.most_common(3)}  pms {pms.most_common(3)}")
