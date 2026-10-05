# -*- coding: utf-8 -*-
"""Decide an AIM path per PN for the 44, with the evidence printed, and write a decision CSV."""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
T = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"
A = ROOT / "01_data" / "91_build" / "_tmp_apply_export_pr00_20260924"

not_in_master = [
    l.strip() for l in (A / "carried_out_not_in_master.txt").read_text().splitlines() if l.strip()
]
info: dict[str, dict] = {}
with (T / "tierA_audited.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        if r["pn"] in not_in_master:
            info[r["pn"]] = r

PH = {"", "Unknown", "Unknown Review", "Not on AIM spine", "nan", "None", "To Review",
      "Unclassified"}


def master_path(r):
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


def cls_aim_path(r):
    return (
        (r.get("aim_l1_fixed") or "").strip(),
        (r.get("aim_l2_fixed") or "").strip(),
        (r.get("aim_l3_fixed") or "").strip(),
    )


def cls_cat_path(r):
    return (
        (r.get("catalog_l1") or "").strip(),
        (r.get("catalog_l2") or "").strip(),
        (r.get("catalog_l3") or "").strip(),
    )


M_by_desc = defaultdict(list)
M_by_fig = defaultdict(list)
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        p = master_path(r)
        if all(x and x not in PH for x in p):
            M_by_desc[(r.get("description") or "").strip()].append(p)
            fk = (r.get("fig_key") or "").strip()
            if fk:
                M_by_fig[fk].append(p)

C_aim_by_desc = defaultdict(list)
C_cat_by_desc = defaultdict(list)
C_aim_by_fig = defaultdict(list)
C_cat_by_fig = defaultdict(list)
with (D / "aim_pn_classification_20260920.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        pa = cls_aim_path(r)
        pc = cls_cat_path(r)
        dn = (r.get("description_norm") or "").strip()
        fk = (r.get("fig_key") or "").strip()
        if all(x and x not in PH for x in pa):
            C_aim_by_desc[dn].append(pa)
            if fk:
                C_aim_by_fig[fk].append(pa)
        if all(pc):
            C_cat_by_desc[dn].append(pc)
            if fk:
                C_cat_by_fig[fk].append(pc)

rows_out = []
for pn in not_in_master:
    t = info[pn]
    desc = (t["Description"] or "").strip()
    fig = (t["fig_key"] or "").strip()
    md = Counter(M_by_desc.get(desc, []))
    cd = Counter(C_aim_by_desc.get(desc, []))
    ccat = Counter(C_cat_by_desc.get(desc, []))
    mf = Counter(M_by_fig.get(fig, []))
    cf = Counter(C_aim_by_fig.get(fig, []))
    cfc = Counter(C_cat_by_fig.get(fig, []))
    rows_out.append(
        {
            "pn": pn,
            "description": desc,
            "fig_key": fig,
            "list_eur": t.get("list_eur"),
            "d_l1": t.get("d_l1"),
            "master_desc": json.dumps(md.most_common(4)),
            "cls_aim_desc": json.dumps(cd.most_common(4)),
            "cls_cat_desc": json.dumps(ccat.most_common(4)),
            "master_fig": json.dumps(mf.most_common(4)),
            "cls_aim_fig": json.dumps(cf.most_common(4)),
            "cls_cat_fig": json.dumps(cfc.most_common(4)),
        }
    )

with (A / "decision_evidence_44.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows_out[0].keys()))
    w.writeheader()
    # sort by list price desc for readability of the big tickets first
    for r in sorted(rows_out, key=lambda x: -float(x["list_eur"] or 0)):
        w.writerow(r)

for r in sorted(rows_out, key=lambda x: -float(x["list_eur"] or 0)):
    print(f"\n### {r['pn']} | {r['description']} | EUR {r['list_eur']} | fig {r['fig_key']} | d_l1 {r['d_l1']}")
    print(f"   master_desc  {r['master_desc']}")
    print(f"   cls_aim_desc {r['cls_aim_desc']}")
    print(f"   cls_cat_desc {r['cls_cat_desc']}")
    print(f"   master_fig   {r['master_fig']}")
    print(f"   cls_aim_fig  {r['cls_aim_fig']}")
    print(f"   cls_cat_fig  {r['cls_cat_fig']}")
print("\nwrote", A / "decision_evidence_44.csv")
