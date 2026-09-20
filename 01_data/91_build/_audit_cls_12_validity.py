#!/usr/bin/env python3
"""Audit step 12: is the Level-1 axis valid?

Level 1 is a COMMERCIAL posture ('Competitive parts', 'Accident parts',
'High value repair', 'Comfort parts'). It was assigned by a text rule reading
the part noun. Competitive exposure, though, is a property of the market: does
an independent brand offer this part, at what price, in which country.

So the axis makes a falsifiable claim. Test it against the independent-brand
price scrapes we already hold: if 'Competitive parts' means anything, parts in
that family should be far likelier to have an independent-brand match than
parts outside it.
"""
from __future__ import annotations
import collections, csv
from pathlib import Path

csv.field_size_limit(10_000_000)
D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")

spine = {}
for r in csv.DictReader((D / "_audit_cls_spine.csv").open(encoding="utf-8", newline="")):
    spine[r["pn"]] = r

def pad(s):
    s = (s or "").strip()
    return s.zfill(10) if s.isdigit() else s

# ---- parts with evidence of an independent-brand equivalent
found, checked = set(), set()
src_rows = []
for name, pncol, hitcol in [
    ("competitiveness_autodoc_risk.csv", "part_number", "Autodoc_CheapestBrand"),
    ("iam_ks_price_gap.csv", "pn", "brands_found"),
    ("iam_mekonomen_price_gap.csv", "pn", "brands_found"),
]:
    p = D / name
    if not p.is_file():
        continue
    for r in csv.DictReader(p.open(encoding="utf-8-sig", newline="")):
        pn = pad(r.get(pncol))
        if not pn:
            continue
        checked.add(pn)
        hit = (r.get(hitcol) or "").strip()
        status = (r.get("status") or "").strip().lower()
        if hit and hit.lower() not in ("", "none", "nan", "0") and "no_match" not in status:
            found.add(pn)
        src_rows.append((name, pn, hit, status))
    print(f"  {name}: cumulative checked {len(checked):,}, with an independent brand found {len(found):,}")

checked = {p for p in checked if p in spine}
found = {p for p in found if p in spine}
print(f"\nparts scraped against independent brands and present in the classification: {len(checked):,}")
print(f"of those, an independent-brand equivalent was found for: {len(found):,} "
      f"({100*len(found)/len(checked):.1f}%)")

print("\n" + "=" * 78)
print("DOES THE 'Competitive parts' LABEL PREDICT AN INDEPENDENT-BRAND ALTERNATIVE?")
print(f"\n  {'assigned Level 1':<26} {'scraped':>8} {'brand found':>12} {'hit rate':>9}")
tab = collections.defaultdict(lambda: [0, 0])
for pn in checked:
    l1 = spine[pn]["l1"] or "(none)"
    tab[l1][0] += 1
    if pn in found:
        tab[l1][1] += 1
for l1, (c, f) in sorted(tab.items(), key=lambda kv: -kv[1][0]):
    print(f"  {l1:<26} {c:>8,} {f:>12,} {100*f/c:>8.1f}%")

comp = tab.get("Competitive parts", [0, 0])
noncomp_c = sum(v[0] for k, v in tab.items() if k != "Competitive parts")
noncomp_f = sum(v[1] for k, v in tab.items() if k != "Competitive parts")
print(f"\n  labelled Competitive parts : {comp[1]:,}/{comp[0]:,} = "
      f"{100*comp[1]/comp[0] if comp[0] else 0:.1f}% have an independent-brand match")
print(f"  labelled anything else     : {noncomp_f:,}/{noncomp_c:,} = "
      f"{100*noncomp_f/noncomp_c if noncomp_c else 0:.1f}%")
if comp[0] and noncomp_c:
    lift = (comp[1]/comp[0]) / (noncomp_f/noncomp_c) if noncomp_f else float("inf")
    print(f"  lift of the label          : {lift:.2f}x  "
          f"(1.00x would mean the label carries no information)")

print("\n  and the reverse: of the parts where an independent brand WAS found,")
c2 = collections.Counter(spine[pn]["l1"] or "(none)" for pn in found)
for k, v in c2.most_common():
    print(f"    {v:>5} ({100*v/len(found):>5.1f}%)  sit in {k}")

print("\n" + "=" * 78)
print("SELECTION CAVEAT - what was chosen for scraping in the first place")
c3 = collections.Counter(spine[pn]["l1"] or "(none)" for pn in checked)
allc = collections.Counter(r["l1"] or "(none)" for r in spine.values()
                           if r["node_present"] == "1")
tot = sum(allc.values())
print(f"  {'Level 1':<26} {'% of scrape list':>17} {'% of whole catalogue':>21}")
for k in sorted(set(c3) | set(allc), key=lambda x: -c3.get(x, 0)):
    print(f"  {k:<26} {100*c3.get(k,0)/len(checked):>16.1f}% {100*allc.get(k,0)/tot:>20.1f}%")
print("\n  The scrape list was not drawn at random, so the hit rates above measure")
print("  the label against the parts somebody already suspected. Read the lift, not")
print("  the absolute rate.")
