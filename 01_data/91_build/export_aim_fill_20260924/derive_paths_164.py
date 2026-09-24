# -*- coding: utf-8 -*-
"""Read-only derivation of an AIM path for each of the 164 PNs in would_land_free.txt.

Method is the same one used for the 44 (export_aim_append_20260924/finalise_decisions.py):
the exact description's own AIM path on the master, where the master (+ classified
workbook) agree on ONE full path with >= 3 supporting parts. The figure key is used
ONLY as a veto, never as the source.

Extra guard the brief adds for the 164: the supporting MASTER rows alone must agree on
one full path with >= 3 parts. The classified workbook may not carry a row over the bar.
This script measures both readings so the difference is visible.
"""
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
OUT = ROOT / "01_data" / "91_build" / "export_aim_fill_20260924"

PH = {"", "Unknown", "Unknown Review", "Not on AIM spine", "nan", "None", "To Review",
      "Unclassified"}

free = [l.strip() for l in (A / "would_land_free.txt").read_text().splitlines() if l.strip()]
blocked = [l.strip() for l in (A / "carried_out_blocked_precedence.txt").read_text().splitlines() if l.strip()]
notin = [l.strip() for l in (A / "carried_out_not_in_master.txt").read_text().splitlines() if l.strip()]
print(f"lists: free {len(free)} | blocked {len(blocked)} | not_in_master {len(notin)}")
assert len(set(free)) == len(free)
assert not (set(free) & set(blocked)), "guard: overlap between free and blocked"
assert not (set(free) & set(notin)), "guard: overlap between free and not_in_master"


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


def cls_path(r):
    a1 = (r.get("aim_l1_fixed") or "").strip()
    a2 = (r.get("aim_l2_fixed") or "").strip()
    a3 = (r.get("aim_l3_fixed") or "").strip()
    if a1 not in PH and a1 and a2 not in PH and a2 and a3 and a3 not in PH:
        return a1, a2, a3
    return ((r.get("catalog_l1") or "").strip(),
            (r.get("catalog_l2") or "").strip(),
            (r.get("catalog_l3") or "").strip())


# ---------------- master ----------------
master_rows = []
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    rd = csv.DictReader(fh)
    for r in rd:
        master_rows.append(r)
print(f"master rows {len(master_rows)}")
by_pn = {r["part_number"]: r for r in master_rows}
missing = [p for p in free if p not in by_pn]
print(f"free pns absent from master: {len(missing)} {missing[:5]}")

M_desc = defaultdict(list)
M_fig = defaultdict(list)
master_leaves = set()
master_leaf_rows = Counter()
for r in master_rows:
    p = mp(r)
    if all(x and x not in PH for x in p):
        master_leaves.add(p)
        master_leaf_rows[p] += 1
        M_desc[(r.get("description") or "").strip()].append(p)
        fk = (r.get("fig_key") or "").strip()
        if fk:
            M_fig[fk].append(p)

# ---------------- classified workbook ----------------
# The workbook carries TWO axes per row: an AIM axis (aim_l1_fixed/l2/l3) and the price
# list's catalogue axis (catalog_l1/l2/l3). Only the AIM axis is evidence about AIM. For
# the 164 every workbook row has an EMPTY AIM axis and only a catalogue node, so the
# catalogue axis must not be read as a competing AIM path. The 44 never hit this because
# none of them was in the workbook at all.
C_desc = defaultdict(list)
C_desc_cat = defaultdict(list)
C_fig = defaultdict(list)
C_fig_cat = defaultdict(list)
with (D / "aim_pn_classification_20260920.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        dn = (r.get("description_norm") or "").strip()
        pa = ((r.get("aim_l1_fixed") or "").strip(),
              (r.get("aim_l2_fixed") or "").strip(),
              (r.get("aim_l3_fixed") or "").strip())
        ca = ((r.get("catalog_l1") or "").strip(),
              (r.get("catalog_l2") or "").strip(),
              (r.get("catalog_l3") or "").strip())
        fk = (r.get("fig_key") or "").strip()
        if all(x and x not in PH for x in pa):
            C_desc[dn].append(pa)
            if fk:
                C_fig[fk].append(pa)
        if all(x and x not in PH for x in ca):
            C_desc_cat[dn].append(ca)
            if fk:
                C_fig_cat[fk].append(ca)

# ---------------- the export rows for the 164 ----------------
info = {}
with (T / "tierA_audited.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        if r["pn"] in set(free):
            info[r["pn"]] = r
print(f"of the 164 found in tierA_audited.csv: {len(info)}")

# The 164 master rows were written from the PR00 price list and carry NO description;
# their description lives on the export row only. So the join key for these is the
# export description, exactly as the 44 used tierA_audited.csv's own Description column.
print("master rows with an empty description:", sum(1 for p in free if not (by_pn[p].get("description") or "").strip()))
print("free rows carrying a catalogue node:", sum(1 for p in free if (by_pn[p].get("cat_l2") or "").strip()))
desc_mismatch = []
for pn in free:
    m_desc = (by_pn[pn].get("description") or "").strip()
    e_desc = (info.get(pn, {}).get("Description") or "").strip()
    if m_desc and m_desc != e_desc:
        desc_mismatch.append((pn, m_desc, e_desc))
print(f"master/export description conflicts (both present): {len(desc_mismatch)}")

# ---------------- decide ----------------
decisions = []
problems = []
for pn in free:
    t = info.get(pn)
    if t is None:
        problems.append((pn, "", "not in tierA_audited.csv", ""))
        continue
    # the description we trust is the export row's own (the master row is blank),
    # which is the same field the 44 were decided on
    desc = (t["Description"] or "").strip()
    fig = (t["fig_key"] or "").strip()
    m_pool = Counter(M_desc.get(desc, []))
    c_pool = Counter(C_desc.get(desc, []))
    pool = m_pool + c_pool
    strong = {k: v for k, v in pool.items() if v >= 3}
    m_strong = {k: v for k, v in m_pool.items() if v >= 3}

    if len(m_strong) != 1:
        problems.append((pn, desc,
                         "master support not single+strong",
                         "master=" + str(m_pool.most_common(4)) +
                         " | workbook_aim=" + str(c_pool.most_common(4))))
        continue
    (path, m_support), = m_strong.items()
    if len(strong) != 1 or next(iter(strong)) != path:
        # master says one thing and the workbook's AIM axis disagrees or adds a competing path
        problems.append((pn, desc,
                         "master path not the single combined path",
                         "master=" + str(m_pool.most_common(4)) +
                         " | workbook_aim=" + str(c_pool.most_common(4))))
        continue

    n_class = Counter(C_desc.get(desc, []))[path]
    n_cat = Counter(C_desc_cat.get(desc, []))[path]
    exists = path in master_leaves

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
        "support_total": pool[path],
        "support_master": m_support,
        "support_classified_workbook": n_class,
        "support_catalogue_axis": n_cat,
        "leaf_exists_on_master": exists,
        "master_leaf_row_count": master_leaf_rows[path],
        "fig_key_top_path": "" if not fk_top else " | ".join(fk_top[0]),
        "fig_key_n": 0 if not fk_top else fk_top[1],
        "fig_key_disagrees": fk_disagrees,
        "evidence": "description agreement (master, cross-checked vs classified workbook)",
        "unplaced_reason": "",
    })

for pn, desc, why, ev in problems:
    decisions.append({
        "pn": pn, "description": desc,
        "fig_key": (by_pn.get(pn, {}).get("fig_key") or "").strip(),
        "list_eur": (info.get(pn, {}).get("list_eur") or ""),
        "chosen_l1": "", "chosen_l2": "", "chosen_l3": "",
        "support_total": 0, "support_master": 0, "support_classified_workbook": 0,
        "leaf_exists_on_master": False, "master_leaf_row_count": 0,
        "fig_key_top_path": "", "fig_key_n": 0, "fig_key_disagrees": False,
        "evidence": ev, "unplaced_reason": why,
    })

placed = [d for d in decisions if d["chosen_l1"]]
unplaced = [d for d in decisions if not d["chosen_l1"]]

OUT.mkdir(parents=True, exist_ok=True)
with (OUT / "decision_164_final.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(decisions[0].keys()))
    w.writeheader()
    w.writerows(decisions)

print(f"\n=== RESULT ===\nplaced: {len(placed)}   unplaced: {len(unplaced)}")
print(f"all chosen paths are live master leaves: "
      f"{all(d['leaf_exists_on_master'] for d in placed)}")
print(f"figure keys that disagree with the chosen path: "
      f"{[d['pn'] for d in placed if d['fig_key_disagrees']] or 'none'}")
if placed:
    print(f"min master support: {min(d['support_master'] for d in placed)}")
    print(f"rows needing the workbook to reach 3: "
          f"{sum(1 for d in placed if d['support_master'] < 3)}")

print("\n--- chosen paths, counted ---")
for k, n in Counter((d["chosen_l1"], d["chosen_l2"], d["chosen_l3"])
                    for d in placed).most_common():
    print(f"  {n:>3}  {k}")

print("\n--- paths that agree with the price-list catalogue axis anyway ---")
cat_agree = sum(1 for d in placed if d["support_catalogue_axis"] > 0)
print(f"placed rows where the catalogue axis (where it exists) carries the same path: {cat_agree}")
print(f"of those, the catalogue axis disagrees on: "
      f"{sum(1 for d in placed if d['support_catalogue_axis'] == 0)}")

print("\n--- unplaced, with reasons ---")
for d in unplaced:
    print(f"  {d['pn']:12} {d['description'][:26]:26} {d['unplaced_reason']}")
    print(f"      {d['evidence']}")

print(f"\nwrote {OUT / 'decision_164_final.csv'}")
