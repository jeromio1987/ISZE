#!/usr/bin/env python3
"""Audit step 13: is the leaf level fine enough to make a decision on?

A leaf is usable if the parts inside it are commercially alike. Two symptoms of
a leaf that is too coarse:
  - it mixes physically different goods (many distinct HS subheadings, many
    distinct part nouns, a wide list-price spread)
  - one part number dominates its euro, so the 'family' figure is really one SKU
"""
from __future__ import annotations
import collections, csv, statistics
from pathlib import Path

csv.field_size_limit(10_000_000)
D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
OUT = D / "_audit_cls_leaf_quality.csv"

rows = []
for r in csv.DictReader((D / "_audit_cls_spine.csv").open(encoding="utf-8", newline="")):
    if r["node_present"] != "1":
        continue
    r["eur"] = float(r["eur"] or 0)
    # PR00 writes prices >= 1000 with a space thousands separator ("1 133.06"),
    # so a naive float() silently drops every four-figure part.
    raw = (r["list_eur"] or "").replace("\u00a0", "").replace(" ", "")
    try:
        r["lp"] = float(raw) if raw else 0.0
    except ValueError:
        r["lp"] = 0.0
    rows.append(r)

leaf = collections.defaultdict(list)
for r in rows:
    leaf[(r["l1"], r["l2"], r["l3"])].append(r)
tot_eur = sum(r["eur"] for r in rows)

recs = []
for k, v in leaf.items():
    e = sum(x["eur"] for x in v)
    hs = collections.Counter(x["hs6"] for x in v if x["hs6"])
    nouns = collections.Counter(x["noun"] for x in v if x["noun"])
    lps = sorted(x["lp"] for x in v if x["lp"] > 0)
    by_pn = sorted((x["eur"] for x in v), reverse=True)
    top1 = 100 * by_pn[0] / e if e and by_pn else 0
    recs.append({
        "level1": k[0], "level2": k[1], "level3": k[2],
        "part_numbers": len(v),
        "billed_eur": round(e, 2),
        "share_of_billed_pct": round(100 * e / tot_eur, 3),
        "distinct_hs6": len(hs),
        "hs6_modal_share_pct": round(100 * hs.most_common(1)[0][1] / sum(hs.values()), 1) if hs else None,
        "distinct_nouns": len(nouns),
        "noun_modal_share_pct": round(100 * nouns.most_common(1)[0][1] / sum(nouns.values()), 1) if nouns else None,
        "list_price_min": round(lps[0], 2) if lps else None,
        "list_price_median": round(statistics.median(lps), 2) if lps else None,
        "list_price_max": round(lps[-1], 2) if lps else None,
        "list_price_ratio_max_over_median": round(lps[-1] / statistics.median(lps), 1)
            if lps and statistics.median(lps) else None,
        "top1_pn_share_of_leaf_eur_pct": round(top1, 1),
        "top_noun": nouns.most_common(1)[0][0] if nouns else "",
    })

with OUT.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(recs[0].keys()))
    w.writeheader()
    w.writerows(sorted(recs, key=lambda r: -r["billed_eur"]))
print(f"-> {OUT}   ({len(recs)} leaves)")

print("\n" + "=" * 78)
print("LEAVES CARRYING REAL MONEY THAT ARE TOO COARSE TO ACT ON")
print("(>= EUR 250k billed, and either 15+ distinct HS subheadings or a list price")
print(" spread above 50x median, or one part number over 40% of the leaf)")
print(f"\n  {'leaf':<52} {'billed EUR':>11} {'PNs':>5} {'HS6':>4} {'nouns':>6} "
      f"{'px max/med':>11} {'top PN %':>9}")
bad = [r for r in recs if r["billed_eur"] >= 250_000 and (
    (r["distinct_hs6"] or 0) >= 15
    or (r["list_price_ratio_max_over_median"] or 0) >= 50
    or r["top1_pn_share_of_leaf_eur_pct"] >= 40)]
for r in sorted(bad, key=lambda r: -r["billed_eur"]):
    nm = f"{r['level2']} > {r['level3']}"
    print(f"  {nm[:52]:<52} {r['billed_eur']:>11,.0f} {r['part_numbers']:>5} "
          f"{r['distinct_hs6']:>4} {r['distinct_nouns']:>6} "
          f"{str(r['list_price_ratio_max_over_median']):>11} "
          f"{r['top1_pn_share_of_leaf_eur_pct']:>8.1f}%")
be = sum(r["billed_eur"] for r in bad)
print(f"\n  {len(bad)} leaves, EUR {be:,.0f} = {100*be/tot_eur:.1f}% of the 18-month book")

print("\n" + "=" * 78)
print("LEAVES WHERE ONE PART NUMBER IS THE 'FAMILY'  (top PN >= 40% of leaf euro,")
print("and the leaf bills over EUR 100k)")
print(f"\n  {'leaf':<52} {'billed EUR':>11} {'PNs':>5} {'top PN %':>9}")
for r in sorted((x for x in recs if x["top1_pn_share_of_leaf_eur_pct"] >= 40
                 and x["billed_eur"] >= 100_000), key=lambda r: -r["billed_eur"]):
    nm = f"{r['level2']} > {r['level3']}"
    print(f"  {nm[:52]:<52} {r['billed_eur']:>11,.0f} {r['part_numbers']:>5} "
          f"{r['top1_pn_share_of_leaf_eur_pct']:>8.1f}%")

print("\n" + "=" * 78)
print("PRICE SPREAD INSIDE A SINGLE LEAF  (worst 20 by max/median list price,")
print("leaves with >= 50 priced parts)")
print(f"\n  {'leaf':<50} {'min':>9} {'median':>9} {'max':>11} {'max/med':>8}")
cand = [r for r in recs if r["list_price_median"] and r["part_numbers"] >= 50]
for r in sorted(cand, key=lambda r: -(r["list_price_ratio_max_over_median"] or 0))[:20]:
    nm = f"{r['level2']} > {r['level3']}"
    print(f"  {nm[:50]:<50} {r['list_price_min']:>9,.0f} {r['list_price_median']:>9,.0f} "
          f"{r['list_price_max']:>11,.0f} {r['list_price_ratio_max_over_median']:>8,.0f}x")
