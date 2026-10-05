"""Verify the two largest claims from the action-points analysis."""

import json
import re
from pathlib import Path

import pandas as pd

DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
SALES = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales")
norm = lambda x: (str(x).strip().lstrip("0") or "0")  # noqa: E731

print("=" * 96)
print("A. ITUK N-SERIES — do the two clocks really disagree by EUR 290,032?")
print("=" * 96)
ev = pd.read_csv(DER / "pms_family_evolution_both_clocks.csv")
it = ev[(ev.distributor_code == "ITUK") & (ev.family == "n_series_truck")]
for clock in ("CY", "FY"):
    g = it[it.clock == clock].groupby("period").billed_eur.sum().sort_index()
    if g.empty:
        continue
    print(f"  {clock}:")
    for yr, v in g.items():
        print(f"     {yr}: EUR {v:,.0f}")
    yrs = list(g.index)
    if len(yrs) >= 2:
        print(f"     move {yrs[-2]} -> {yrs[-1]}: EUR {g.iloc[-1]-g.iloc[-2]:,.0f}")

print()
print("=" * 96)
print("B. IUK LIGHT VEHICLE — EUR 186,000, and did its fleet or sold_to move?")
print("=" * 96)
iuk = ev[(ev.distributor_code == "IUK") & (ev.family == "light_vehicle") & (ev.clock == "CY")]
g = iuk.groupby("period").billed_eur.sum().sort_index()
print("  billed euro by year:")
for yr, v in g.items():
    print(f"     {yr}: EUR {v:,.0f}")

uio = pd.read_csv(DER / "uio_by_market_type_year.csv")
f = uio[(uio.distributor_code == "IUK") & (uio.model_type == "LCV")]
print("  LCV fleet (IUK):")
for yr, v in f.groupby("year").uio_units.sum().items():
    if 2023 <= yr <= 2026:
        print(f"     {yr}: {v:,.0f}")

print()
print("  per-vehicle on those two:")
for yr in (2024, 2025):
    if yr in g.index:
        fl = f[f.year == yr].uio_units.sum()
        print(f"     {yr}: EUR {g[yr]:,.0f} / {fl:,.0f} = EUR {g[yr]/fl:,.2f}")

print()
print("  sold_to code stability check — IUK codes in the sales fact:")
sf = pd.read_parquet(DER / "sales_fact.parquet")
sf["pn"] = sf.part_number.map(norm)
dim = pd.read_csv(DER / "distributor_dimension.csv")
m = dict(zip(dim.sold_to_sap, dim.distributor_code))
sf["db"] = sf.sold_to_sap.map(m)
sf["yr"] = pd.to_datetime(sf.billing_date, errors="coerce").dt.year
iuk_codes = sf[(sf.db == "IUK") & (sf.yr.isin([2024, 2025]))]
print(iuk_codes.groupby(["yr", "sold_to_sap"]).size().to_string())

print()
print("=" * 96)
print("C. DID THE PAGE GET REBUILT AT 13:20?")
print("=" * 96)
for f_ in sorted(SALES.glob("ISZE_PMS_Family_Evolution*")):
    print(f"  {f_.name:52s} {f_.stat().st_size/1024:8,.0f} KB  "
          f"{pd.Timestamp(f_.stat().st_mtime, unit='s').strftime('%H:%M:%S')}")
