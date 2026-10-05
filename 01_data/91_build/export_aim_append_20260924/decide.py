# -*- coding: utf-8 -*-
"""Decide which of the 44 have a single >3-support path by exact description, and which are contested."""
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

not_in_master = [
    l.strip() for l in (A / "carried_out_not_in_master.txt").read_text().splitlines() if l.strip()
]
info = {}
with (T / "tierA_audited.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        if r["pn"] in not_in_master:
            info[r["pn"]] = r


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


M_desc = defaultdict(list)
M_fig = defaultdict(list)
M_desc_all = defaultdict(list)
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        desc = (r.get("description") or "").strip()
        p = mp(r)
        M_desc_all[desc].append(p)
        if all(x and x not in PH for x in p):
            M_desc[desc].append(p)
            fk = (r.get("fig_key") or "").strip()
            if fk:
                M_fig[fk].append(p)

C_desc = defaultdict(list)
C_desc_cat = defaultdict(list)
C_fig_cat = defaultdict(list)
with (D / "aim_pn_classification_20260920.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        dn = (r.get("description_norm") or "").strip()
        pa = ((r.get("aim_l1_fixed") or "").strip(), (r.get("aim_l2_fixed") or "").strip(),
              (r.get("aim_l3_fixed") or "").strip())
        if all(x and x not in PH for x in pa):
            C_desc[dn].append(pa)
        pc = ((r.get("catalog_l1") or "").strip(), (r.get("catalog_l2") or "").strip(),
              (r.get("catalog_l3") or "").strip())
        if all(pc):
            C_desc_cat[dn].append(pc)
            fk = (r.get("fig_key") or "").strip()
            if fk:
                C_fig_cat[fk].append(pc)

auto, contested = [], []
for pn in not_in_master:
    t = info[pn]
    desc = (t["Description"] or "").strip()
    fig = (t["fig_key"] or "").strip()
    pool = Counter(M_desc.get(desc, [])) + Counter(C_desc.get(desc, []))
    strong = {k: v for k, v in pool.items() if v >= 3}
    if len(strong) == 1:
        auto.append((pn, desc, next(iter(strong)), strong[next(iter(strong))]))
    else:
        contested.append(pn)

print(f"AUTO by exact-description agreement (single path >=3): {len(auto)}")
for pn, desc, path, n in auto:
    print(f"  {pn:12} {desc[:34]:34} -> {path}  (support {n})")

print(f"\nCONTESTED / no single path >=3: {len(contested)}")
for pn in contested:
    t = info[pn]
    desc = (t["Description"] or "").strip()
    fig = (t["fig_key"] or "").strip()
    print(f"\n  {pn} | {desc} | fig {fig}")
    print(f"    master_desc(usable)   {Counter(M_desc.get(desc, [])).most_common(6)}")
    print(f"    master_desc(all)      {Counter(M_desc_all.get(desc, [])).most_common(6)}")
    print(f"    classif_aim_desc      {Counter(C_desc.get(desc, [])).most_common(6)}")
    print(f"    classif_cat_desc      {Counter(C_desc_cat.get(desc, [])).most_common(6)}")
    print(f"    master_fig            {Counter(M_fig.get(fig, [])).most_common(6)}")
    print(f"    classif_cat_fig       {Counter(C_fig_cat.get(fig, [])).most_common(6)}")
