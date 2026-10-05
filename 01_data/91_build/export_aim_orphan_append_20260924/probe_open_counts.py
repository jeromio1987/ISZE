# -*- coding: utf-8 -*-
"""Read-only: the open count on the IE40 price list, before and after, on both surfaces.

  * the main parts table (aim_master_v2.csv)
  * the published pair that Power BI loads (AIM_Master_PN_Categories_Figkey_*.csv)
"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
EQ = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"
BEFORE = DER / "aim_master_v2.csv.bak_pre_orphan_append_20260924_170151"


def s(v):
    return "" if v is None else str(v).strip()


def cls(v):
    v = s(v)
    if v and not v.lower().startswith("unknown"):
        return "real"
    if v.lower().startswith("unknown"):
        return "marker"
    return "blank"


q_pns = []
with (EQ / "queue.csv").open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        k = s(r["pn"]).upper()
        if k not in q_pns:
            q_pns.append(k)
print(f"queue unique part numbers: {len(q_pns)}")


def survey(path: Path, label: str):
    rows = {}
    with path.open(encoding="utf-8-sig", newline="") as fh:
        rdr = csv.DictReader(fh)
        for r in rdr:
            rows[s(r.get("part_number")).upper()] = r
    on = [p for p in q_pns if p in rows]
    off = [p for p in q_pns if p not in rows]
    fixed = Counter()
    raw = Counter()
    for p in on:
        r = rows[p]
        fixed[cls(r.get("aim_l1_fixed") or r.get("aim_l1"))] += 1
        raw[cls(r.get("aim_l1") or r.get("aim_level_1"))] += 1
    print(f"\n{label}")
    print(f"   part numbers present : {len(on)}")
    print(f"   fixed-then-raw       : {dict(fixed)}")
    print(f"   aim_l1 alone         : {dict(raw)}")
    print(f"   no row at all        : {len(off)}")
    print(f"   still open           : {fixed['marker'] + fixed['blank'] + len(off)}")
    return fixed, raw, off


survey(BEFORE, "BEFORE  main parts table (backup 17:01:51)")
survey(DER / "aim_master_v2.csv", "AFTER   main parts table (now)")
survey(DER / "AIM_Master_PN_Categories_Figkey_20260924.csv",
       "AFTER   published pair csv 20260924 (not rebuilt yet)")
survey(DER / "AIM_Master_PN_Categories_Figkey_20260921.csv",
       "        published pair csv 20260921")
