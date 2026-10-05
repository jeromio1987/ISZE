# -*- coding: utf-8 -*-
r"""Read-only probe 11: pin the FY2026 network billing basis exactly."""
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
reb = df["part_number"].astype(str).str.fullmatch("REBATE", case=False, na=False)

fy = (df["billing_date"] >= "2025-04-01") & (df["billing_date"] <= "2026-03-31")
print("FY2026 rebate lines: %d  value %.2f" % ((fy & reb).sum(), df.loc[fy & reb, "net_sales_value"].sum()))

net = set(dim.loc[dim["network_role"].eq("network_db"), "sold_to_sap"])
print("network_db keys: %d" % len(net))
print("FY2026, network_db, all lines:        %.2f  (%d entities)" % (
    df.loc[fy & df["sold_to_sap"].isin(net), "net_sales_value"].sum(),
    df.loc[fy & df["sold_to_sap"].isin(net), "sold_to_sap"].nunique()))
print("FY2026, network_db, rebates removed:  %.2f  (%d entities)" % (
    df.loc[fy & df["sold_to_sap"].isin(net) & ~reb, "net_sales_value"].sum(),
    df.loc[fy & df["sold_to_sap"].isin(net) & ~reb, "sold_to_sap"].nunique()))
print("FY2026, all entities, rebates removed:%.2f  (%d entities)" % (
    df.loc[fy & ~reb, "net_sales_value"].sum(), df.loc[fy & ~reb, "sold_to_sap"].nunique()))

# 22 distributor *codes* is a different count from 25 sold-to keys
print()
print("distributor codes in dimension: %d, distinct gps_db_label: %d" % (
    dim["distributor_code"].nunique(), dim["gps_db_label"].nunique()))
d22 = dim[dim["network_role"].eq("network_db")]
print("network_db rows: %d, distinct codes %d" % (len(d22), d22["distributor_code"].nunique()))
k25 = set(d22["sold_to_sap"])
sub = df.loc[fy & df["sold_to_sap"].isin(k25) & ~reb]
print("FY2026 network_db less rebates: %.2f" % sub["net_sales_value"].sum())
codeof = dict(zip(d22["sold_to_sap"], d22["distributor_code"]))
sub = sub.assign(code=sub["sold_to_sap"].map(codeof))
print("   -> merged to %d distributor codes" % sub["code"].nunique())
print("   share of 570000 = %.4f%%   480000 = %.4f%%   90000 = %.4f%%   100000 = %.4f%%" % (
    100 * 570000 / sub["net_sales_value"].sum(),
    100 * 480000 / sub["net_sales_value"].sum(),
    100 * 90000 / sub["net_sales_value"].sum(),
    100 * 100000 / sub["net_sales_value"].sum()))
