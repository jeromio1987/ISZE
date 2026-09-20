#!/usr/bin/env python3
"""Audit step 3: read the classified workbook's own notes + taxonomy sheet, and
dump the full PR00 price file (description, price, HS commodity code, origin,
figure) to a fast CSV so later audit steps do not re-parse 12 MB of xlsx."""
from __future__ import annotations
from pathlib import Path
import csv, openpyxl

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PRC = ISZE / "01_data" / "01_Pricing"
D = ISZE / "01_data" / "00_derived"
CLS_WB = PRC / "IE40 Price list as of 13.03.2026 PR00_3_level_classified_GPT.xlsx"
PRICE_WB = PRC / "Price_file_PR00_IE40_20260810.xlsx"
OUT = D / "_audit_cls_pr00_flat.csv"

# ------------------------------------------------ the classifier's own notes
print("=" * 78)
print("CLASSIFIED WORKBOOK - its own stated method and taxonomy")
wb = openpyxl.load_workbook(CLS_WB, read_only=True, data_only=True)
ws = wb["3-Level Summary"]
print("\n-- 3-Level Summary (full) --")
for row in ws.iter_rows(values_only=True):
    vals = [("" if c is None else str(c)) for c in row]
    if any(v.strip() for v in vals):
        print("   ", " | ".join(v for v in vals if v.strip()))

ws = wb["3-Level Taxonomy"]
print("\n-- 3-Level Taxonomy (full, 172 leaves) --")
tax = []
for i, row in enumerate(ws.iter_rows(values_only=True)):
    if i < 2:
        if row and row[0]:
            print("   note:", row[0])
        continue
    if i == 2:
        continue
    if row and row[0]:
        tax.append(tuple("" if c is None else str(c) for c in row[:4]))
print(f"   {len(tax)} taxonomy leaves")
for t in tax:
    print(f"   {t[3]:>7}  {t[0]} > {t[1]} > {t[2]}")
wb.close()

# --------------------------------------------------------- flatten the price
print("\n" + "=" * 78)
print("PR00 price file -> flat csv")
wb = openpyxl.load_workbook(PRICE_WB, read_only=True, data_only=True)
ws = wb["Sheet1"]
it = ws.iter_rows(values_only=True)
hdr = [("" if c is None else str(c).strip()) for c in next(it)]
print("header:", hdr)
idx = {h: i for i, h in enumerate(hdr)}
need = ["P/N", "Newest P/N", "Description", "Price", "Commodity Code",
        "Country of Origin", "Fig No.", "Key No.", "Weight", "ABC Code"]
missing = [c for c in need if c not in idx]
if missing:
    print("MISSING COLUMNS:", missing)

n = 0
with OUT.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["pn", "newest_pn", "description", "price_eur", "hs_code",
                "origin", "fig_no", "key_no", "weight_kg", "abc"])
    for row in it:
        if row is None or row[idx["P/N"]] is None:
            continue
        def g(c):
            v = row[idx[c]] if c in idx else None
            return "" if v is None else str(v).strip()
        pn = g("P/N")
        if pn.isdigit():
            pn = pn.zfill(10)
        w.writerow([pn, g("Newest P/N"), g("Description"),
                    g("Price").replace(",", "."), g("Commodity Code"),
                    g("Country of Origin"), g("Fig No."), g("Key No."),
                    g("Weight").replace(",", "."), g("ABC Code")])
        n += 1
wb.close()
print(f"wrote {n:,} rows -> {OUT}")
