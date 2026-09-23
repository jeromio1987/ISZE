"""Task 5 evidence: the -32.6% per-truck figure, and where else the pack compares
a part year against a full year. Read-only."""
from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PACK = ROOT / "09_meetings/BVDB_PBI_Data_Upload_2026-09-23"

print("=" * 96)
print("A. Parts billed per truck, pack's own figures")
g = pd.read_csv(PACK / "02_GPS/gps_spu_by_distributor.csv", dtype={"year": str})
for y in ("2025", "2026"):
    s = g[g.year == y]
    sales = s.total_sales_eur.sum()
    uio = s.uio_units.sum()
    print(f"  {y}: sales=EUR {sales:,.2f}  uio={uio:,.0f}  per truck=EUR {sales / uio:,.2f}")
s25 = g[g.year == "2025"]
s26 = g[g.year == "2026"]
p25 = s25.total_sales_eur.sum() / s25.uio_units.sum()
p26 = s26.total_sales_eur.sum() / s26.uio_units.sum()
print(f"  implied movement as printed: {(p26 / p25 - 1) * 100:+.1f}%")
ann = s26.total_sales_eur.sum() * 12 / 8
print(f"  2026 annualised (x12/8): EUR {ann:,.2f} -> EUR {ann / s26.uio_units.sum():,.2f}/truck")
print(f"  annualised movement: {((ann / s26.uio_units.sum()) / p25 - 1) * 100:+.1f}%")

# same-months check on sales_fact
sf = pd.read_parquet(ROOT / "01_data/00_derived/sales_fact.parquet")
sf["billing_date"] = pd.to_datetime(sf["billing_date"], errors="coerce")
m = sf["billing_date"].dt.month
for y in (2025, 2026):
    sel = sf[(sf["billing_date"].dt.year == y) & (m <= 8)]
    print(f"  sales_fact Jan-Aug {y}: EUR {sel['net_sales_value'].sum():,.2f}")
print(f"  sales_fact max billing_date: {sf['billing_date'].max().date()}")

print("=" * 96)
print("B. other files in the pack that mention a year-on-year comparison or a prior year")
needles = ("yoy", "prior year", "vs prior", "previous year", "growth", "decline", "vs 20")
for p in sorted(PACK.rglob("*")):
    if not p.is_file():
        continue
    if p.suffix.lower() in (".csv",):
        df = pd.read_csv(p, dtype=str, nrows=0)
        hits = [c for c in df.columns if any(n in c.lower() for n in needles)]
        if hits:
            print(f"  {p.relative_to(PACK)}: columns {hits}")
    elif p.suffix.lower() in (".md", ".txt"):
        txt = p.read_text(encoding="utf-8", errors="replace").lower()
        hits = [n for n in needles if n in txt]
        if hits:
            print(f"  {p.relative_to(PACK)}: text mentions {hits}")

print("=" * 96)
print("C. target_spend_waterfall years present (2026?)")
w = pd.read_csv(PACK / "02_GPS/target_spend_waterfall.csv", dtype={"year": str})
print(f"  years: {sorted(w.year.unique())}  rows={len(w)}")
print(f"  columns: {list(w.columns)}")
