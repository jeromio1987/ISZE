# -*- coding: utf-8 -*-
"""Read-only probe: is the rebuilt pair actually carrying the new master values?"""
import csv
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
F = ROOT / "01_data" / "91_build" / "export_aim_fill_20260924"
MASTER = D / "aim_master_v2.csv"
CSV24 = D / "AIM_Master_PN_Categories_Figkey_20260924.csv"
XLSX24 = D / "AIM_Master_PN_Categories_Figkey_20260924.xlsx"

for p in (MASTER, CSV24, XLSX24,
          D / "aim_master_v2.csv.bak_pre_export_fill_20260924_140856"):
    st = p.stat()
    print(f"{p.name:70} {st.st_size:>12,}  mtime {datetime.fromtimestamp(st.st_mtime)}")

with (F / "decision_164_final.csv").open(encoding="utf-8-sig", newline="") as fh:
    dec = [d for d in csv.DictReader(fh) if d["chosen_l1"]]
sample = {d["pn"]: d for d in dec}

print("\nmaster rows now:")
m = {}
with MASTER.open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        if r["part_number"] in sample:
            m[r["part_number"]] = r
for pn in list(sample)[:5]:
    r = m[pn]
    print(f"  {pn} aim={r['aim_l1']}/{r['aim_l2']}/{r['aim_l3']} src={r['aim_source']} changed={r['aim_changed']}")

print("\npair rows now:")
n = 0
seen = 0
with CSV24.open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        n += 1
        if r["part_number"] in sample:
            seen += 1
            if seen <= 5:
                print(f"  {r['part_number']} aim={r['aim_level_1']}/{r['aim_level_2']}/{r['aim_level_3']} "
                      f"src={r['aim_source']} desc={r['description'][:24]!r} desc_src={r['description_source']}")
print(f"  pair rows {n} | of the 162 seen {seen}")
