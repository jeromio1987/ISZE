# -*- coding: utf-8 -*-
"""Read-only probe: what the current 20260924 pair says for a sample of the 164, and how the
rebuild builder's description coalesce behaves for them today."""
import csv
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
A = ROOT / "01_data" / "91_build" / "_tmp_apply_export_pr00_20260924"
F = ROOT / "01_data" / "91_build" / "export_aim_fill_20260924"
CSV = D / "AIM_Master_PN_Categories_Figkey_20260924.csv"

with (F / "decision_164_final.csv").open(encoding="utf-8-sig", newline="") as fh:
    dec = list(csv.DictReader(fh))
placed = [d["pn"] for d in dec if d["chosen_l1"]]
sample = placed[:6]

want = set(placed) | set(d["pn"] for d in dec if not d["chosen_l1"])
got = {}
n = 0
with CSV.open(encoding="utf-8-sig", newline="") as fh:
    rd = csv.DictReader(fh)
    print("pair columns:", rd.fieldnames)
    for r in rd:
        n += 1
        if r["part_number"] in want:
            got[r["part_number"]] = r
print("pair rows:", n)
print("of the 164 found in the current pair:", len(got))
for pn in sample:
    r = got[pn]
    print(f"  {pn} | desc={r['description'][:30]!r} | src={r['description_source']} | "
          f"aim={r['aim_level_1']}/{r['aim_level_2']}/{r['aim_level_3']} | aim_src={r['aim_source']}")

print("\ncheck the 44 appended earlier are in this pair with their stamp:")
notin = [l.strip() for l in (A / "carried_out_not_in_master.txt").read_text().splitlines() if l.strip()]
c44 = 0
with CSV.open(encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        if r["part_number"] in set(notin):
            if r["aim_source"] == "export_pr00_20260924":
                c44 += 1
print(f"  {c44}/44 carry the append stamp in the current pair")
print("\ncurrent aim_source distribution among the 164 in the pair:")
print(" ", Counter((got[p]["aim_source"] or "").strip() for p in got if p in set(placed)).most_common(5))
