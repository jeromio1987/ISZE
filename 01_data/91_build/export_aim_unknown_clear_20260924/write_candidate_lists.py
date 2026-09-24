# -*- coding: utf-8 -*-
"""Read-only: write the two candidate lists so the count question can be settled.

Writes ONLY inside this folder. Touches no shared file.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
WHY = ROOT / "01_data" / "91_build" / "export_aim_open_why_20260924"
OUT = ROOT / "01_data" / "91_build" / "export_aim_unknown_clear_20260924"

MARK = {"unknown", "unknown review", "to review", "unclassified"}


def bl(s):
    return (s or "").strip()


def is_marker(s):
    t = bl(s).lower()
    return t in MARK or t.startswith("unknown")


opn = [bl(r["pnk"]).upper() for r in csv.DictReader(
    (WHY / "open_parts_classified.csv").open(encoding="utf-8-sig", newline=""))]

master = {}
with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        master[bl(r["part_number"])] = r

ov = {}
with (DER / "aim_pn_classification_20260920.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        ov[bl(r["part_number"]).upper()] = r

master_marker = [p for p in opn if p in master and any(
    is_marker(master[p].get(c)) for c in
    ("aim_l1", "aim_l2", "aim_l3", "aim_l1_fixed", "aim_l2_fixed"))]
overlay_marker = [p for p in master_marker if p in ov and any(
    is_marker(ov[p].get(c)) for c in ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"))]

OUT.mkdir(parents=True, exist_ok=True)
with (OUT / "candidate_819_overlay_set.csv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["part_number"])
    for p in overlay_marker:
        w.writerow([p])

with (OUT / "candidate_845_master_set.csv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["part_number"])
    for p in master_marker:
        w.writerow([p])

with (OUT / "candidate_26_not_in_overlay.csv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["part_number", "description", "aim_l1", "aim_l1_fixed", "fig_key", "has_catalogue_node"])
    for p in sorted(set(master_marker) - set(overlay_marker)):
        r = master[p]
        w.writerow([p, bl(r["description"]), bl(r["aim_l1"]), bl(r["aim_l1_fixed"]),
                    bl(r["fig_key"]), bl(r["has_catalogue_node"])])

print("overlay set (819):", len(overlay_marker))
print("master set  (845):", len(master_marker))
print("in master set only (26):", len(set(master_marker) - set(overlay_marker)))
print("wrote candidate_819_overlay_set.csv, candidate_845_master_set.csv, "
      "candidate_26_not_in_overlay.csv")
