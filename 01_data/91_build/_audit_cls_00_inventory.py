#!/usr/bin/env python3
"""Audit step 0: inventory what we can test the classification against."""
from __future__ import annotations
import csv, collections, json
from pathlib import Path

D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
V2 = D / "aim_pn_classification_v2.csv"

rows = list(csv.DictReader(V2.open(encoding="utf-8", newline="")))
n = len(rows)
desc = sum(1 for r in rows if r["description_norm"].strip())
print(f"v2 rows {n:,}   with description {desc:,} ({100*desc/n:.1f}%)   without {n-desc:,}")
print()

bysrc = collections.defaultdict(lambda: [0, 0])
for r in rows:
    b = bysrc[r["workbook_source"] or "(blank)"]
    b[0] += 1
    if r["description_norm"].strip():
        b[1] += 1
print("description coverage by workbook_source")
for k, (t, d) in sorted(bysrc.items(), key=lambda kv: -kv[1][0]):
    print(f"  {k:<16} rows {t:>7,}  desc {d:>7,} ({100*d/t:5.1f}%)")
print()

print("L3 granularity inside the biggest L2 buckets")
for l2 in ["Body parts", "Electrical sensors", "Hardware", "Gaskets / seals",
           "Miscellaneous", "Hydraulic / mechanical", "Transmission parts",
           "Brake parts", "Filters"]:
    c = collections.Counter(r["catalog_l3"] for r in rows if r["catalog_l2"] == l2)
    print(f"\n* {l2}: {sum(c.values()):,} PNs in {len(c)} L3 nodes")
    for k, v in c.most_common(14):
        print(f"     {v:>7,}  {k}")
print()

# ---- what other derived files carry a description + euro?
print("=" * 70)
print("candidate description / euro sources in 00_derived")
for p in sorted(D.glob("*.csv")):
    try:
        with p.open(encoding="utf-8", newline="") as f:
            h = next(csv.reader(f))
    except Exception:
        continue
    hl = [c.lower() for c in h]
    has_desc = any("desc" in c or "text" in c or "name" in c for c in hl)
    has_pn = any(c in ("pn", "pn_norm", "part_number", "material") or "part" in c for c in hl)
    has_eur = any("eur" in c or "sales" in c or "value" in c for c in hl)
    if has_pn and (has_desc or has_eur):
        print(f"  {p.name:<56} desc={has_desc} eur={has_eur}")
        print(f"      {h}")
