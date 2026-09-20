#!/usr/bin/env python3
"""Audit step 4: build the audit spine.

One row per classified part number, carrying:
  - the assigned node (catalog_l1/l2/l3) and the workbook node
  - the PR00 description, list price, HS commodity code, origin, figure
  - billed euro / qty in 2025-01-01..2026-06-30
  - the description NOUN HEAD (Isuzu descriptions are 'NOUN; qualifier')

Writes _audit_cls_spine.csv and prints coverage + first structural findings.
"""
from __future__ import annotations
import csv, collections, re
from pathlib import Path

csv.field_size_limit(10_000_000)
D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
V2 = D / "aim_pn_classification_v2.csv"
FLAT = D / "_audit_cls_pr00_flat.csv"
SPINE = D / "_audit_cls_desc_spine.csv"
OUT = D / "_audit_cls_spine.csv"

pr00 = {}
for r in csv.DictReader(FLAT.open(encoding="utf-8", newline="")):
    pr00[r["pn"]] = r

money = {}
for r in csv.DictReader(SPINE.open(encoding="utf-8", newline="")):
    money[r["part_number"]] = r

cls = list(csv.DictReader(V2.open(encoding="utf-8", newline="")))

def noun_head(desc: str) -> str:
    """Isuzu part text is 'NOUN; qualifier,qualifier'. Return the noun."""
    d = (desc or "").upper().strip()
    if not d:
        return ""
    head = re.split(r"[;,(]", d)[0]
    head = re.sub(r"[^A-Z0-9 /&.-]", " ", head)
    return " ".join(head.split())

rows = []
for r in cls:
    pn = r["part_number"]
    p = pr00.get(pn, {})
    m = money.get(pn, {})
    desc = (p.get("description") or "").strip() or (r["description_norm"] or "").strip() \
        or (m.get("description_best") or "").strip()
    hs = (p.get("hs_code") or "").strip()
    rows.append({
        "pn": pn,
        "description": desc.upper(),
        "noun": noun_head(desc),
        "l1": r["catalog_l1"], "l2": r["catalog_l2"], "l3": r["catalog_l3"],
        "wb_l1": r["workbook_l1"], "wb_l2": r["workbook_l2"], "wb_l3": r["workbook_l3"],
        "wb_kind": r["workbook_axis_kind"], "wb_source": r["workbook_source"],
        "residual": r["catalog_residual"], "node_present": r["catalog_node_present"],
        "fig_key": r["fig_key"], "fig_no": (p.get("fig_no") or "").strip(),
        "key_no": (p.get("key_no") or "").strip(),
        "hs": hs, "hs4": hs[:4], "hs6": hs[:6],
        "origin": (p.get("origin") or "").strip(),
        "list_eur": (p.get("price_eur") or "").strip(),
        "weight_kg": (p.get("weight_kg") or "").strip(),
        "in_pr00": "1" if p else "0",
        "eur": float(m.get("l12m_eur") or 0),
        "qty": float(m.get("l12m_qty") or 0),
    })

with OUT.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

n = len(rows)
tot_eur = sum(r["eur"] for r in rows)
print(f"spine rows                {n:,}")
print(f"in PR00 price file        {sum(1 for r in rows if r['in_pr00']=='1'):,}")
print(f"with a description        {sum(1 for r in rows if r['description']):,} "
      f"({100*sum(1 for r in rows if r['description'])/n:.1f}%)")
print(f"with an HS commodity code {sum(1 for r in rows if r['hs']):,} "
      f"({100*sum(1 for r in rows if r['hs'])/n:.1f}%)")
print(f"with a figure number      {sum(1 for r in rows if r['fig_no']):,}")
print(f"billed in window          {sum(1 for r in rows if r['eur']>0):,} PNs, "
      f"EUR {tot_eur:,.0f}")
print(f"-> {OUT}")

# ------------------------------------------------- residual / 'Other' mass
print("\n" + "=" * 74)
print("RESIDUAL AND 'OTHER' MASS  (rows / billed euro in window)")
def blk(name, pred):
    rr = [r for r in rows if pred(r)]
    e = sum(r["eur"] for r in rr)
    print(f"  {name:<44} {len(rr):>7,} PNs  EUR {e:>13,.0f}  "
          f"{100*e/tot_eur:5.2f}% of billed")
blk("Other / review > Miscellaneous (L1 residual)", lambda r: r["residual"] == "1")
blk("no node at all", lambda r: r["node_present"] == "0" and r["residual"] == "0")
blk("L3 starting with 'Other'", lambda r: r["l3"].lower().startswith("other"))
blk("L3 'Review needed'", lambda r: r["l3"] == "Review needed")
blk("ANY vague bucket (residual + Other* L3)",
    lambda r: r["residual"] == "1" or r["l3"].lower().startswith("other")
    or r["node_present"] == "0")

# ------------------------------------------------- tiny leaves
print("\n" + "=" * 74)
print("LEAF SIZE DISTRIBUTION")
leaf = collections.Counter((r["l1"], r["l2"], r["l3"]) for r in rows if r["node_present"] == "1")
sizes = sorted(leaf.values())
print(f"  leaves {len(leaf)}   min {sizes[0]}  median {sizes[len(sizes)//2]}  max {sizes[-1]}")
tiny = {k: v for k, v in leaf.items() if v <= 10}
print(f"  leaves with <=10 part numbers: {len(tiny)}")
for k, v in sorted(tiny.items(), key=lambda kv: kv[1]):
    e = sum(r["eur"] for r in rows if (r["l1"], r["l2"], r["l3"]) == k)
    print(f"     {v:>3} PNs  EUR {e:>11,.0f}   {k[0]} > {k[1]} > {k[2]}")

# ------------------------------------------------- noun head purity
print("\n" + "=" * 74)
print("NOUN-HEAD CONSISTENCY  (same noun, different Level 2)")
by_noun = collections.defaultdict(collections.Counter)
noun_eur = collections.Counter()
for r in rows:
    if r["noun"] and r["node_present"] == "1":
        by_noun[r["noun"]][r["l2"]] += 1
        noun_eur[r["noun"]] += r["eur"]
split = []
for nn, c in by_noun.items():
    tot = sum(c.values())
    if tot < 20:
        continue
    modal = c.most_common(1)[0][1]
    purity = modal / tot
    split.append((purity, tot, nn, c))
split.sort()
print(f"  nouns with >=20 parts: {len(split)}")
print(f"  worst 30 by modal-group purity:")
for purity, tot, nn, c in split[:30]:
    top = ", ".join(f"{k} {v}" for k, v in c.most_common(4))
    print(f"    {purity*100:5.1f}%  {tot:>5} PNs  EUR {noun_eur[nn]:>11,.0f}  {nn:<26} -> {top}")
