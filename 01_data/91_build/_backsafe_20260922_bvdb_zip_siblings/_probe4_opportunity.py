#!/usr/bin/env python3
"""READ-ONLY follow-up on the probe finding: are the 2026 category gaps in
pms_opportunity_matrix.csv resting on a full-year denominator, and is that
disclosed anywhere the pack's reader would look?"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PACK = ROOT / "09_meetings" / "BVDB_PBI_Data_Upload_2026-09-23"

op = pd.read_csv(DER / "pms_opportunity_matrix.csv")
print("pms_opportunity_matrix.csv")
print("   columns:", list(op.columns))
print("   rows per year:", op.groupby("year").size().to_dict())

for c in ("expected_qty", "expected_rev_eur", "revenue_gap_eur", "revenue_gap_quotable",
          "gap_eur", "actual_rev_eur"):
    if c in op.columns:
        print(f"   {c}: non-null {int(op[c].notna().sum())}/{len(op)}")

if "expected_qty" in op.columns:
    print("\n   expected_qty total by year (is the denominator full-year?):")
    print(op.groupby("year")["expected_qty"].sum().to_string())

if "revenue_gap_quotable" in op.columns:
    print("\n   revenue_gap_quotable by year:")
    print(op.groupby(["year", "revenue_gap_quotable"]).size().to_string())

print("\n   does the file itself carry a period column?")
print("   period_basis present:", "period_basis" in op.columns)

print("\n" + "=" * 80)
print("Disclosure check: is the 2026 basis stated anywhere the reader would look?")
print("=" * 80)
for rel in ("00_START_HERE/HOW_TO.md", "00_START_HERE/MANIFEST.csv",
            "00_START_HERE/README.txt", "00_START_HERE/MEETING_BRIEF_Jerome.md"):
    t = (PACK / rel).read_text(encoding="utf-8", errors="replace")
    hits = [i + 1 for i, ln in enumerate(t.splitlines())
            if "opportunity_matrix" in ln or "category gap" in ln.lower()]
    print(f"   {rel}: lines mentioning the gap file / category gaps -> {hits}")
    for i in hits:
        print(f"      {t.splitlines()[i-1][:200]}")
