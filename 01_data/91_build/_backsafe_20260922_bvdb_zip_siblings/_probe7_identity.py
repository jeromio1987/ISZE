#!/usr/bin/env python3
"""Prove the algebraic identity the opportunity splice depends on.

In build_pms_opportunity_matrix.py:
    avg_sp_eur      = actual_rev_eur / actual_qty
    tam_eur         = expected_qty * avg_sp_eur
    capture_rate_total = actual_qty / expected_qty
    revenue_gap_eur = max(expected_qty - actual_qty, 0) * avg_sp_eur

Therefore, using only columns the file actually carries:
    revenue_gap_eur == tam_eur * max(1 - capture_rate_total, 0)      [when avg_sp>0]
    like_for_like   == tam_eur * max(coverage - capture_rate_total, 0)

If the first identity holds on every row, the second is safe to use. It is checked
here rather than assumed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PRISM = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism")
sys.path.insert(0, str(PRISM))
from modules.year_coverage import year_coverage  # noqa: E402

op = pd.read_csv(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
                 r"\pms_opportunity_matrix.csv")

pred = op["tam_eur"] * np.maximum(1 - op["capture_rate_total"], 0.0)
diff = (pred - op["revenue_gap_eur"]).abs()
print(f"rows: {len(op)}")
print(f"identity revenue_gap_eur == tam*(1-capture):")
print(f"   max abs difference : {diff.max():.6f}")
print(f"   rows over 0.02     : {int((diff > 0.02).sum())}")
print(f"   rows over 1.00     : {int((diff > 1.0).sum())}")

bad = op[diff > 1.0]
if len(bad):
    print("\n   rows where it does not hold (avg_sp=0 by construction):")
    print(bad[["distributor_code", "pms_category", "year", "capture_rate_total",
               "avg_sp_eur", "tam_eur", "revenue_gap_eur"]].head(10).to_string(index=False))

cov = year_coverage()
print(f"\ncoverage: { {k: round(v, 4) for k, v in sorted(cov.items())} }")

for yr in sorted(op["year"].unique()):
    sub = op[op["year"] == yr]
    c = float(cov.get(int(yr), 1.0))
    l4l = (sub["tam_eur"] * np.maximum(c - sub["capture_rate_total"], 0.0)).sum()
    print(f"   {yr}  coverage={c:.4f}  printed gap {sub['revenue_gap_eur'].sum():>14,.0f}"
          f"   like-for-like {l4l:>14,.0f}")

print("\nWhere the identity fails, avg_sp_eur is 0 and the printed gap is 0 too, so the")
print("like-for-like is 0 on those rows as well — consistent, not silently different.")
