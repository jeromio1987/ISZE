# -*- coding: utf-8 -*-
"""Read-only derivation of an AIM path per PN for the 44. Prints all evidence, decides nothing silently."""
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
assert len(info) == len(not_in_master)

PH = {"", "Unknown", "Unknown Review", "Not on AIM spine", "nan", "None", "To Review",
      "Unclassified"}


def master_path(r: dict) -> tuple[str, str, str]:
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


def cls_path(r: dict) -> tuple[str, str, str]:
    """AIM axis where the workbook carries it, else the catalogue axis."""
    a1 = (r.get("aim_l1_fixed") or "").strip()
    a2 = (r.get("aim_l2_fixed") or "").strip()
    a3 = (r.get("aim_l3_fixed") or "").strip()
    if a1 not in PH and a1 and a2 not in PH and a2 and a3 not in PH and a3:
        return a1, a2, a3
    return (
        (r.get("catalog_l1") or "").strip(),
        (r.get("catalog_l2") or "").strip(),
        (r.get("catalog_l3") or "").strip(),
    )


# ---- load master indexes ----
M_by_desc: dict[str, list] = defaultdict(list)
M_by_fig: dict[str, list] = defaultdict(list)
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        p = master_path(r)
        if all(p):
            M_by_desc[(r.get("description") or "").strip()].append(p)
            fk = (r.get("fig_key") or "").strip()
            if fk:
                M_by_fig[fk].append(p)

# ---- load classified indexes ----
C_by_desc: dict[str, list] = defaultdict(list)
C_by_fig: dict[str, list] = defaultdict(list)
with (D / "aim_pn_classification_20260920.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        p = cls_path(r)
        if all(p):
            C_by_desc[(r.get("description_norm") or "").strip()].append(p)
            fk = (r.get("fig_key") or "").strip()
            if fk:
                C_by_fig[fk].append(p)

result = {}
for pn in not_in_master:
    t = info[pn]
    desc = (t["Description"] or "").strip()
    fig = (t["fig_key"] or "").strip()
    md = M_by_desc.get(desc, [])
    cd = C_by_desc.get(desc, [])
    mf = M_by_fig.get(fig, [])
    cf = C_by_fig.get(fig, [])
    result[pn] = {
        "description": desc,
        "fig_key": fig,
        "d_l1": t.get("d_l1"),
        "master_desc_paths": Counter(md).most_common(6),
        "classified_desc_paths": Counter(cd).most_common(6),
        "master_fig_paths": Counter(mf).most_common(6),
        "classified_fig_paths": Counter(cf).most_common(6),
    }

    print("=" * 100)
    print(f"{pn}  |  {desc}  |  fig {fig}  |  d_l1 {t.get('d_l1')}  |  EUR {t.get('list_eur')}")
    print(f"  master  by description ({len(md)} rows): {Counter(md).most_common(4)}")
    print(f"  classif by description ({len(cd)} rows): {Counter(cd).most_common(4)}")
    print(f"  master  by figure key  ({len(mf)} rows): {Counter(mf).most_common(4)}")
    print(f"  classif by figure key  ({len(cf)} rows): {Counter(cf).most_common(4)}")

(A / "evidence_44.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print("\nwrote", A / "evidence_44.json")
