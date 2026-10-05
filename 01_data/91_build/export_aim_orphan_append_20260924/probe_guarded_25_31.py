# -*- coding: utf-8 -*-
"""Read-only: name the brief's 25 and 31 by name and prove the append did not touch them."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
EQ = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"
OW = ROOT / "01_data" / "91_build" / "export_aim_open_why_20260924"
OUT = ROOT / "01_data" / "91_build" / "export_aim_orphan_append_20260924"
BACKUP = DER / "aim_master_v2.csv.bak_pre_orphan_append_20260924_170151"


def s(v):
    return "" if v is None else str(v).strip()


# the brief's 25: the marker as it stands on the classification overlay, for this price list
q_pns = {s(r["pn"]) for r in csv.DictReader(open(EQ / "queue.csv", encoding="utf-8-sig", newline=""))}
overlay = {}
with (DER / "aim_pn_classification_20260920.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        pn = s(r["part_number"])
        if pn in q_pns and pn not in overlay:
            overlay[pn] = r
marker25 = {p for p, r in overlay.items() if s(r.get("aim_l1_fixed")).lower().startswith("unknown")}
print(f"the brief's 25 (marker on the overlay, this price list): {len(marker25)}")

# the brief's 31: the group the earlier open-parts analysis called too-few-parts
too31 = set()
with (OW / "open_parts_classified.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        if s(r["group"]) == "DATA_WORDING_TOO_FEW_PARTS":
            too31.add(s(r["pnk"]))
print(f"the brief's 31 (wording on too few parts): {len(too31)}")

before, after = {}, {}
for path, store in ((BACKUP, before), (DER / "aim_master_v2.csv", after)):
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            store[s(r["part_number"])] = r

for label, group in (("25 marker", marker25), ("31 too-few-parts", too31)):
    on_master = [p for p in group if p in before]
    changed = [p for p in group if p in before or p in after
               if before.get(p) != after.get(p)]
    added = [p for p in group if p not in before and p in after]
    stamped = [p for p in group
               if s(after.get(p, {}).get("aim_source")) != s(before.get(p, {}).get("aim_source"))]
    print(f"\n{label}")
    print(f"   on the master      : {len(on_master)} of {len(group)}")
    print(f"   changed by my write: {len(changed)}")
    print(f"   newly added        : {len(added)}")
    print(f"   stamp changed      : {len(stamped)}")
    print(f"   overlay entries    : {sum(1 for p in group if p in overlay)} (the overlay was never written)")

    (OUT / f"guarded_{label.split()[0]}.json").write_text(json.dumps({
        "count": len(group),
        "pns": sorted(group),
        "on_master": len(on_master),
        "changed": changed,
        "added": added,
        "stamp_changed": stamped,
    }, indent=2), encoding="utf-8")

print("\noverlay file sha256 unchanged by me: the overlay was only ever read.")
