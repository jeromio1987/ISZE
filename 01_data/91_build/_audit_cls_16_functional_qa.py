#!/usr/bin/env python3
"""Audit step 16: QA the third taxonomy (the Mar-2026 functional workbook).

It gets air filtration right, which corroborates finding 1 from an independent
build. But the 'PARTS FUNCTIONAL' sheet looked like it had been sorted by
description and then filled downwards, so gearbox bearings landed under
ENGINE > Cylinder Block & Crankshaft. Test that.
"""
from __future__ import annotations
import collections, csv, re
from pathlib import Path
import openpyxl

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
P = ISZE / "01_data" / "01_Pricing" / "ISZE_Parts_Sales_Classification_Mar2026_v2.xlsx"
D = ISZE / "01_data" / "00_derived"

wb = openpyxl.load_workbook(P, read_only=True, data_only=True)
ws = wb["PARTS FUNCTIONAL"]
it = ws.iter_rows(values_only=True)
next(it)
hdr = [("" if c is None else str(c).strip()) for c in next(it)]
i = {h: k for k, h in enumerate(hdr)}
recs = []
for row in it:
    if row is None or row[i["PN"]] is None:
        continue
    def g(c):
        v = row[i[c]]
        return "" if v is None else str(v).strip()
    recs.append({"pn": g("PN"), "desc": g("Description").upper(),
                 "l1": g("L1"), "l1c": g("L1 Category"),
                 "l2": g("L2"), "l2c": g("L2 Sub-Category")})
wb.close()
print(f"PARTS FUNCTIONAL rows: {len(recs):,}")

l1 = collections.Counter(f"{r['l1']} {r['l1c']}" for r in recs)
print(f"\nLevel 1 ({len(l1)} values):")
for k, v in sorted(l1.items()):
    print(f"  {v:>6}  {k}")

# ---- the bearing test
b = [r for r in recs if re.match(r"^BEARING", r["desc"])]
print(f"\nparts whose description starts with BEARING: {len(b):,}")
c = collections.Counter(f"{r['l1c']} > {r['l2c']}" for r in b)
for k, v in c.most_common(10):
    print(f"  {v:>5}  {k}")

# gearbox-specific bearings filed under the engine block
GEARBOX = [r"MAINSHAFT", r"COUNTER", r"INPUT ?SHAFT", r"OUTPUT", r"\bCLU\b",
           r"REVERSE", r"SYNCHRO", r"DIFF", r"AXLE ?SHAFT", r"PROPELLER"]
wrong = [r for r in b
         if any(re.search(p, r["desc"]) for p in GEARBOX)
         and r["l1c"] == "ENGINE"]
print(f"\ngearbox / axle bearings filed under ENGINE: {len(wrong):,}")
for r in wrong[:18]:
    print(f"    {r['pn']}  {r['desc'][:40]:<40} -> {r['l1c']} > {r['l2c']}")

# how concentrated is 01.01?
c0101 = [r for r in recs if r["l2"] == "01.01"]
nouns = collections.Counter(re.split(r"[;,]", r["desc"])[0].strip() for r in c0101)
print(f"\n'01.01 Cylinder Block & Crankshaft' holds {len(c0101):,} parts; top nouns:")
for k, v in nouns.most_common(10):
    print(f"    {v:>5}  {k}")

# ---- does it agree with the catalogue tree on air filtration?
print("\n" + "=" * 74)
print("CROSS-CHECK: the two taxonomies on engine air filtration")
spine = {r["pn"]: r for r in csv.DictReader(
    (D / "_audit_cls_spine.csv").open(encoding="utf-8", newline=""))}
af = [r for r in recs if r["l2c"].upper().startswith("AIR FILTER")]
print(f"functional workbook '05.02 Air Filter / Cleaner': {len(af)} parts")
agree = collections.Counter()
eur = collections.Counter()
for r in af:
    s = spine.get(r["pn"].zfill(10) if r["pn"].isdigit() else r["pn"])
    if not s:
        agree["(not in catalogue tree)"] += 1
        continue
    k = f"{s['l2']} > {s['l3']}"
    agree[k] += 1
    eur[k] += float(s["eur"] or 0)
print("where the catalogue tree puts those same parts:")
for k, v in agree.most_common():
    print(f"    {v:>4} parts  EUR {eur[k]:>11,.0f}   {k}")
