#!/usr/bin/env python3
"""Audit step 14: does the misfile actually break the PMS service categories?

fig_key_taxonomy.yaml derives pms_category from the PR00 node:

    pr00_pms_category_rules:
      - match_group: "Filters"
        level3_contains: {oil:.., fuel:.., air: air_filter, urea:..}
      - match_fig_key: "130-006"    ->  air_filter      # escape hatch
      - match_group: "Suspension"
        level3_contains: {king: king_pin, ...}

An air filter sitting in "Air conditioning > Other A/C" cannot match
match_group "Filters". The only thing that can still save it is the fig-key
rule. Measure whether it does. Same question for king pins under Suspension.
Then check the shipped parts_catalog_dimension.csv to see what actually landed.
"""
from __future__ import annotations
import collections, csv, re
from pathlib import Path

csv.field_size_limit(10_000_000)
D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
rows = [r for r in csv.DictReader((D / "_audit_cls_spine.csv").open(encoding="utf-8", newline=""))
        if r["node_present"] == "1"]
for r in rows:
    r["eur"] = float(r["eur"] or 0)

AIRPAT = [r"\bFILTER; ?ACL\b", r"\bELEMENT; ?A[CI]L\b", r"ELEMENT; ?AIR CLEANER",
          r"FILTER; ?AIR CLEANER", r"\bAIR CLEANER ELEMENT\b", r"ELEMENT ASM; ?AIR"]
NOT = [r"\bCASE\b", r"\bCOVER\b", r"\bBRACKET\b", r"\bBRKT\b", r"\bBOLT\b", r"\bSEAL\b",
       r"\bGASKET\b", r"\bCLAMP\b", r"\bDUCT\b", r"\bHOSE\b", r"\bBODY\b", r"\bIND\b"]
air = [r for r in rows if r["description"]
       and any(re.search(p, r["description"]) for p in AIRPAT)
       and not any(re.search(p, r["description"]) for p in NOT)]
mis = [r for r in air if r["l3"] != "Air filter"]

print("AIR FILTER -> pms_category, rule by rule")
print(f"  engine air-cleaner elements found        {len(air)}   EUR {sum(r['eur'] for r in air):,.0f}")
print(f"  of which outside 'Filters' group         {len(mis)}   EUR {sum(r['eur'] for r in mis):,.0f}")
in_filters = [r for r in air if r["l2"] == "Filters"]
print(f"  can match rule `match_group: Filters`    {len(in_filters)}   "
      f"EUR {sum(r['eur'] for r in in_filters):,.0f}")

hatch = [r for r in mis if r["fig_key"] == "130-006"]
print(f"  saved by `match_fig_key: 130-006`        {len(hatch)}   "
      f"EUR {sum(r['eur'] for r in hatch):,.0f}")
lost = [r for r in mis if r["fig_key"] != "130-006"]
print(f"  -> NO pms_category at all               {len(lost)}   "
      f"EUR {sum(r['eur'] for r in lost):,.0f}")
fk = collections.Counter(r["fig_key"] or "(blank)" for r in mis)
print(f"  fig keys actually carried by the misfiled parts: "
      f"{dict(fk.most_common(8))}")

print("\nKING PIN -> pms_category")
kp = [r for r in rows if r["description"] and re.search(r"\bKING PIN\b", r["description"])]
kp_susp = [r for r in kp if r["l2"] == "Suspension"]
print(f"  parts reading KING PIN                   {len(kp)}   EUR {sum(r['eur'] for r in kp):,.0f}")
print(f"  can match rule `match_group: Suspension` {len(kp_susp)}   "
      f"EUR {sum(r['eur'] for r in kp_susp):,.0f}")
print(f"  -> NO king_pin category                  {len(kp)-len(kp_susp)}   "
      f"EUR {sum(r['eur'] for r in kp)-sum(r['eur'] for r in kp_susp):,.0f}")
print(f"  where they sit: {dict(collections.Counter(f'{r[chr(39)+chr(39)]}' if False else r['l2']+' > '+r['l3'] for r in kp).most_common(4))}")

# ------------------------------------------- what actually shipped
pcd = D / "parts_catalog_dimension.csv"
print(f"\nSHIPPED parts_catalog_dimension.csv")
if not pcd.is_file():
    print("  MISSING - cannot verify what landed")
else:
    pc = list(csv.DictReader(pcd.open(encoding="utf-8", newline="")))
    print(f"  rows {len(pc):,}   columns {list(pc[0].keys())}")
    key = "part_number" if "part_number" in pc[0] else list(pc[0].keys())[0]
    catcol = next((c for c in pc[0] if "pms_category" in c), None)
    idx = {r[key]: r for r in pc}
    cats = collections.Counter(r.get(catcol) or "(blank)" for r in pc)
    print(f"  pms_category populated on {sum(v for k,v in cats.items() if k!='(blank)'):,} rows")
    print(f"  air_filter rows in the shipped dimension: {cats.get('air_filter', 0)}")
    print(f"  king_pin rows  in the shipped dimension: {cats.get('king_pin', 0)}")
    print(f"\n  the {len(air)} engine air-cleaner parts, as tagged in the shipped dimension:")
    got = collections.Counter()
    gote = collections.Counter()
    for r in air:
        v = (idx.get(r["pn"], {}).get(catcol) or "(not tagged)")
        got[v] += 1
        gote[v] += r["eur"]
    for k, v in got.most_common():
        print(f"    {v:>4} parts  EUR {gote[k]:>11,.0f}   pms_category = {k}")
    print(f"\n  the {len(kp)} KING PIN parts, as tagged:")
    got = collections.Counter()
    gote = collections.Counter()
    for r in kp:
        v = (idx.get(r["pn"], {}).get(catcol) or "(not tagged)")
        got[v] += 1
        gote[v] += r["eur"]
    for k, v in got.most_common():
        print(f"    {v:>4} parts  EUR {gote[k]:>11,.0f}   pms_category = {k}")
