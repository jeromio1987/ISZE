# -*- coding: utf-8 -*-
"""Read-only: how the 99 open parts (43 + 25 + 31) are counted, and proof the 25 and the 31
were not touched by the orphan append."""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
EQ = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"
OUT = ROOT / "01_data" / "91_build" / "export_aim_orphan_append_20260924"
BACKUP = DER / "aim_master_v2.csv.bak_pre_orphan_append_20260924_170151"


def s(v):
    return "" if v is None else str(v).strip()


def fam(*vals):
    """real if any value is a real family; marker if any says Unknown; else blank."""
    saw_marker = False
    for v in vals:
        v = s(v)
        if not v:
            continue
        if v.lower().startswith("unknown"):
            saw_marker = True
        else:
            return "real"
    return "marker" if saw_marker else "blank"


q_pns = []
with (EQ / "queue.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        k = s(r["pn"])
        if k not in q_pns:
            q_pns.append(k)

master_before = {}
with BACKUP.open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        master_before[s(r["part_number"])] = r
master_now = {}
with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        master_now[s(r["part_number"])] = r

overlay = {}
with (DER / "aim_pn_classification_20260920.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        pn = s(r["part_number"])
        if pn not in overlay:
            overlay[pn] = r


def classify(pn, master):
    m = master.get(pn)
    o = overlay.get(pn)
    if m is None:
        return "no_row"
    vals = []
    if m:
        vals += [m.get("aim_l1_fixed"), m.get("aim_l1")]
    if o:
        vals += [o.get("aim_l1_fixed"), o.get("aim_l1")]
    return fam(*vals)


before = Counter(classify(p, master_before) for p in q_pns)
after = Counter(classify(p, master_now) for p in q_pns)
print("queue unique part numbers:", len(q_pns))
print("BEFORE  master+overlay:", dict(before))
print("AFTER   master+overlay:", dict(after))

# the brief's split
marker25 = [p for p in q_pns
            if classify(p, master_before) == "marker"]
blank31 = [p for p in q_pns
           if classify(p, master_before) == "blank"]
norow = [p for p in q_pns if classify(p, master_before) == "no_row"]
print(f"\nbefore: no row {len(norow)} | marker {len(marker25)} | blank/wording {len(blank31)}"
      f" | real {before['real']} | total {len(norow)+len(marker25)+len(blank31)+before['real']}")

# who are the blanks - on master or only on the overlay?
mb = sum(1 for p in blank31 if p in master_before)
ob = sum(1 for p in blank31 if p not in master_before and p in overlay)
print(f"   of the blank group: {mb} have a master row, {ob} exist only on the overlay")

touched = [p for p in marker25 + blank31
           if master_now.get(p) != master_before.get(p) or p not in master_now]
print(f"\nmarker+blank rows that my append changed: {len(touched)}")
stamps = {s(d.get("aim_source")) for d in master_now.values()}
newstamped = [p for p in marker25 + blank31
              if s(master_now.get(p, {}).get("aim_source")) in stamps
              and s(master_now.get(p, {}).get("aim_source")) != s(master_before.get(p, {}).get("aim_source"))]
print(f"marker+blank rows that gained a new stamp: {len(newstamped)}")

(OUT / "open_split_before_after.json").write_text(json.dumps({
    "queue_pn": len(q_pns),
    "before": dict(before),
    "after": dict(after),
    "no_row_before": len(norow),
    "marker_before": len(marker25),
    "blank_before": len(blank31),
    "blank_on_master": mb,
    "blank_overlay_only": ob,
    "guarded_rows_changed": touched,
    "guarded_rows_new_stamp": newstamped,
}, indent=2), encoding="utf-8")
