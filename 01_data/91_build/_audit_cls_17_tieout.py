#!/usr/bin/env python3
"""Claim-check: does the classification join actually tie out to the shipped
price comparison, and are the keys actually clean?

Claims under test (asserted in chat, sourced from aim_catalog_breakdown_NOTES.md
rather than recomputed):
  A. network weighted base-price increase reproduces 5.9616%
  B. step euro reproduces 1,652,140.71
  C. keys are clean: 0 duplicates, all 10 characters
  D. the description-rule error rate is 4.12% of the 18-month book
"""
from __future__ import annotations
import collections, csv
from pathlib import Path

csv.field_size_limit(10_000_000)
D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")

# ---------------------------------------------------------------- A and B
rows = list(csv.DictReader((D / "price_bp_weighted_compare_pn.csv").open(
    encoding="utf-8-sig", newline="")))
print(f"price_bp_weighted_compare_pn.csv rows: {len(rows):,}")

def f(v):
    v = (v or "").strip().replace("\u00a0", "").replace(" ", "")
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None

def truthy(v):
    return (v or "").strip().lower() in ("1", "true", "yes", "y")

inscope = [r for r in rows if truthy(r.get("in_scope"))]
print(f"in_scope rows: {len(inscope):,}")

num = den = 0.0
step = 0.0
priced_both = 0
for r in inscope:
    q = f(r.get("billed_qty"))
    new = f(r.get("bp_new_jpy"))
    old = f(r.get("bp_prior_revised"))
    s = f(r.get("value_eur_step"))
    if s is not None:
        step += s
    if q is not None and new is not None and old is not None and old > 0:
        num += q * new
        den += q * old
        priced_both += 1

inc = (num / den - 1) * 100 if den else None
print(f"\nA. network weighted base-price increase")
print(f"   rows priced on both sides : {priced_both:,}")
print(f"   recomputed                : {inc:.4f}%")
print(f"   claimed in the note       : 5.9616%")
print(f"   verdict                   : {'MATCH' if abs(inc-5.9616) < 0.0001 else 'MISMATCH'}")

print(f"\nB. step euro")
print(f"   recomputed                : {step:,.2f}")
print(f"   claimed in the note       : 1,652,140.71")
print(f"   verdict                   : {'MATCH' if abs(step-1_652_140.71) < 0.01 else 'MISMATCH'}")

# does the classification join preserve it?
cls = {r["part_number"]: r for r in csv.DictReader(
    (D / "aim_pn_classification_v2.csv").open(encoding="utf-8", newline=""))}
def pad(s):
    s = (s or "").strip()
    return s.zfill(10) if s.isdigit() else s
num2 = den2 = step2 = 0.0
matched = 0
unmatched_step = 0.0
for r in inscope:
    pn = pad(r.get("part_number"))
    hit = pn in cls
    q, new, old = f(r.get("billed_qty")), f(r.get("bp_new_jpy")), f(r.get("bp_prior_revised"))
    s = f(r.get("value_eur_step")) or 0.0
    if hit:
        matched += 1
        step2 += s
        if q is not None and new is not None and old is not None and old > 0:
            num2 += q * new
            den2 += q * old
    else:
        unmatched_step += s
inc2 = (num2 / den2 - 1) * 100 if den2 else None
print(f"\n   join to the classification: {matched:,}/{len(inscope):,} rows "
      f"({100*matched/len(inscope):.4f}%)")
print(f"   increase on matched rows  : {inc2:.4f}%  (vs {inc:.4f}% on all in-scope)")
print(f"   step euro on matched rows : {step2:,.2f}  "
      f"(unmatched carries {unmatched_step:,.2f})")

# ---------------------------------------------------------------- C
keys = [r["part_number"] for r in cls.values()] if False else \
    [r["part_number"] for r in csv.DictReader(
        (D / "aim_pn_classification_v2.csv").open(encoding="utf-8", newline=""))]
dupes = len(keys) - len(set(keys))
badlen = sum(1 for k in keys if len(k) != 10)
print(f"\nC. key integrity, recomputed on the file")
print(f"   rows {len(keys):,}   duplicate part numbers {dupes}   "
      f"keys not exactly 10 chars {badlen}")
pr00 = {r["pn_norm"] for r in csv.DictReader(
    (D / "pr00_classification.csv").open(encoding="utf-8", newline=""))}
nojoin = [k for k in keys if k not in pr00]
print(f"   BUT keys that do not join pr00_classification: {len(nojoin):,} "
      f"(leading zero: {sum(1 for k in nojoin if k.startswith('0')):,})")

# ---------------------------------------------------------------- D
v = list(csv.DictReader((D / "_audit_cls_description_violations.csv").open(
    encoding="utf-8", newline="")))
spine = list(csv.DictReader((D / "_audit_cls_spine.csv").open(encoding="utf-8", newline="")))
tot = sum(float(r["eur"] or 0) for r in spine)
ve = sum(float(x["l12m_eur"]) for x in v)
print(f"\nD. description-rule error rate, recomputed")
print(f"   flagged part numbers {len({x['part_number'] for x in v}):,}   "
      f"EUR {ve:,.0f} of {tot:,.0f} = {100*ve/tot:.2f}%")
