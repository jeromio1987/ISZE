#!/usr/bin/env python3
"""How big is the part-year effect on the pack's category-gap chart?

`pms_opportunity_matrix.csv` is written by build_pms_opportunity_matrix.py from
pms_capture_by_db_year.csv, whose expected_qty is fleet x services/year - a
FULL-YEAR denominator (verified identical 2023-2026 below). For 2026 it pairs that
with eight months of actual revenue.

`revenue_gap_quotable` is NOT a period guard: it is the avg-price firewall from
DECISIONS.md. Checked here, and True on nearly every 2026 row.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"

cap = pd.read_csv(DER / "pms_capture_by_db_year.csv")
c = cap[cap["line_type"] == "total"]
print("pms_capture_by_db_year.csv, expected_qty by year (the denominator):")
print(c.groupby("year").agg(expected_qty=("expected_qty", "sum"),
                            actual_qty=("actual_qty", "sum")).to_string())
print("\n   IUK expected_qty by year:")
print(c[c["distributor_code"] == "IUK"].groupby("year")["expected_qty"].sum().to_string())

op = pd.read_csv(DER / "pms_opportunity_matrix.csv")
print("\n" + "=" * 90)
print("pms_opportunity_matrix.csv -- revenue_gap_eur, network total by year")
print("=" * 90)
g = op.groupby("year").agg(revenue_gap_eur=("revenue_gap_eur", "sum"),
                           quotable_eur=("revenue_gap_eur",
                                         lambda s: s[op.loc[s.index,
                                                            "revenue_gap_quotable"]].sum()),
                           rows=("revenue_gap_eur", "size"))
print(g.round(0).to_string())

y25 = float(g.loc[2025, "revenue_gap_eur"])
y26 = float(g.loc[2026, "revenue_gap_eur"])
print(f"\n   2026 as printed / 2025            : {y26/y25:.3f}  "
      f"({y26:,.0f} vs {y25:,.0f})")
print(f"   2026 gap scaled to 12 months (x12/8): {y26*12/8:,.0f}  "
      f"-> {y26*12/8/y25:.3f} of 2025")
print(f"   so the printed 2026 gap is understated by roughly "
      f"{(1 - 8/12)*100:.0f}% of what a full year at the same rate would show")
print("   (the gap is TAM minus actual revenue; eight months of revenue inflates it)")

print("\n   is revenue_gap_quotable a period guard? -> grouped by year:")
print(op.groupby(["year", "revenue_gap_quotable"]).size().to_string())
print("\n   2026 rows where quotable=True (a reader would chart these):",
      int(((op["year"] == 2026) & op["revenue_gap_quotable"]).sum()), "of",
      int((op["year"] == 2026).sum()))

print("\n" + "=" * 90)
print("The pack's own instruction")
print("=" * 90)
howto = (ROOT / "09_meetings" / "BVDB_PBI_Data_Upload_2026-09-23" / "00_START_HERE" /
         "HOW_TO.md").read_text(encoding="utf-8")
for ln in howto.splitlines():
    if "opportunity" in ln.lower() or "Top category gaps" in ln:
        print("   ", ln.strip())
print("\n   does any pack file state that the gap is 8-month actual vs full-year expected?")
for rel in ("00_START_HERE/HOW_TO.md", "00_START_HERE/MANIFEST.csv",
            "00_START_HERE/README.txt"):
    t = (ROOT / "09_meetings" / "BVDB_PBI_Data_Upload_2026-09-23" / rel).read_text(
        encoding="utf-8", errors="replace").lower()
    print(f"   {rel}: 'expected' mentioned = {'expected' in t}; "
          f"'full-year' = {'full-year' in t or 'full year' in t}")
