# -*- coding: utf-8 -*-
"""Read-only probe 3: where could "819" have come from?

Searches the read-only files in scope for a set of exactly 819 marker rows, so the
report names a source instead of guessing. Touches nothing (no EPC files).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
EQ = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"
TIER = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"

MARK = {"unknown", "unknown review", "to review", "unclassified"}


def bl(s):
    return (s or "").strip()


def is_marker(s):
    t = bl(s).lower()
    return t in MARK or t.startswith("unknown")


def scan(path: Path, cols_hint=("aim",), limit=400000):
    if not path.exists():
        print(f"  {path.name:44s} MISSING")
        return
    try:
        with path.open(encoding="utf-8-sig", newline="") as fh:
            rd = csv.DictReader(fh)
            hdr = [c for c in (rd.fieldnames or [])]
            aimcols = [c for c in hdr if any(h in c.lower() for h in cols_hint)]
            pncol = next((c for c in hdr if c.lower() in
                          ("pn", "pnk", "part_number", "part no", "newest p/n")), None)
            n = 0
            marker_pns = set()
            for r in rd:
                n += 1
                if n > limit:
                    break
                vals = [r.get(c) for c in aimcols] or [v for v in r.values()]
                if any(is_marker(v) for v in vals):
                    marker_pns.add(bl(r.get(pncol)) if pncol else "")
            print(f"  {path.name:44s} rows={n:>7d} aimcols={len(aimcols):>2d} "
                  f"marker_rows={len(marker_pns):>6d}")
    except Exception as e:  # noqa: BLE001
        print(f"  {path.name:44s} ERROR {type(e).__name__}: {e}")


print("Scanning read-only files in scope for a marker set of 819")
print("")
for f in [
    EQ / "open_worklist_20260924.csv",
    EQ / "classified.csv",
    EQ / "still_unknown.csv",
    EQ / "eq_hits_review_20260924.csv",
    EQ / "queue.csv",
    TIER / "tierA_audited.csv",
    DER / "aim_pn_classification_20260920.csv",
    DER / "AIM_Master_PN_Categories_Figkey_20260924.csv",
]:
    scan(f)

print("")
print("--- overlay: exact marker split vs master ---")
ov = {}
with (DER / "aim_pn_classification_20260920.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        ov[bl(r["part_number"]).upper()] = r

pair = {}
with (DER / "AIM_Master_PN_Categories_Figkey_20260924.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        pair[bl(r["part_number"]).upper()] = r

WHY = ROOT / "01_data" / "91_build" / "export_aim_open_why_20260924"
opn = []
with (WHY / "open_parts_classified.csv").open(encoding="utf-8-sig", newline="") as fh:
    opn = [bl(r["pnk"]).upper() for r in csv.DictReader(fh)]

master = {}
with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        master[bl(r["part_number"])] = r

A = [p for p in opn if p in master and is_marker(master[p]["aim_l1"])]
B = [p for p in opn if p in ov and is_marker(ov[p]["aim_l1_fixed"])]
C = [p for p in opn if p in pair and is_marker(pair[p]["aim_level_1"])]
print(f"  master aim_l1 marker        : {len(A)}")
print(f"  overlay aim_l1_fixed marker : {len(B)}")
print(f"  pair aim_level_1 marker     : {len(C)}")
print(f"  master minus overlay        : {len(set(A)-set(B))}")
print(f"  the 26, has_catalogue_node values: "
      f"{sorted(set(bl(master[p].get('has_catalogue_node')) for p in set(A)-set(B)))}")
print(f"  the 26, aim_source values: "
      f"{sorted(set(bl(master[p].get('aim_source')) for p in set(A)-set(B)))}")
