"""Numbers behind the Plan B white paper. Reads parquet and derived files only (never raw billing extracts).

Outputs (next to the paper):
  planb_basis_fy2026.csv   one row per distributor in scope
  planb_numbers.json       the figures the paper quotes; build_plan_b_paper.py asserts against it

Basis, as in the first white paper: FY2026 = 1 Apr 2025 to 31 Mar 2026; 19 distributors outside the CIS markets;
billed = net sales value without credit notes, freight, transport, service fees and rebate lines;
stock orders = order type SOR. Rebate credits = lines described "Rebate Material".

Run from the ISZE root:  python 09_meetings/Excellence_Partner_Program_2026/_build/plan_b_numbers.py
"""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
PACK = HERE.parent
ROOT = HERE.parents[2]
D = ROOT / "01_data" / "00_derived"

df = pd.read_parquet(D / "sales_fact.parquet")
dim = pd.read_csv(D / "distributor_dimension.csv")
dim = dim[(dim.network_role == "network_db") & (dim.region != "CIS")]
m = dict(zip(dim.sold_to_sap, dim.distributor_code))

fy = df[(df.billing_date >= "2025-04-01") & (df.billing_date <= "2026-03-31")].copy()
fy["db"] = fy.sold_to_sap.map(m)
fy = fy[fy.db.notna()]
desc = fy.description.fillna("").str.lower()
rebate = fy[desc.str.contains("rebate")].groupby("db").net_sales_value.sum()
bill = fy[~desc.str.contains("rebate|freight|transport|demurrage|service fee|interest") & ~fy.saty.isin(["CR", "RE", "FD", "ZDR", "DR"])]
billed = bill.groupby("db").net_sales_value.sum()
sor = bill[bill.saty == "SOR"].groupby("db").net_sales_value.sum()

KICKBACK = ["IUK", "IRELAND", "UTI", "PORTUGAL", "GERMANY", "BELGIUM", "SWEDEN", "NORWAY", "UMI"]  # nine, per the first white paper
LABEL = {"ITUK": "Isuzu Truck UK", "IUK": "Isuzu UK pickup", "UTI": "UTI", "UMI": "UMI", "GERMANY": "Germany", "BELGIUM": "Benelux",
         "PORTUGAL": "Portugal", "NORWAY": "Norway", "SWEDEN": "Sweden", "IRELAND": "Ireland", "GREECE": "Greece", "CYPRUS": "Cyprus",
         "HUNGARY": "Hungary", "FINLAND": "Finland", "MALTA": "Malta", "ROMANIA": "Romania", "DENMARK": "Denmark", "ICELAND": "Iceland",
         "PALESTINE": "Palestine"}

std = pd.read_csv(D / "billed_vs_std_warranty_fy2026.csv").set_index("distributor_code")
t = pd.concat([billed.rename("billed"), sor.rename("stock_orders"), rebate.rename("rebate_credit")], axis=1).fillna(0).sort_values("billed", ascending=False)
t["label"] = [LABEL[i] for i in t.index]
t["kickback"] = [i in KICKBACK for i in t.index]
t["std_months_fy2026"] = [int(std.month_count[i]) if i in std.index else 0 for i in t.index]
t["share_billed"] = t.billed / t.billed.sum()
t.to_csv(PACK / "planb_basis_fy2026.csv", index_label="distributor_code", float_format="%.2f")

kb = t[t.kickback]
nk = t[~t.kickback]
kb_with_credit = kb[kb.rebate_credit > 0]
has_file = t[t.std_months_fy2026 > 0]
nokick_no_file = kb[kb.std_months_fy2026 == 0]

out = {
    "billed_total": round(t.billed.sum()),
    "stock_total": round(t.stock_orders.sum()),
    "stock_share": round(t.stock_orders.sum() / t.billed.sum(), 4),
    "rebate_total": round(t.rebate_credit.sum()),
    "kickback_n": len(kb),
    "kickback_billed": round(kb.billed.sum()),
    "kickback_share_billed": round(kb.billed.sum() / t.billed.sum(), 4),
    "kickback_share_stock": round(kb.stock_orders.sum() / t.stock_orders.sum(), 4),
    "others_n": len(nk),
    "others_billed": round(nk.billed.sum()),
    "others_share_billed": round(nk.billed.sum() / t.billed.sum(), 4),
    "kickback_rebate_credit": round(kb.rebate_credit.sum()),
    "kickback_with_credit_n": len(kb_with_credit),
    "kickback_20pct": round(kb.rebate_credit.sum() * 0.20),
    "all_credit_20pct": round(t.rebate_credit.sum() * 0.20),
    "ituk_billed": round(t.loc["ITUK", "billed"]),
    "ituk_share": round(t.loc["ITUK", "billed"] / t.billed.sum(), 4),
    "ituk_credit": round(t.loc["ITUK", "rebate_credit"]),
    "ireland_credit": round(t.loc["IRELAND", "rebate_credit"]),
    "with_file_n": len(has_file),
    "with_file_billed": round(has_file.billed.sum()),
    "with_file_share": round(has_file.billed.sum() / t.billed.sum(), 4),
    "kickback_without_file_n": len(nokick_no_file),
    "kickback_without_file_billed": round(nokick_no_file.billed.sum()),
    "kickback_without_file_names": [LABEL[i] for i in nokick_no_file.index],
    "per_distributor": {LABEL[i]: {"billed": round(r.billed), "stock": round(r.stock_orders), "credit": round(r.rebate_credit),
                                    "kickback": bool(r.kickback), "months": int(r.std_months_fy2026)} for i, r in t.iterrows()},
}
(PACK / "planb_numbers.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps({k: v for k, v in out.items() if k != "per_distributor"}, indent=1, ensure_ascii=False))
print(t[["label", "billed", "stock_orders", "rebate_credit", "kickback", "std_months_fy2026"]].round(0).to_string())
