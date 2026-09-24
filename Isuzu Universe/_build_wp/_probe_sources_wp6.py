# -*- coding: utf-8 -*-
r"""Read-only probe 6: try to reproduce the horizon total and the ITUK capture aggregate."""
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
dim["sold_to_sap"] = dim["sold_to_sap"].astype(float)

keyed = set(dim["sold_to_sap"])
print("sold_to_sap in parquet: %d, in dimension: %d, in both: %d" % (
    df["sold_to_sap"].nunique(), len(keyed), len(set(df["sold_to_sap"]) & keyed)))
print("parquet-only keys:", sorted(set(df["sold_to_sap"]) - keyed))
for role in ("network_db",):
    ks = set(dim.loc[dim["network_role"].eq(role), "sold_to_sap"])
    sub = df[df["sold_to_sap"].isin(ks)]
    print("  %-14s %d entities  horizon %.2f" % (role, len(ks), sub["net_sales_value"].sum()))
allkeyed = df[df["sold_to_sap"].isin(keyed)]
print("  keyed only (dimension entities)  horizon %.2f across %d" % (
    allkeyed["net_sales_value"].sum(), allkeyed["sold_to_sap"].nunique()))
noreb = allkeyed[~allkeyed["part_number"].astype(str).str.fullmatch("REBATE", case=False, na=False)]
print("  keyed, REBATE removed            horizon %.2f" % noreb["net_sales_value"].sum())
net = set(dim.loc[dim["network_role"].eq("network_db"), "sold_to_sap"])
noreb_net = df[df["sold_to_sap"].isin(net)]
noreb_net = noreb_net[~noreb_net["part_number"].astype(str).str.fullmatch(
    "REBATE", case=False, na=False)]
print("  network_db, REBATE removed       horizon %.2f" % noreb_net["net_sales_value"].sum())

# top-30 entities by value
byent = df.groupby("sold_to_sap")["net_sales_value"].sum().sort_values(ascending=False)
print("\ntop 32 entities, horizon value:")
print(byent.head(32).to_string())
print("top 30 total: %.2f" % byent.head(30).sum())

print("\nITUK 2025, derived file: %.2f" % df[(df["sold_to_sap"] == 2575)
      & (df["billing_date"] >= "2025-01-01") & (df["billing_date"] <= "2025-12-31")
      ]["net_sales_value"].sum())
print("ITUK whole horizon: %.2f" % df[df["sold_to_sap"] == 2575]["net_sales_value"].sum())

# ITUK capture aggregate, weighted on units
cap = pd.read_csv(os.path.join(D, "pms_capture_by_db_year.csv"), encoding="utf-8-sig")
t = cap[(cap["distributor_code"] == "ITUK") & (cap["year"] == 2025)]
print("\nITUK 2025 capture rows: %d line types %s" % (len(t), sorted(t["line_type"].unique())))
print("  expected_qty sum %.1f  actual_qty sum %.1f  ratio %.4f" % (
    t["expected_qty"].sum(), t["actual_qty"].sum(), t["actual_qty"].sum() / t["expected_qty"].sum()))
print("  actual_rev sum %.2f  gap sum %.2f" % (t["actual_rev_eur"].sum(), t["revenue_gap_eur"].sum()))
g = t[t["line_type"] == "genuine"]
print("  genuine line: expected %.1f actual %.1f ratio %.4f  rev %.2f" % (
    g["expected_qty"].sum(), g["actual_qty"].sum(),
    g["actual_qty"].sum() / g["expected_qty"].sum(), g["actual_rev_eur"].sum()))
