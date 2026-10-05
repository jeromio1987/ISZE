# -*- coding: utf-8 -*-
r"""Read-only probe 4: the horizon total and rebate lines, measured inside the derived billing file."""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ISZE = os.path.dirname(ROOT)
D = os.path.join(ISZE, "01_data", "00_derived")

df = pd.read_parquet(os.path.join(D, "sales_fact.parquet"))
dim = pd.read_csv(os.path.join(D, "distributor_dimension.csv"), encoding="utf-8-sig")

print("rows %d   period %s .. %s" % (
    len(df), df["billing_date"].min(), df["billing_date"].max()))
print("net_sales_value total: %.2f" % df["net_sales_value"].sum())
print("distinct sold_to_sap: %d" % df["sold_to_sap"].nunique())

print()
print("network_role values:", dim["network_role"].value_counts().to_dict())
print("scope values:", dim["scope"].value_counts().to_dict())

net = set(dim.loc[dim["network_role"].astype(str).str.lower().str.contains("network"),
                  "sold_to_sap"])
print("network entity keys: %d" % len(net))
sub = df[df["sold_to_sap"].isin(net)]
print("rows on network entities: %d   net value: %.2f" % (len(sub), sub["net_sales_value"].sum()))

print()
reb = df[df["part_number"].astype(str).str.fullmatch("REBATE", case=False, na=False)]
print("REBATE lines: %d  value %.2f  period %s .. %s" % (
    len(reb), reb["net_sales_value"].sum(),
    reb["billing_date"].min(), reb["billing_date"].max()))
print("REBATE by sold_to:")
print(reb.groupby("sold_to")["net_sales_value"].agg(["count", "sum"]).to_string())

print()
print("FY2026 (2025-04-01..2026-03-31) net value: %.2f across %d entities" % (
    df[(df["billing_date"] >= "2025-04-01") & (df["billing_date"] <= "2026-03-31")]["net_sales_value"].sum(),
    df[(df["billing_date"] >= "2025-04-01") & (df["billing_date"] <= "2026-03-31")]["sold_to_sap"].nunique()))
print("calendar 2025 net value: %.2f" % (
    df[(df["billing_date"] >= "2025-01-01") & (df["billing_date"] <= "2025-12-31")]["net_sales_value"].sum()))
