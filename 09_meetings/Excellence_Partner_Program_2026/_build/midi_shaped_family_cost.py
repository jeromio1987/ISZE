"""FY2026 stock-order euros for the MIDI-shaped proposal.

Same billing cut as plan_b_numbers.py: FY2026, 19 distributors outside the CIS
markets, stock orders = order type SOR, credits and freight out.

Families are AIM level-3 nodes from aim_pn_classification_20260920.csv.
Oil filters are a labelled part of filters, not a separate programme.
Brake linings, clutch pressure plates and release parts, and mixed filter
assemblies are counted so they can be shown as left out. They are not in the 2%.

Run from the ISZE root:
  python 09_meetings/Excellence_Partner_Program_2026/_build/midi_shaped_family_cost.py
"""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
PACK = HERE.parent
ROOT = HERE.parents[2]
D = ROOT / "01_data" / "00_derived"

IN_SCOPE = {
    "Clutch disc": ["Clutch Disc"],
    "Clutch kit": ["Clutch Kit"],
    "Brake pad": ["Brake Pad", "Brake Pad Kit"],
    "Brake shoe": ["Brake Shoe"],
    "Oil filter": ["Oil Filter", "Oil Filter Element"],
    "Air filter": ["Air Cleaner Filter"],
    "Fuel filter": ["Fuel Filter", "Fuel Filter Element"],
}
LEFT_OUT = {
    "Brake lining": ["Brake Lining"],
    "Clutch pressure plate": ["Pressure Plate"],
    "Clutch release bearing": ["Release Bearing"],
    "Filter assembly, mixed": ["Filter Assembly"],
    "Filter element, mixed": ["Filter Element"],
}
FIRST_WAVE = ["IUK", "IRELAND", "UTI", "GREECE", "PORTUGAL", "GERMANY", "ITUK"]
LABEL = {
    "ITUK": "Isuzu Truck UK", "IUK": "Isuzu UK pickup", "UTI": "UTI", "UMI": "UMI",
    "GERMANY": "Germany", "BELGIUM": "Benelux", "PORTUGAL": "Portugal", "NORWAY": "Norway",
    "SWEDEN": "Sweden", "IRELAND": "Ireland", "GREECE": "Greece", "CYPRUS": "Cyprus",
    "HUNGARY": "Hungary", "FINLAND": "Finland", "MALTA": "Malta", "ROMANIA": "Romania",
    "DENMARK": "Denmark", "ICELAND": "Iceland", "PALESTINE": "Palestine",
}

df = pd.read_parquet(D / "sales_fact.parquet", columns=["billing_date", "sold_to_sap", "part_number", "description", "net_sales_value", "saty"])
dim = pd.read_csv(D / "distributor_dimension.csv")
dim = dim[(dim.network_role == "network_db") & (dim.region != "CIS")]
code = dict(zip(dim.sold_to_sap, dim.distributor_code))

fy = df[(df.billing_date >= "2025-04-01") & (df.billing_date <= "2026-03-31")].copy()
fy["db"] = fy.sold_to_sap.map(code)
fy = fy[fy.db.notna()]
desc = fy.description.fillna("").str.lower()
bill = fy[~desc.str.contains("rebate|freight|transport|demurrage|service fee|interest") & ~fy.saty.isin(["CR", "RE", "FD", "ZDR", "DR"])]
sor = bill[bill.saty == "SOR"].copy()
sor["pn"] = sor.part_number.astype(str).str.strip()

aim = pd.read_csv(
    D / "aim_pn_classification_20260920.csv",
    usecols=["part_number", "aim_l3_fixed"],
    dtype=str,
    low_memory=False,
)
aim["pn"] = aim.part_number.str.strip()
l3_to_family = {}
for family, nodes in {**IN_SCOPE, **LEFT_OUT}.items():
    for node in nodes:
        l3_to_family[node] = family
aim["family"] = aim.aim_l3_fixed.map(l3_to_family)
aim = aim[aim.family.notna()][["pn", "family"]].drop_duplicates("pn")

sor = sor.merge(aim, on="pn", how="left")
sor["in_programme"] = sor.family.isin(IN_SCOPE)

rows = []
for db, g in sor.groupby("db"):
    row = {
        "distributor_code": db,
        "label": LABEL.get(db, db),
        "first_wave": db in FIRST_WAVE,
        "stock_orders": round(float(g.net_sales_value.sum()), 2),
    }
    for family in list(IN_SCOPE) + list(LEFT_OUT):
        row[family] = round(float(g.loc[g.family == family, "net_sales_value"].sum()), 2)
    prog = g[g.in_programme]
    row["programme_stock"] = round(float(prog.net_sales_value.sum()), 2)
    row["programme_2pct"] = round(row["programme_stock"] * 0.02, 2)
    row["oil_filter"] = row["Oil filter"]
    rows.append(row)

t = pd.DataFrame(rows).sort_values("programme_stock", ascending=False)
t.to_csv(PACK / "midi_shaped_family_cost_fy2026.csv", index=False, float_format="%.2f")

def pack(frame):
    out = {"distributors": int(len(frame)), "stock_orders": round(float(frame.stock_orders.sum()), 2)}
    for family in list(IN_SCOPE) + list(LEFT_OUT):
        out[family] = round(float(frame[family].sum()), 2)
    out["programme_stock"] = round(float(frame.programme_stock.sum()), 2)
    out["programme_2pct"] = round(float(frame.programme_2pct.sum()), 2)
    out["filters"] = round(float(frame[["Oil filter", "Air filter", "Fuel filter"]].sum().sum()), 2)
    out["clutch"] = round(float(frame[["Clutch disc", "Clutch kit"]].sum().sum()), 2)
    return out

summary = {
    "window": "FY2026 2025-04-01 to 2026-03-31",
    "stock_definition": "saty SOR, after rebate freight and credit notes, same cut as plan_b_numbers.py",
    "classification": "aim_pn_classification_20260920.csv aim_l3_fixed",
    "in_scope_nodes": IN_SCOPE,
    "left_out_nodes": LEFT_OUT,
    "all_19": pack(t),
    "first_wave": pack(t[t.first_wave]),
    "sor_unclassified_eur": round(float(sor.loc[sor.family.isna(), "net_sales_value"].sum()), 2),
    "sor_total": round(float(sor.net_sales_value.sum()), 2),
}
(PACK / "midi_shaped_family_cost_fy2026.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
print(json.dumps(summary, indent=1))
print(t[["label", "first_wave", "programme_stock", "programme_2pct", "Oil filter", "Air filter", "Fuel filter", "Clutch disc", "Clutch kit", "Brake pad", "Brake shoe"]].to_string(index=False))
