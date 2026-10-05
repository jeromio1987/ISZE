"""Resolve a contradiction: the audit file and the report give different move percentages.

Audit file says Ireland +23.12% and Belgium -3.18%.
Report says Ireland +6.47% and Belgium +0.52%.

Compute both from the actual files: the pre-change baseline versus the current live file.
"""

import pandas as pd

DER = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
base = pd.read_csv(DER + r"\pms_capture_by_db_year.csv.bak_pre_n35_ratio_20260918")
live = pd.read_csv(DER + r"\pms_capture_by_db_year.csv")

k = ["distributor_code", "pms_category", "year", "line_type"]
m = base.merge(live, on=k, suffixes=("_base", "_live"))

print("=" * 100)
print("WHOLE expected demand, market total, all years: baseline -> live")
print("=" * 100)
t = m[m.line_type == "total"]
g = t.groupby("distributor_code").agg(
    base=("expected_qty_base", "sum"), live=("expected_qty_live", "sum")
).round(0)
g["move_pct"] = (100 * (g.live / g.base - 1)).round(2)
print(g.sort_values("move_pct", ascending=False).to_string())

print()
print("=" * 100)
print("2025 oil filter only")
print("=" * 100)
o = t[(t.year == 2025) & (t.pms_category == "oil_filter")].set_index("distributor_code")
oo = o[["expected_qty_base", "expected_qty_live", "capture_rate_base", "capture_rate_live"]].copy()
oo["move_pct"] = (100 * (oo.expected_qty_live / oo.expected_qty_base - 1)).round(2)
oo["cover_base_pct"] = (100 * oo.capture_rate_base).round(1)
oo["cover_live_pct"] = (100 * oo.capture_rate_live).round(1)
print(oo[["expected_qty_base", "expected_qty_live", "move_pct", "cover_base_pct",
          "cover_live_pct"]].to_string())

print()
print("=" * 100)
print("THE TWO CLAIMS, SIDE BY SIDE")
print("=" * 100)
ire = g.loc["IRELAND"] if "IRELAND" in g.index else None
bel = g.loc["BELGIUM"] if "BELGIUM" in g.index else None
print(f"  Ireland : audit file says +23.12% | report says +6.47% | DATA SAYS "
      f"{ire['move_pct'] if ire is not None else 'n/a'}%")
print(f"  Belgium : audit file says  -3.18% | report says +0.52% | DATA SAYS "
      f"{bel['move_pct'] if bel is not None else 'n/a'}%")

print()
print("=" * 100)
print("Why -3.18% is possible for Belgium: share FELL (0.9180 -> 0.8571)")
print("=" * 100)
from pathlib import Path
sh = pd.read_csv(Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism\data"
                      r"\uio_ld_n35_share.csv"))
print(sh[["distributor_code", "n35_share", "basis"]].to_string(index=False))
print()
print("  cv_std = 0.5 x (1 + share):")
for _, r in sh.iterrows():
    s = float(r["n35_share"])
    print(f"    {r['distributor_code']:10s} share {s:.4f} -> cv_std {0.5*(1+s):.4f}")
