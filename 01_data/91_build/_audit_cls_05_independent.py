#!/usr/bin/env python3
"""Audit step 5: test the classification against two INDEPENDENT structures it
did not see when it was built.

  (a) HS commodity code (customs tariff) - a world standard goods taxonomy,
      filled by Isuzu/SAP on the price master.
  (b) Isuzu's own parts-catalogue figure number (Fig No.) - the manufacturer's
      real assembly grouping.

Both are independent of the description text, so agreement is evidence and
disagreement is a candidate error. Also: exact-description conflicts.
"""
from __future__ import annotations
import csv, collections
from pathlib import Path

csv.field_size_limit(10_000_000)
D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
rows = list(csv.DictReader((D / "_audit_cls_spine.csv").open(encoding="utf-8", newline="")))
for r in rows:
    r["eur"] = float(r["eur"] or 0)
live = [r for r in rows if r["node_present"] == "1"]
tot_eur = sum(r["eur"] for r in live)

# --------------------------------------------------------------- HS coverage
print("=" * 78)
print("(a) HS COMMODITY CODE CROSS-CHECK")
hs4 = collections.Counter(r["hs4"] for r in live if r["hs4"])
hs6 = collections.Counter(r["hs6"] for r in live if r["hs6"])
print(f"  parts with a node: {len(live):,}")
print(f"  distinct HS4 headings {len(hs4)}   distinct HS6 subheadings {len(hs6)}")
print(f"  top 20 HS6 by part count:")
for k, v in hs6.most_common(20):
    e = sum(r["eur"] for r in live if r["hs6"] == k)
    modal = collections.Counter(r["l2"] for r in live if r["hs6"] == k).most_common(1)[0]
    print(f"    {k}  {v:>6,} PNs  EUR {e:>11,.0f}   modal L2 = {modal[0]} "
          f"({100*modal[1]/v:.0f}%)")

# ---- agreement index: does the assigned L2 equal its HS6's modal L2?
print("\n  -- agreement index (assigned L2 vs the modal L2 of its HS6 peers) --")
modal_of_hs6, size_of_hs6 = {}, {}
for k in hs6:
    sub = [r for r in live if r["hs6"] == k]
    c = collections.Counter(r["l2"] for r in sub)
    modal_of_hs6[k] = c.most_common(1)[0][0]
    size_of_hs6[k] = len(sub)

MIN = 30
scoped = [r for r in live if r["hs6"] and size_of_hs6.get(r["hs6"], 0) >= MIN]
agree = [r for r in scoped if r["l2"] == modal_of_hs6[r["hs6"]]]
se = sum(r["eur"] for r in scoped)
ae = sum(r["eur"] for r in agree)
print(f"  scope: HS6 groups with >= {MIN} parts -> {len(scoped):,} parts, EUR {se:,.0f}")
print(f"  agree with HS6 majority: {len(agree):,} parts ({100*len(agree)/len(scoped):.1f}%), "
      f"EUR {ae:,.0f} ({100*ae/se:.1f}% of euro)")

# ---- where does it disagree most, by euro?
print("\n  -- biggest euro disagreements vs HS6 majority (top 40 parts) --")
dis = sorted((r for r in scoped if r["l2"] != modal_of_hs6[r["hs6"]]),
             key=lambda r: -r["eur"])
for r in dis[:40]:
    print(f"    EUR {r['eur']:>10,.0f}  {r['pn']}  {r['description'][:42]:<42} "
          f"| assigned {r['l1']} > {r['l2']} > {r['l3']}  | HS {r['hs6']} says {modal_of_hs6[r['hs6']]}")

# ---- purity per L2: how internally coherent is each assigned group in HS terms?
print("\n  -- HS coherence of each assigned Level 2 group --")
print(f"    {'Level 2':<26} {'PNs':>7} {'billed EUR':>13} {'HS6 modal share':>16} {'distinct HS6':>13}")
l2s = collections.Counter(r["l2"] for r in live)
out = []
for l2 in l2s:
    sub = [r for r in live if r["l2"] == l2 and r["hs6"]]
    if not sub:
        continue
    c = collections.Counter(r["hs6"] for r in sub)
    modal = c.most_common(1)[0]
    out.append((modal[1] / len(sub), l2, len(sub), sum(r["eur"] for r in sub),
                modal[0], len(c)))
for share, l2, cnt, e, mhs, nhs in sorted(out):
    print(f"    {l2:<26} {cnt:>7,} {e:>13,.0f} {share*100:>14.1f}% ({mhs}) {nhs:>6}")

# ----------------------------------------------------------- figure purity
print("\n" + "=" * 78)
print("(b) ISUZU OWN CATALOGUE FIGURE CROSS-CHECK")
figs = collections.defaultdict(list)
for r in live:
    if r["fig_no"]:
        figs[r["fig_no"]].append(r)
print(f"  distinct figure numbers: {len(figs)}")
big = {k: v for k, v in figs.items() if len(v) >= 20}
print(f"  figures with >= 20 parts: {len(big)}")
pur_rows, agree_n, agree_e, scope_n, scope_e = [], 0, 0.0, 0, 0.0
for k, v in big.items():
    c = collections.Counter(r["l2"] for r in v)
    m, mc = c.most_common(1)[0]
    pur_rows.append((mc / len(v), k, len(v), sum(r["eur"] for r in v), m, len(c)))
    scope_n += len(v); scope_e += sum(r["eur"] for r in v)
    agree_n += mc; agree_e += sum(r["eur"] for r in v if r["l2"] == m)
print(f"  agreement with the figure's own majority group: "
      f"{agree_n:,}/{scope_n:,} parts ({100*agree_n/scope_n:.1f}%), "
      f"EUR {agree_e:,.0f}/{scope_e:,.0f} ({100*agree_e/scope_e:.1f}%)")
pur_rows.sort()
print("\n  -- 25 figures where the classifier scatters an Isuzu assembly the most --")
for share, k, cnt, e, m, ngrp in pur_rows[:25]:
    c = collections.Counter(r["l2"] for r in figs[k])
    top = ", ".join(f"{a} {b}" for a, b in c.most_common(5))
    print(f"    fig {k:<6} {cnt:>5} PNs  EUR {e:>11,.0f}  purity {share*100:5.1f}% "
          f"across {ngrp} groups -> {top}")

# -------------------------------------------------- exact-description clash
print("\n" + "=" * 78)
print("(c) EXACT SAME DESCRIPTION, DIFFERENT NODE")
bydesc = collections.defaultdict(list)
for r in live:
    if r["description"]:
        bydesc[r["description"]].append(r)
clash_l2 = {d: v for d, v in bydesc.items() if len({x["l2"] for x in v}) > 1}
clash_l3 = {d: v for d, v in bydesc.items() if len({x["l3"] for x in v}) > 1}
pn_l2 = sum(len(v) for v in clash_l2.values())
pn_l3 = sum(len(v) for v in clash_l3.values())
e_l2 = sum(x["eur"] for v in clash_l2.values() for x in v)
e_l3 = sum(x["eur"] for v in clash_l3.values() for x in v)
print(f"  distinct descriptions with a node : {len(bydesc):,}")
print(f"  descriptions split across Level 2 : {len(clash_l2):,}  "
      f"({pn_l2:,} parts, EUR {e_l2:,.0f} = {100*e_l2/tot_eur:.2f}% of billed)")
print(f"  descriptions split across Level 3 : {len(clash_l3):,}  "
      f"({pn_l3:,} parts, EUR {e_l3:,.0f} = {100*e_l3/tot_eur:.2f}% of billed)")
print("\n  -- top 30 L2 clashes by euro --")
sc = sorted(clash_l2.items(), key=lambda kv: -sum(x["eur"] for x in kv[1]))
for d, v in sc[:30]:
    c = collections.Counter(x["l2"] for x in v)
    print(f"    EUR {sum(x['eur'] for x in v):>10,.0f}  {len(v):>4} PNs  {d[:44]:<44} -> "
          + ", ".join(f"{a} {b}" for a, b in c.most_common(5)))
