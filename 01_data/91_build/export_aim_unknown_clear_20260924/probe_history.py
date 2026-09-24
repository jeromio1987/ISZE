# -*- coding: utf-8 -*-
"""Read-only probe 5: did any earlier master state hold 819 marker rows on this list?

Checks the pre-write backups for the IE40 open-list marker count, so the report can say
whether "819" is stale or simply read off a different file.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
WHY = ROOT / "01_data" / "91_build" / "export_aim_open_why_20260924"

MARK = {"unknown", "unknown review", "to review", "unclassified"}


def bl(s):
    return (s or "").strip()


def is_marker(s):
    t = bl(s).lower()
    return t in MARK or t.startswith("unknown")


opn = set()
with (WHY / "open_parts_classified.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        opn.add(bl(r["pnk"]).upper())
print("IE40 open-list part numbers:", len(opn))
print("")

cands = sorted(DER.glob("aim_master_v2.csv.bak_*"))
cands.append(DER / "aim_master_v2.csv")
for p in cands:
    try:
        n_rows = 0
        on_list_l1 = 0
        on_list_any = 0
        with p.open(encoding="utf-8", newline="") as fh:
            rd = csv.DictReader(fh)
            for r in rd:
                n_rows += 1
                if bl(r["part_number"]).upper() in opn:
                    if is_marker(r.get("aim_l1")):
                        on_list_l1 += 1
                    if any(is_marker(r.get(c)) for c in
                           ("aim_l1", "aim_l2", "aim_l3", "aim_l1_fixed", "aim_l2_fixed")):
                        on_list_any += 1
        print(f"  {p.name:62s} rows={n_rows:>7d} on_list_l1={on_list_l1:>5d} on_list_any={on_list_any:>5d}")
    except Exception as e:  # noqa: BLE001
        print(f"  {p.name:62s} ERROR {type(e).__name__}: {e}")
