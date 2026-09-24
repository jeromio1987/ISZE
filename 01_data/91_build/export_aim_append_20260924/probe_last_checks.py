# -*- coding: utf-8 -*-
"""Read-only: last checks before writing."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
A = ROOT / "01_data" / "91_build" / "_tmp_apply_export_pr00_20260924"

pns = [l.strip() for l in (A / "carried_out_not_in_master.txt").read_text().splitlines() if l.strip()]

# 1. is the master sorted by part_number, and where do prior appends sit?
rows = []
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for i, r in enumerate(csv.DictReader(fh)):
        rows.append(r)
pns_col = [r["part_number"] for r in rows]
print("first 5 PNs :", pns_col[:5])
print("last 8 PNs  :", pns_col[-8:])
print("is sorted ascending:", pns_col == sorted(pns_col))
for probe in ("5874123331", "1212350110", "0811230200"):
    idx = [i for i, p in enumerate(pns_col) if p == probe]
    print(f"prior-appended {probe}: index {idx} of {len(pns_col)}")
# monotonicity break points (where sorting stops holding)
breaks = [i for i in range(1, len(pns_col)) if pns_col[i] < pns_col[i - 1]]
print(f"sort-order breaks: {len(breaks)} | first 5: {breaks[:5]}")
if breaks:
    print("PN at first break:", pns_col[breaks[0] - 1], "->", pns_col[breaks[0]])

# 2. price class
pc = {}
p = D / "price_bp_weighted_compare_pn.csv"
if p.exists():
    with p.open(encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh)
        cols = rd.fieldnames
        for r in rd:
            pc[str(r.get("part_number") or "").strip()] = r
print("\nprice_bp_weighted_compare_pn cols:", cols[:10])
print("of the 44 in price file:", sorted(set(pns) & set(pc)))

# 3. jp cache: is the 4signal-added row there (i.e. do added rows get jp codes)?
jp = set()
jpp = D / "jp_codes_cache_20260920.csv"
if jpp.exists():
    with jpp.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            jp.add(str(r.get("pn") or "").strip())
print("\n5874123331 in jp cache:", "5874123331" in jp)
print("0811230200 in jp cache:", "0811230200" in jp)

# 4. near-miss keys: is any of the 44 already present under a different length/padding?
print("\nany of the 44 already in the master:", sorted(set(pns) & set(pns_col)))
sources = {}
with (A.parent / "export_aim_tiering_20260924" / "tierA_audited.csv").open(
        encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        if r["pn"] in pns:
            sources[r["pn"]] = r.get("pn_source")
print("source PN differs from row PN for:")
for k, v in sources.items():
    if v and v != k:
        print(f"   {k} <- {v}  | source PN on master: {v in set(pns_col)}")
print("\nany zero-padded variant of the 44 on the master:",
      sorted({p for p in pns if p.zfill(10) in set(pns_col)}))
