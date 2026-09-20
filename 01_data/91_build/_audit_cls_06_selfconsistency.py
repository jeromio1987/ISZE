#!/usr/bin/env python3
"""Audit step 6: test the classifier against its OWN stated method.

The source workbook says: "Generated from Description field using rule-based
mapping." A rule-based mapping on a string is a function: the same input string
must produce the same output. So every case where one identical Description
string carries two different nodes is a self-contradiction of the stated method
- measured on the workbook's own Description column, not on any later file.
"""
from __future__ import annotations
import collections, csv
from pathlib import Path
import openpyxl

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
CLS_WB = ISZE / "01_data" / "01_Pricing" / \
    "IE40 Price list as of 13.03.2026 PR00_3_level_classified_GPT.xlsx"
D = ISZE / "01_data" / "00_derived"
OUT = D / "_audit_cls_selfcontradictions.csv"

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
    recs.append({
        "pn": g("P/N").zfill(10) if g("P/N").isdigit() else g("P/N"),
        "desc": g("Description"),
        "l1": g("Level 1 Family"), "l2": g("Level 2 Group"), "l3": g("Level 3 Type"),
        "fig": g("Fig No."), "key": g("Key No."), "price": g("Price"),
    })
wb.close()
print(f"workbook data rows: {len(recs):,}")

# euro weight
money = {}
for r in csv.DictReader((D / "_audit_cls_desc_spine.csv").open(encoding="utf-8", newline="")):
    money[r["part_number"]] = float(r["l12m_eur"] or 0)
def eur(pn): return money.get(pn, 0.0)
tot_eur = sum(money.values())

# ---------------------------------------------- byte-identical description test
by = collections.defaultdict(list)
for r in recs:
    if r["desc"]:
        by[r["desc"]].append(r)

def report(level):
    bad = {d: v for d, v in by.items() if len({x[level] for x in v}) > 1}
    pn = sum(len(v) for v in bad.values())
    e = sum(eur(x["pn"]) for v in bad.values() for x in v)
    print(f"  identical description, different {level}: {len(bad):,} descriptions, "
          f"{pn:,} part numbers, EUR {e:,.0f} ({100*e/tot_eur:.2f}% of billed)")
    return bad

print(f"\ndistinct non-empty descriptions: {len(by):,}")
print("SELF-CONTRADICTION OF THE STATED METHOD (byte-identical Description string)")
bad1 = report("l1"); bad2 = report("l2"); bad3 = report("l3")

print("\n  top 35 by euro, Level 1 contradictions (the commercial axis):")
for d, v in sorted(bad1.items(), key=lambda kv: -sum(eur(x['pn']) for x in kv[1]))[:35]:
    c = collections.Counter(x["l1"] for x in v)
    print(f"    EUR {sum(eur(x['pn']) for x in v):>10,.0f}  {len(v):>4} PNs  {d[:40]:<40} -> "
          + ", ".join(f"{a} {b}" for a, b in c.most_common(4)))

print("\n  top 35 by euro, Level 3 contradictions:")
for d, v in sorted(bad3.items(), key=lambda kv: -sum(eur(x['pn']) for x in kv[1]))[:35]:
    c = collections.Counter(x["l3"] for x in v)
    print(f"    EUR {sum(eur(x['pn']) for x in v):>10,.0f}  {len(v):>4} PNs  {d[:40]:<40} -> "
          + ", ".join(f"{a} {b}" for a, b in c.most_common(4)))

with OUT.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["description", "part_number", "level1", "level2", "level3",
                "fig_no", "key_no", "l12m_eur", "contradiction_level",
                "n_pn_same_desc", "variants_at_level"])
    for lvl, bad in (("level1", bad1), ("level2", bad2), ("level3", bad3)):
        for d, v in bad.items():
            var = sorted({x[{"level1": "l1", "level2": "l2", "level3": "l3"}[lvl]] for x in v})
            for x in v:
                w.writerow([d, x["pn"], x["l1"], x["l2"], x["l3"], x["fig"], x["key"],
                            f"{eur(x['pn']):.2f}", lvl, len(v), " | ".join(var)])
print(f"\n-> {OUT}")

# ------------------------------------------- is the minority always a singleton?
print("\nshape of the contradictions at Level 2")
sizes = collections.Counter()
for d, v in bad2.items():
    c = collections.Counter(x["l2"] for x in v)
    minority = sum(c.values()) - c.most_common(1)[0][1]
    sizes[minority] += 1
for k in sorted(sizes):
    print(f"  {sizes[k]:>4} descriptions have {k} part number(s) off the majority node")
