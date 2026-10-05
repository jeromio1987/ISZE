#!/usr/bin/env python3
"""Audit step 8: two defects in the provenance chain.

DEFECT A - successor inheritance.
  build_pr00_classification.py loops `for i_pn_idx in (i_pn, i_new)` and writes
  BOTH the part number and its 'Newest P/N' successor into the same output key
  space, skipping any key already present. So a successor part number can be
  classified from an UNRELATED predecessor row that happened to appear earlier
  in the workbook, and its own row is then discarded. Measure how often the
  inherited node differs from the node the part's own description would get.

DEFECT B - key normalisation mismatch.
  That builder stores zero-STRIPPED keys (`s.lstrip("0")`); the v2 file and its
  gate use zero-PADDED 10-character keys. Measure how many rows the gate's
  'catalogue ties to PR00 on 100%' check therefore never tested.
"""
from __future__ import annotations
import collections, csv, re
from pathlib import Path
import openpyxl

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ISZE / "01_data" / "00_derived"
CLS_WB = ISZE / "01_data" / "01_Pricing" / \
    "IE40 Price list as of 13.03.2026 PR00_3_level_classified_GPT.xlsx"
OUT = D / "_audit_cls_successor_inheritance.csv"

def norm_strip(pn) -> str:
    s = re.sub(r"\.0$", "", str(pn).strip().upper())
    return s.lstrip("0") or "0"

def pad(pn: str) -> str:
    return pn.zfill(10) if pn.isdigit() else pn

# ---- read the workbook exactly as the builder reads it
wb = openpyxl.load_workbook(CLS_WB, read_only=True, data_only=True)
ws = wb["Sheet1"]
it = ws.iter_rows(values_only=True)
hdr = [("" if c is None else str(c).strip()) for c in next(it)]
i = {h: k for k, h in enumerate(hdr)}
recs = []
for row in it:
    if row is None or row[i["P/N"]] is None:
        continue
    def g(c):
        v = row[i[c]]
        return "" if v is None else str(v).strip()
    recs.append((g("P/N"), g("Newest P/N"), g("Description"),
                 g("Level 1 Family"), g("Level 2 Group"), g("Level 3 Type")))
wb.close()

money = {}
for r in csv.DictReader((D / "_audit_cls_desc_spine.csv").open(encoding="utf-8", newline="")):
    money[r["part_number"]] = float(r["l12m_eur"] or 0)
tot_eur = sum(money.values())

# own node, keyed on the part's own row
own = {}
for pn, new, desc, l1, l2, l3 in recs:
    own[norm_strip(pn)] = (l1, l2, l3, desc, pn)

# replay the builder's first-come-first-served fill
out = {}
for pn, new, desc, l1, l2, l3 in recs:
    for cand in (pn, new):
        if not cand:
            continue
        n = norm_strip(cand)
        if not n or n in out:
            continue
        out[n] = (l1, l2, l3, desc, pn, "self" if cand == pn else "successor")

print("DEFECT A - successor inheritance")
print(f"  workbook rows                         {len(recs):,}")
print(f"  distinct keys the builder writes       {len(out):,}")
print(f"  of which filled from a 'Newest P/N'   "
      f"{sum(1 for v in out.values() if v[5]=='successor'):,}")

# a successor key is WRONG-BY-INHERITANCE when the part has its own workbook row
# carrying a different node, but the successor fill won the key.
bad = []
for n, v in out.items():
    if v[5] != "successor":
        continue
    o = own.get(n)
    if not o:
        continue          # part has no own row - inheritance is the only source
    if (o[0], o[1], o[2]) != (v[0], v[1], v[2]):
        bad.append((n, o, v))
e_bad = sum(money.get(pad(n), 0) for n, o, v in bad)
print(f"  successor keys whose OWN row says something different: {len(bad):,}"
      f"   EUR {e_bad:,.0f} ({100*e_bad/tot_eur:.2f}% of billed)")
print("\n  top 25 by billed euro:")
for n, o, v in sorted(bad, key=lambda t: -money.get(pad(t[0]), 0))[:25]:
    print(f"    EUR {money.get(pad(n),0):>9,.0f}  {pad(n)}  own text {o[3][:30]:<30}")
    print(f"        own node        {o[0]} > {o[1]} > {o[2]}")
    print(f"        inherited from  {v[4]} '{v[3][:30]}' -> {v[0]} > {v[1]} > {v[2]}")

with OUT.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["part_number", "own_description", "own_l1", "own_l2", "own_l3",
                "inherited_from_pn", "inherited_description",
                "inherited_l1", "inherited_l2", "inherited_l3", "l12m_eur"])
    for n, o, v in sorted(bad, key=lambda t: -money.get(pad(t[0]), 0)):
        w.writerow([pad(n), o[3], o[0], o[1], o[2], v[4], v[3], v[0], v[1], v[2],
                    f"{money.get(pad(n),0):.2f}"])
print(f"\n-> {OUT}")

# ------------------------------------------------------------------ defect B
print("\nDEFECT B - key normalisation mismatch in the gate's strongest check")
pr00 = {r["pn_norm"] for r in csv.DictReader(
    (D / "pr00_classification.csv").open(encoding="utf-8", newline=""))}
v2 = [r["part_number"] for r in csv.DictReader(
    (D / "aim_pn_classification_v2.csv").open(encoding="utf-8", newline=""))]
joined = [k for k in v2 if k in pr00]
lead0 = [k for k in v2 if k.startswith("0")]
lead0_joined = [k for k in lead0 if k in pr00]
print(f"  v2 rows                                   {len(v2):,}")
print(f"  v2 keys found verbatim in pr00_classification {len(joined):,}")
print(f"  v2 keys NOT found (never tested by the gate)  {len(v2)-len(joined):,}"
      f"   EUR {sum(money.get(k,0) for k in v2 if k not in pr00):,.0f}")
print(f"  v2 keys with a leading zero               {len(lead0):,}, "
      f"of which joined {len(lead0_joined):,}")
print(f"  -> the gate reported 163,014 rows checked at 100.0%; "
      f"{len(v2)-len(joined):,} rows were skipped, not verified")
