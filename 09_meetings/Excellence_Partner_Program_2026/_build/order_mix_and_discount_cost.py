"""Order-type mix FY2026 per distributor + cost of a stock-order discount (Excellence Partner analysis).

Reads derived files only (no raw SAP billing):
  01_data/00_derived/sales_fact.parquet          FY2026 = 1 Apr 2025 - 31 Mar 2026
  01_data/00_derived/distributor_dimension.csv   sold-to -> distributor
  01_data/00_derived/q1fy2027_export_with_saty.csv  SAP cost per line -> indicative gross margin

Run from the ISZE root:  python 09_meetings/Excellence_Partner_Program_2026/_build/order_mix_and_discount_cost.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DER = ROOT / "01_data" / "00_derived"
OUT = Path(__file__).resolve().parent / "order_mix_fy2026.csv"
NOT_NETWORK = {"not_a_customer", "excluded_non_parts", "excluded_entity", "direct_account"}

dim = pd.read_csv(DER / "distributor_dimension.csv")
db_of = dict(zip(dim.sold_to_sap, dim.distributor_code.fillna(dim.network_role)))

f = pd.read_parquet(DER / "sales_fact.parquet")
f["billing_date"] = pd.to_datetime(f["billing_date"])
f = f[(f.billing_date >= "2025-04-01") & (f.billing_date < "2026-04-01")]
f = f[~f.saty.isin(["CR", "RE", "G2"])]
f = f[~f.part_number.astype(str).str.upper().isin(["TRANSPORT", "REBATE"])]
f["db"] = f.sold_to_sap.map(db_of).fillna(f.sold_to_sap.astype(str))
f = f[~f.db.isin(NOT_NETWORK)]

p = f.pivot_table(index="db", columns="saty", values="net_sales_value", aggfunc="sum").fillna(0)
p["total"] = p.sum(axis=1)
out = pd.DataFrame({"fy2026_billed_eur": p.total.round(0)})
for c in ["SOR", "PRD", "VOR", "RUSH"]:
    out[f"{c}_share"] = (p.get(c, 0) / p.total).round(3)
out["SOR_eur"] = p.get("SOR", 0).round(0)
out = out.sort_values("fy2026_billed_eur", ascending=False)
out.to_csv(OUT)

q = pd.read_csv(DER / "q1fy2027_export_with_saty.csv", low_memory=False)
q = q[(q.EUR_Amount > 0) & ~q.Material.astype(str).str.upper().isin(["TRANSPORT", "REBATE"])]
gm_all = 1 - q.EUR_Cost.sum() / q.EUR_Amount.sum()
sor = q[q.SaTy == "SOR"]
gm_sor = 1 - sor.EUR_Cost.sum() / sor.EUR_Amount.sum()

print(out.to_string())
print(f"\nNetwork FY2026 billed EUR {p.total.sum():,.0f} | stock orders (SOR) EUR {p.SOR.sum():,.0f}")
print(f"Indicative gross margin Q1 FY2027: all {gm_all:.1%} | stock orders {gm_sor:.1%}")

scen = {
    "IDS >= 85% today (PORTUGAL, HUNGARY, MALTA)": ["PORTUGAL", "HUNGARY", "MALTA"],
    "Four largest (ITUK, IUK, UTI, UMI)": ["ITUK", "IUK", "UTI", "UMI"],
    "All distributors": list(out.index),
}
for name, dbs in scen.items():
    base = out.loc[out.index.intersection(dbs), "SOR_eur"].sum()
    print(f"{name}: SOR EUR {base:,.0f} -> 2.5% = EUR {base*0.025:,.0f} | 5% = EUR {base*0.05:,.0f}")
for d in (0.025, 0.05):
    print(f"Volume needed on discounted stock orders to keep margin euros flat at {d:.1%}: +{gm_sor/(gm_sor-d)-1:.1%}")
