# -*- coding: utf-8 -*-
"""Read-only: the final open count on the IE40 price list, using the brief's own three groups.

The brief names them as the earlier analysis did:
  43  no row on the main parts table at all
  25  carrying the 'Unknown' marker
  31  a row, but no usable family
Everything else on the list has a real family.
"""
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


q_pns = set()
with (EQ / "queue.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        q_pns.add(s(r["pn"]))

overlay = {}
with (DER / "aim_pn_classification_20260920.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        pn = s(r["part_number"])
        if pn in q_pns and pn not in overlay:
            overlay[pn] = r
marker25 = {p for p, r in overlay.items() if s(r.get("aim_l1_fixed")).lower().startswith("unknown")}

too31 = set()
with (OW / "open_parts_classified.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        if s(r["group"]) == "DATA_WORDING_TOO_FEW_PARTS":
            too31.add(s(r["pnk"]))


def load(p):
    d = {}
    with p.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            d[s(r["part_number"])] = r
    return d


before = load(BACKUP)
after = load(DER / "aim_master_v2.csv")


def real(r):
    """A real family anywhere the published file would read it."""
    for c in ("aim_l1_fixed", "aim_l1"):
        v = s(r.get(c))
        if v and not v.lower().startswith("unknown"):
            return True
    return False


out = {}
for label, store in (("before", before), ("after", after)):
    norow = [p for p in q_pns if p not in store]
    m25 = [p for p in marker25 if p in store and not real(store[p])]
    b31 = [p for p in too31 if p in store and not real(store[p])]
    others_blank = [p for p in q_pns
                    if p in store and not real(store[p])
                    and p not in set(marker25) and p not in too31]
    real_n = sum(1 for p in q_pns if p in store and real(store[p]))
    out[label] = {
        "no_row": len(norow), "marker_25": len(m25), "blank_31": len(b31),
        "other_blank": len(others_blank), "real": real_n,
        "total": len(q_pns),
        "open_brief_groups": len(norow) + len(m25) + len(b31),
    }
    print(f"\n{label}")
    print(f"   no row on the master           : {len(norow)}")
    print(f"   of the brief's 25, still open  : {len(m25)}")
    print(f"   of the brief's 31, still open  : {len(b31)}")
    print(f"   other blank rows not in either : {len(others_blank)} {others_blank[:12]}")
    print(f"   with a real family             : {real_n}")
    print(f"   total part numbers on the list : {len(q_pns)}")
    print(f"   open on the brief's three groups: {len(norow) + len(m25) + len(b31)}")
    print(f"   reconciles to the total        : "
          f"{len(norow) + len(m25) + len(b31) + len(others_blank) + real_n == len(q_pns)}")

(OUT / "open_count_final.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
