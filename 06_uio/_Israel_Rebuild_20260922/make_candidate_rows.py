"""Produce the candidate rebuilt Israel rows for UIO V20, in the workbook's own row shape.

Rows in the live workbook (sheet '1.UIO Overview'):
  row 7  ISRAEL CV LD       - whole N-series, ministry bands 6.5-7.5 t
  row 8  ISRAEL CV MD       - ministry bands 7.6-10 t + 10.1-12 t (V18 folds 12 t in here)
  (no row)                  - ministry band 12.1-16 t, 227 trucks, has nowhere to go

This writes the rebuilt candidate for all three.
"""
from __future__ import annotations

import csv
from pathlib import Path

BASE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Israel_Rebuild_20260922")
SRC = BASE / "rebuild_outputs" / "rebuilt_israel_parc_by_class.csv"
OUT = BASE / "rebuild_outputs"

CLS = ["6.5-7.5 t", "7.6-10 t", "10.1-12 t", "12.1-16 t"]

rows = list(csv.DictReader(SRC.open(encoding="utf-8")))
by_year = {int(r["year"]): r for r in rows}

YEARS = list(range(1994, 2031))
HEADER = (["year", "LD_row_6.5-7.5t", "MD_row_7.6-10t", "MD_row_10.1-12t",
           "NEW_row_12.1-16t", "rebuilt_total", "gov_total", "delta_vs_gov", "basis"])

with (OUT / "rebuild_israel_rows_for_v20.csv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(HEADER)
    for y in YEARS:
        r = by_year[y]
        ld = float(r["6.5-7.5 t"])
        md_a = float(r["7.6-10 t"])
        md_b = float(r["10.1-12 t"])
        hd = float(r["12.1-16 t"])
        tot = ld + md_a + md_b + hd
        w.writerow([y, round(ld), round(md_a), round(md_b), round(hd), round(tot),
                    r["gov_total"] or "", (round(tot - float(r["gov_total"])) if r["gov_total"] else ""),
                    r["basis"]])

print("candidate rows written to:", OUT / "rebuild_israel_rows_for_v20.csv")
print()
print(f"{'year':>6}{'LD row':>10}{'MD row':>10}{'NEW 12.1-16t':>15}{'total':>9}{'gov':>9}{'delta':>8}")
for y in (2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027, 2030):
    r = by_year[y]
    ld = round(float(r["6.5-7.5 t"]))
    md = round(float(r["7.6-10 t"]) + float(r["10.1-12 t"]))
    hd = round(float(r["12.1-16 t"]))
    tot = ld + md + hd
    g = r["gov_total"]
    print(f"{y:>6}{ld:>10,}{md:>10,}{hd:>15,}{tot:>9,}{(f'{int(g):,}' if g else '—'):>9}"
          f"{(f'{tot - int(g):+,}' if g else '—'):>8}")
