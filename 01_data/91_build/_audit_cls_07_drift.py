#!/usr/bin/env python3
"""Audit step 7: why do identical CURRENT descriptions carry different nodes?

Hypothesis: the classification was frozen on the 13-Mar-2026 price list text.
The live price master (10-Aug-2026) has different text for some part numbers.
Nobody re-ran the classifier, so the node now describes an old description.
Test it by diffing the two description columns part number by part number.
"""
from __future__ import annotations
import collections, csv
from pathlib import Path
import openpyxl

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ISZE / "01_data" / "00_derived"
CLS_WB = ISZE / "01_data" / "01_Pricing" / \
    "IE40 Price list as of 13.03.2026 PR00_3_level_classified_GPT.xlsx"
OUT = D / "_audit_cls_description_drift.csv"

wb = openpyxl.load_workbook(CLS_WB, read_only=True, data_only=True)
ws = wb["Sheet1"]
it = ws.iter_rows(values_only=True)
hdr = [("" if c is None else str(c).strip()) for c in next(it)]
i = {h: k for k, h in enumerate(hdr)}
mar = {}
for row in it:
    if row is None or row[i["P/N"]] is None:
        continue
    pn = str(row[i["P/N"]]).strip()
    pn = pn.zfill(10) if pn.isdigit() else pn
    mar[pn] = {
        "desc": "" if row[i["Description"]] is None else str(row[i["Description"]]).strip(),
        "l1": "" if row[i["Level 1 Family"]] is None else str(row[i["Level 1 Family"]]).strip(),
        "l2": "" if row[i["Level 2 Group"]] is None else str(row[i["Level 2 Group"]]).strip(),
        "l3": "" if row[i["Level 3 Type"]] is None else str(row[i["Level 3 Type"]]).strip(),
    }
wb.close()

aug = {}
for r in csv.DictReader((D / "_audit_cls_pr00_flat.csv").open(encoding="utf-8", newline="")):
    aug[r["pn"]] = r["description"].strip()

money = {}
for r in csv.DictReader((D / "_audit_cls_desc_spine.csv").open(encoding="utf-8", newline="")):
    money[r["part_number"]] = float(r["l12m_eur"] or 0)

both = [pn for pn in mar if pn in aug]
same = [pn for pn in both if mar[pn]["desc"].upper() == aug[pn].upper()]
diff = [pn for pn in both if mar[pn]["desc"].upper() != aug[pn].upper()]
e_diff = sum(money.get(pn, 0) for pn in diff)
tot = sum(money.values())

print("PART TEXT DRIFT: classified list 13-Mar-2026  vs  live price master 10-Aug-2026")
print(f"  part numbers in the classified list      {len(mar):,}")
print(f"  part numbers in the live price master    {len(aug):,}")
print(f"  present in both                          {len(both):,}")
print(f"  description IDENTICAL                    {len(same):,} ({100*len(same)/len(both):.2f}%)")
print(f"  description CHANGED                      {len(diff):,} ({100*len(diff)/len(both):.2f}%)"
      f"   EUR {e_diff:,.0f} ({100*e_diff/tot:.2f}% of billed)")
print(f"  in classified list but NOT in live master {len(mar)-len(both):,}")
print(f"  in live master but NOT classified         {len(aug)-len(both):,}"
      f"   EUR {sum(money.get(p,0) for p in aug if p not in mar):,.0f}")

print("\n  top 30 changed-text parts by billed euro:")
for pn in sorted(diff, key=lambda p: -money.get(p, 0))[:30]:
    print(f"    EUR {money.get(pn,0):>10,.0f}  {pn}  "
          f"{mar[pn]['desc'][:34]:<34} -> {aug[pn][:34]:<34} | node stays "
          f"{mar[pn]['l2']} > {mar[pn]['l3']}")

with OUT.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["part_number", "description_classified_mar2026", "description_live_aug2026",
                "level1", "level2", "level3", "l12m_eur"])
    for pn in sorted(diff, key=lambda p: -money.get(p, 0)):
        w.writerow([pn, mar[pn]["desc"], aug[pn], mar[pn]["l1"], mar[pn]["l2"],
                    mar[pn]["l3"], f"{money.get(pn,0):.2f}"])
print(f"\n-> {OUT}")

# ---- and the specific FILTER; ACL case
print("\n  the 'FILTER; ACL' clash, explained part by part:")
acl = [pn for pn in both if aug[pn].upper() == "FILTER; ACL"]
c = collections.Counter(mar[pn]["l2"] for pn in acl)
print(f"    {len(acl)} part numbers now read 'FILTER; ACL'; assigned groups: {dict(c)}")
for pn in sorted(acl, key=lambda p: -money.get(p, 0))[:12]:
    print(f"      EUR {money.get(pn,0):>9,.0f}  {pn}  classified text "
          f"{mar[pn]['desc'][:38]:<38} -> {mar[pn]['l2']} > {mar[pn]['l3']}")
