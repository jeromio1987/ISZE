#!/usr/bin/env python3
"""Quantify the part-year effect on the category gap, using the real formula.

From modules/pms_engine.py:
    avg_sp_eur      = actual_rev_eur / actual_qty          (8-month unit price)
    revenue_gap_eur = max(expected_qty - actual_qty, 0) * avg_sp_eur

expected_qty is fleet x services/year -> a FULL-YEAR denominator (verified identical
in 2023, 2024, 2025 and 2026). For 2026, actual_qty is eight months. So the bracket
is (12-month expectation - 8-month actual), which is larger than the honest
full-year bracket (12 - 12): the printed 2026 gap is OVERSTATED.

The like-for-like comparator puts the expectation on the same eight months. That is
a pro-rata of the expectation, which is an assumption, so it is labelled as one and
is not written into any file.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"

cap = pd.read_csv(DER / "pms_capture_by_db_year.csv")
c = cap[cap["line_type"] == "total"].copy()
c["avg_sp"] = np.where(c["actual_qty"] > 0,
                       c["actual_rev_eur"] / c["actual_qty"], np.nan)

op = pd.read_csv(DER / "pms_opportunity_matrix.csv")
print("printed revenue_gap_eur, network total by year:")
t = op.groupby("year")["revenue_gap_eur"].sum()
print(t.round(0).to_string())

print("\n2026 against 2025 as printed: "
      f"{t.loc[2026]:,.0f} vs {t.loc[2025]:,.0f} -> "
      f"{t.loc[2026]/t.loc[2025]:.3f}x")

# like-for-like: eight twelfths of the expectation against the eight months actual
c26 = c[c["year"] == 2026].copy()
c26["gap_l4l"] = np.maximum(c26["expected_qty"] * (8 / 12) - c26["actual_qty"], 0) * c26["avg_sp"]
l4l = float(c26["gap_l4l"].sum())
c25 = c[c["year"] == 2025].copy()
c25["gap_l4l"] = np.maximum(c25["expected_qty"] - c25["actual_qty"], 0) * c25["avg_sp"]
l4l25 = float(c25["gap_l4l"].sum())
print(f"\nlike-for-like 2026 (expectation x 8/12, an ASSUMPTION):  {l4l:,.0f}")
print(f"2025 on its own full-year basis:                          {l4l25:,.0f}")
print(f"as printed, 2026 reads {t.loc[2026]/t.loc[2025]:.2f}x of 2025 (looks slightly worse)")
print(f"like-for-like, 2026 reads {l4l/l4l25:.2f}x of 2025 (looks better)")

over = t.loc[2026] - l4l
print(f"\nthe printed 2026 gap is overstated by about EUR {over:,.0f} "
      f"({over/t.loc[2026]*100:.0f}% of the printed figure), by the eight missing months")

# every 2026 row carries the same 8-month problem? check the bulk of them
print("\n2026 rows: revenue_gap_eur > 0:", int((op[(op.year == 2026)].revenue_gap_eur > 0).sum()),
      "of", int((op.year == 2026).sum()))
print("\nIUK 2026 vs 2025, top categories by printed gap:")
sel = op[op["distributor_code"] == "IUK"]
p = sel.pivot_table(index="pms_category", columns="year", values="revenue_gap_eur",
                    aggfunc="sum")
print(p[[2025, 2026]].sort_values(2026, ascending=False).head(8).round(0).to_string())

print("\nany period column in the file?  period_basis:", "period_basis" in op.columns)
print("expected_qty per year (all markets, all categories):")
print(c.groupby("year")["expected_qty"].sum().to_string())
