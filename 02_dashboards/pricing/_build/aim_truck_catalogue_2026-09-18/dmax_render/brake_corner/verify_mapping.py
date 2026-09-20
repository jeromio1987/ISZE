"""Verify the part-number to fig-key mapping behind each callout.

For every part family in the front brake corner, print the billed part numbers,
their billed descriptions, and the catalogue row each one sits on.  This is the
evidence behind what the callouts say, so it is checked directly rather than
inferred from a summary.
"""
from __future__ import annotations

import collections
import csv
import os
import re

ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"
D = os.path.join(ISZE, "01_data", "00_derived")
CAT = os.path.join(D, "parts_catalog_dimension.csv")
SALES = os.path.join(D, "sales_by_db_fig_key_year.csv")
PRICE = os.path.join(D, "price_bp_weighted_compare_pn.csv")

FAM = {
    "disc_front": re.compile(r"^ROTOR;\s*DISC BRK,FRT\s*$", re.I),
    "padkit_front": re.compile(r"^PAD KIT;\s*CALIPER,DISC BRK,FRT\s*$", re.I),
    "padkit_noshim": re.compile(r"^PAD KIT;\s*DISC BRK,W/O SHIM\s*&\s*CLIP\s*$", re.I),
    "caliper_front": re.compile(r"^CALIPER;\s*FRT DISC BRK\s*$", re.I),
}

pn_desc = {}
pn_price = {}
for r in csv.DictReader(open(PRICE, newline="", encoding="utf-8-sig")):
    d = (r["billed_description"] or "").strip()
    pn = (r["part_number"] or "").strip()
    for k, rx in FAM.items():
        if rx.match(d):
            pn_price.setdefault(k, collections.Counter())[pn] += float(r["net_sales_value"] or 0)
            pn_desc[pn] = d

cat = collections.defaultdict(list)
for r in csv.DictReader(open(CAT, newline="", encoding="utf-8-sig")):
    pn = (r["part_number"] or "").strip()
    cat[pn].append((r["fig_key"], r["fig_key_label"], r["pms_category"]))

for k in FAM:
    pns = pn_price.get(k, {})
    print("=" * 100)
    print("%s  billed part numbers: %d" % (k, len(pns)))
    for pn, eur in pns.most_common():
        rows = cat.get(pn)
        rowtxt = ("NO CATALOGUE ROW" if not rows
                  else " | ".join("%s %s [%s]" % (a, b, c) for a, b, c in rows))
        print("   %-12s EUR %10s   %-32s -> %s" % (pn, format(eur, ",.0f"),
                                                   pn_desc.get(pn, "")[:32], rowtxt))

print()
print("=" * 100)
print("what the SALES file says for every fig key those part numbers landed on")
keys = set()
for k in FAM:
    for pn in pn_price.get(k, {}):
        for fk, fl, c in cat.get(pn, []):
            keys.add(fk)
agg = collections.defaultdict(lambda: {"eur": 0.0, "qty": 0.0, "lab": collections.Counter(),
                                       "pns": 0, "db": collections.Counter()})
for r in csv.DictReader(open(SALES, newline="", encoding="utf-8-sig")):
    fk = (r["fig_key"] or "").strip()
    if fk not in keys:
        continue
    e = float(r["net_sales_eur"] or 0)
    agg[fk]["eur"] += e
    agg[fk]["qty"] += float(r["billed_qty"] or 0)
    agg[fk]["lab"][r["fig_key_label"]] += e
    agg[fk]["pns"] = max(agg[fk]["pns"], int(r["distinct_pns"] or 0))
    agg[fk]["db"][r["distributor_code"]] += e
for fk in sorted(keys):
    a = agg.get(fk)
    if not a:
        print("   %-10s no billing at all in the sales file" % fk)
        continue
    print("   %-10s %-34s EUR %12s  qty %9s  pns %3d  top DBs %s"
          % (fk, a["lab"].most_common(1)[0][0][:34], format(a["eur"], ",.0f"),
             format(a["qty"], ",.0f"), a["pns"], a["db"].most_common(3)))
