"""Print the before/after table for the AdBlue factor change.

Compares the two saved copies of pms_capture_by_db_year.csv, both produced by the same build chain —
one with urea_filter left at 1.0 (the old value), one with the sourced 0.20 N-series / 0.375 F-series.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

BUILD = Path(__file__).resolve().parent
OUT = BUILD / "_urea_before_after.txt"

base_cap = pd.read_csv(BUILD / "_state_base_pms_capture_by_db_year.csv")
aft_cap = pd.read_csv(BUILD / "_state_after_pms_capture_by_db_year.csv")

bf = base_cap[base_cap.line_type == "total"].copy()
af = aft_cap[aft_cap.line_type == "total"].copy()

lines: list[str] = []


def w(s: str = "") -> None:
    lines.append(s)
    print(s)


w("=" * 118)
w("ADBLUE (urea) FILTER — before and after the interval fix")
w("old value 1.0 (one per service visit)  ->  0.20 N-series / 0.375 F-series")
w("=" * 118)

b = bf[bf.pms_category == "urea_filter"].copy()
a = af[af.pms_category == "urea_filter"].copy()
m = b.merge(a, on=["distributor_code", "year"], suffixes=("_b", "_a")).sort_values(
    ["distributor_code", "year"])

w(f"{'market':10s} {'year':>5s} {'expected before':>16s} {'expected after':>15s} "
  f"{'x':>6s} {'capture before':>15s} {'capture after':>14s}  moved")
for r in m.itertuples():
    if r.expected_qty_b == 0 and r.expected_qty_a == 0:
        continue
    ratio = (r.expected_qty_b / r.expected_qty_a) if r.expected_qty_a else float("nan")
    mv = abs(r.expected_qty_b - r.expected_qty_a) > 0.005
    w(f"{r.distributor_code:10s} {int(r.year):5d} {r.expected_qty_b:16,.1f} "
      f"{r.expected_qty_a:15,.1f} {ratio:6.2f} {r.capture_rate_b*100:14.2f}% "
      f"{r.capture_rate_a*100:13.2f}%  {'YES' if mv else ''}")

moved = m[(m.expected_qty_b - m.expected_qty_a).abs() > 0.005]
w()
w(f"market-years listed: {len(m)}   market-years where the AdBlue expectation moved: {len(moved)}")
w(f"markets whose AdBlue denominator changed: {', '.join(sorted(moved.distributor_code.unique()))}")
unchanged = sorted(set(m.distributor_code.unique()) - set(moved.distributor_code.unique()))
w(f"markets untouched: {', '.join(unchanged)}")

w()
w("=" * 118)
w("DID ANY OTHER CATEGORY MOVE? (it must not)")
w("=" * 118)
bb = bf.groupby("pms_category").expected_qty.sum()
aa = af.groupby("pms_category").expected_qty.sum()
others_same = True
for cat in sorted(set(bb.index) | set(aa.index)):
    x = float(bb.get(cat, 0.0))
    y = float(aa.get(cat, 0.0))
    same = abs(x - y) < 0.005
    if not same and cat != "urea_filter":
        others_same = False
    w(f"  {cat:24s} before {x:14,.1f}  after {y:14,.1f}  "
      f"{'same' if same else 'MOVED by ' + format(y - x, ',.1f')}")
w(f"  -> every category other than urea_filter unchanged: {others_same}")

w()
w("=" * 118)
w("NETWORK TOTALS (all 14 families, all years)")
w("=" * 118)
for tag, df in (("before", bf), ("after", af)):
    u = df[df.pms_category == "urea_filter"]
    w(f"  {tag:6s}  all expected {df.expected_qty.sum():14,.0f}   "
      f"all gap EUR {df.revenue_gap_eur.sum():16,.0f}   "
      f"urea expected {u.expected_qty.sum():12,.0f}   "
      f"urea gap EUR {u.revenue_gap_eur.sum():14,.0f}")

w()
w("=" * 118)
w("PER-MARKET TOTAL CAPTURE 2025, all 14 families — did any published headline move?")
w("=" * 118)
b25 = bf[bf.year == 2025].groupby("distributor_code").apply(
    lambda g: g.actual_qty.sum() / g.expected_qty.sum() if g.expected_qty.sum() else float("nan"),
    include_groups=False)
a25 = af[af.year == 2025].groupby("distributor_code").apply(
    lambda g: g.actual_qty.sum() / g.expected_qty.sum() if g.expected_qty.sum() else float("nan"),
    include_groups=False)
w(f"  {'market':10s} {'before':>9s} {'after':>9s} {'delta pp':>9s}")
for k in sorted(set(b25.index) | set(a25.index)):
    x = float(b25.get(k, float("nan")))
    y = float(a25.get(k, float("nan")))
    w(f"  {k:10s} {100*x:8.2f}% {100*y:8.2f}% {100*(y-x):8.2f}")

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\nwritten ->", OUT)
