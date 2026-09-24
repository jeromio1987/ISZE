# -*- coding: utf-8 -*-
"""Final decision for the 44: chosen AIM path + proof the leaf already exists on the master.

Rule applied (step 6a): the exact description's own AIM path, where master + classified
workbook agree on ONE full path with >= 3 supporting parts. Figure key is used only as a
veto (step 6b) and never as the source.
Writes decision_44_final.csv. Read-only against the master.
"""
from __future__ import annotations

import csv
import json
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
T = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"
A = ROOT / "01_data" / "91_build" / "_tmp_apply_export_pr00_20260924"
OUT = ROOT / "01_data" / "91_build" / "export_aim_append_20260924"
PH = {"", "Unknown", "Unknown Review", "Not on AIM spine", "nan", "None", "To Review",
      "Unclassified"}

pns = [l.strip() for l in (A / "carried_out_not_in_master.txt").read_text().splitlines() if l.strip()]
info = {}
with (T / "tierA_audited.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        if r["pn"] in pns:
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


master_leaves = set()           # every (L1,L2,L3) that exists on the master
master_leaf_rows = Counter()
M_desc = defaultdict(list)
M_fig = defaultdict(list)
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        p = mp(r)
        if all(x and x not in PH for x in p):
            master_leaves.add(p)
            master_leaf_rows[p] += 1
            M_desc[(r.get("description") or "").strip()].append(p)
            fk = (r.get("fig_key") or "").strip()
            if fk:
                M_fig[fk].append(p)

C_desc = defaultdict(list)
C_fig = defaultdict(list)
with (D / "aim_pn_classification_20260920.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        pa = ((r.get("aim_l1_fixed") or "").strip(), (r.get("aim_l2_fixed") or "").strip(),
              (r.get("aim_l3_fixed") or "").strip())
        if all(x and x not in PH for x in pa):
            dn = (r.get("description_norm") or "").strip()
            C_desc[dn].append(pa)
            fk = (r.get("fig_key") or "").strip()
            if fk:
                C_fig[fk].append(pa)

decisions = []
problems = []
for pn in pns:
    t = info[pn]
    desc = (t["Description"] or "").strip()
    fig = (t["fig_key"] or "").strip()
    pool = Counter(M_desc.get(desc, [])) + Counter(C_desc.get(desc, []))
    strong = {k: v for k, v in pool.items() if v >= 3}
    if len(strong) != 1:
        problems.append((pn, desc, "description evidence not single+strong", pool.most_common(4)))
        continue
    (path, support), = strong.items()
    n_master = Counter(M_desc.get(desc, []))[path]
    n_class = Counter(C_desc.get(desc, []))[path]
    exists = path in master_leaves

    # figure-key veto (never the source)
    fk_paths = Counter(M_fig.get(fig, [])) + Counter(C_fig.get(fig, []))
    fk_top = fk_paths.most_common(1)[0] if fk_paths else None
    fk_disagrees = bool(fk_top) and fk_top[0] != path

    decisions.append({
        "pn": pn,
        "description": desc,
        "fig_key": fig,
        "list_eur": t["list_eur"],
        "chosen_l1": path[0],
        "chosen_l2": path[1],
        "chosen_l3": path[2],
        "support_total": support,
        "support_master": n_master,
        "support_classified_workbook": n_class,
        "leaf_exists_on_master": exists,
        "master_leaf_row_count": master_leaf_rows[path],
        "fig_key_top_path": "" if not fk_top else " | ".join(fk_top[0]),
        "fig_key_n": 0 if not fk_top else fk_top[1],
        "fig_key_disagrees": fk_disagrees,
        "evidence": "description agreement (master + classified workbook)",
    })
    if not exists:
        problems.append((pn, desc, "chosen path is NOT an existing master leaf", path))

with (OUT / "decision_44_final.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(decisions[0].keys()))
    w.writeheader()
    w.writerows(decisions)

print(f"decisions: {len(decisions)} of 44   problems: {len(problems)}")
print("\nall chosen paths exist as live master leaves:",
      all(d["leaf_exists_on_master"] for d in decisions))
print("any figure key that disagrees with the chosen path:",
      [d["pn"] for d in decisions if d["fig_key_disagrees"]] or "none")

print("\n--- the chosen paths, counted ---")
for k, n in Counter((d["chosen_l1"], d["chosen_l2"], d["chosen_l3"]) for d in decisions).most_common():
    print(f"  {n:>3}  {k}")

print("\n--- minimum support ---")
print("min support total:", min(d["support_total"] for d in decisions))
print("rows carried by the master alone (support_master >= 3):",
      sum(1 for d in decisions if d["support_master"] >= 3))
print("rows that needed the classified workbook to reach 3:",
      sum(1 for d in decisions if d["support_master"] < 3))

print("\n--- problems ---")
for p in problems:
    print("  ", p)

for d in sorted(decisions, key=lambda x: -float(x["list_eur"])):
    print(f"{d['pn']:12} {d['description'][:32]:32} -> {d['chosen_l1']} > {d['chosen_l2']} > {d['chosen_l3']}"
          f"   [m{d['support_master']}+c{d['support_classified_workbook']}]")
