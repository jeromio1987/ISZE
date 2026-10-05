# -*- coding: utf-8 -*-
"""Read-only: measure the would-be placement for the marker rows on the IE40 list.

This does NOT write to the master or the overlay. It answers, for the marker rows the
brief wants cleared, how many the wording rule would place — so the number is known
before any write is authorised.

Rule reused exactly as the two earlier write-backs describe it (derive_paths_164.py):
the part's exact description already means ONE full AIM path on the master, supported by
at least 3 master parts, with the figure key used only as a veto.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
WHY = ROOT / "01_data" / "91_build" / "export_aim_open_why_20260924"
EQ = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"
OUT = ROOT / "01_data" / "91_build" / "export_aim_unknown_clear_20260924"

PH = {"", "Unknown", "Unknown Review", "Not on AIM spine", "nan", "None", "To Review",
      "Unclassified"}
RESIDUAL = {"Maintenance Service", "Literature Marketing", "Tools Equipment",
            "Logistics Packaging", "Fluids Chemicals"}
CARVE = {
    "GASKET; CYL HD", "GASKET SET; ENG OVERHAUL", "LAMP ASM; HEAD", "LAMP ASM; RR COMB",
    "LAMP ASM; FRM COMB", "LAMP ASM; FRT COMB", "LAMP ASM; FOG", "LAMP ASM; SIDE COMB",
    "CYLINDER ASM; CLUTCH MASTER", "PUMP ASM; OIL,P/S",
}
LOG = []


def say(*p):
    line = " ".join(str(x) for x in p)
    print(line)
    LOG.append(line)


def bl(s):
    return (s or "").strip()


def norm_desc(s):
    return " ".join(bl(s).upper().split())


def is_marker(s):
    t = bl(s).lower()
    return t in {"unknown", "unknown review", "to review", "unclassified"} or t.startswith("unknown")


def mp(r):
    l1 = bl(r.get("aim_l1"))
    l2 = bl(r.get("aim_l2"))
    l3 = bl(r.get("aim_l3"))
    f1 = bl(r.get("aim_l1_fixed"))
    f2 = bl(r.get("aim_l2_fixed"))
    if f1 not in PH:
        l1 = f1
    if f2 not in PH:
        l2 = f2
    return l1, l2, l3


# ------------------------------------------------------------------ inputs
master = []
with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    master = list(csv.DictReader(fh))
say("master rows:", len(master))

by_pn = {bl(r["part_number"]): r for r in master}

# the open list, its reasons, and the wording the export carries
open_rows = []
with (WHY / "open_parts_classified.csv").open(encoding="utf-8-sig", newline="") as fh:
    open_rows = list(csv.DictReader(fh))

# export wording per part number (the queue carries the price extract Description)
que_desc = {}
with (EQ / "queue.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        que_desc.setdefault(bl(r["pn"]).upper(), bl(r["Description"]))

# ------------------------------------------------------------------ dictionary
M_desc = defaultdict(list)
M_fig = defaultdict(list)
master_leaves = Counter()
for r in master:
    p = mp(r)
    if all(x and x not in PH for x in p):
        master_leaves[p] += 1
        M_desc[norm_desc(r.get("description"))].append(p)
        fk = bl(r.get("fig_key"))
        if fk:
            M_fig[fk].append(p)
say("distinct master wordings with a usable path:", len(M_desc))

# ------------------------------------------------------------------ the marker set
marker_master = [p for p in (bl(x["pnk"]).upper() for x in open_rows)
                 if p in by_pn and any(is_marker(by_pn[p].get(c)) for c in
                                       ("aim_l1", "aim_l2", "aim_l3", "aim_l1_fixed", "aim_l2_fixed"))]
say("marker rows on the master for this list:", len(marker_master))

ov = {}
with (DER / "aim_pn_classification_20260920.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        ov.setdefault(bl(r["part_number"]).upper(), r)
marker_overlay = [p for p in marker_master
                  if p in ov and any(is_marker(ov[p].get(c)) for c in
                                     ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"))]
say("of those, also carrying a marker in the classification overlay:", len(marker_overlay))
say("in the master marker set but with NO overlay row:", len(set(marker_master) - set(marker_overlay)))

# ------------------------------------------------------------------ decide
placed, unplaced = [], []
for pn in marker_master:
    m = by_pn[pn]
    d = norm_desc(m.get("description")) or norm_desc(que_desc.get(pn, ""))
    pool = Counter(M_desc.get(d, []))
    strong = {k: v for k, v in pool.items() if v >= 3}
    fig = bl(m.get("fig_key"))
    fk_paths = Counter(M_fig.get(fig, []))
    fk_top = fk_paths.most_common(1)[0] if fk_paths else None

    if len(strong) != 1:
        unplaced.append((pn, d, "wording does not resolve to one path with 3+ master parts",
                         str(pool.most_common(3))))
        continue
    (path, sup), = strong.items()
    if fk_top and fk_top[0] != path:
        unplaced.append((pn, d, "figure key vetoes the wording's path",
                         f"{fk_top[0]} on {fk_top[1]}"))
        continue
    placed.append({"pn": pn, "description": d, "fig_key": fig,
                   "aim": list(path), "support_master": sup,
                   "residual_family": path[0] in RESIDUAL,
                   "carved_out": d in CARVE})

say("")
say("MEASURED, strict rule as the two earlier write-backs describe it")
say("  would be placed :", len(placed))
say("  left unplaced   :", len(unplaced))
say("")
say("  of the placed, on a residual bucket the rule normally refuses:",
    sum(1 for x in placed if x["residual_family"]))
say("  of the placed, on a wording the tiering study held back:",
    sum(1 for x in placed if x["carved_out"]))
say("  of the placed, in the overlay marker subset:", sum(1 for x in placed if x["pn"] in set(marker_overlay)))
say("")
say("  support distribution:", dict(sorted(Counter(
    x["support_master"] for x in placed).items())))
say("  min support:", min(x["support_master"] for x in placed))
say("  max support:", max(x["support_master"] for x in placed))
say("")
say("  chosen families:")
for k, n in Counter(x["aim"][0] for x in placed).most_common():
    say(f"     {n:>4}  {k}")
say("")
say("  unplaced reasons:")
for k, n in Counter(x[2] for x in unplaced).most_common():
    say(f"     {n:>4}  {k}")

OUT.mkdir(parents=True, exist_ok=True)
with (OUT / "candidate_845_decisions.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["part_number", "description", "fig_key", "aim_l1", "aim_l2", "aim_l3",
                "support_master", "residual_family", "carved_out", "outcome"])
    for x in placed:
        w.writerow([x["pn"], x["description"], x["fig_key"], *x["aim"], x["support_master"],
                    int(x["residual_family"]), int(x["carved_out"]), "would_place"])
    for pn, d, why, ev in unplaced:
        w.writerow([pn, d, "", "", "", "", "", "", "", "unplaced: " + why])

s = {
    "marker_master": len(marker_master),
    "marker_overlay": len(marker_overlay),
    "marker_master_only": len(set(marker_master) - set(marker_overlay)),
    "would_place": len(placed),
    "left_unplaced": len(unplaced),
    "placed_on_residual_bucket": sum(1 for x in placed if x["residual_family"]),
    "placed_on_carved_out_wording": sum(1 for x in placed if x["carved_out"]),
}
(OUT / "candidate_845_summary.json").write_text(json.dumps(s, indent=2), encoding="utf-8")
(OUT / "candidate_845_run.txt").write_text("\n".join(LOG) + "\n", encoding="utf-8")
say("")
say(json.dumps(s, indent=2))
say("wrote", OUT / "candidate_845_decisions.csv")
