"""Backlog WK41 - fuller read: ageing, SaTy, families, delay-file picture, supply visibility."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

BO = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_natalie_bo_wk41_20261007\2026-10-06_1147_Natalie_BO info VP 06-10-2026.xlsx")
DELAY = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\ISZE_Order Status as of 2 October 2026_request to check.xlsx")
FACT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\sales_fact.parquet")
OUT = BO.parent


def norm_pn(v) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", str(v or ""))


data = pd.read_excel(BO, sheet_name="DATA", header=3).dropna(how="all")
data.columns = [str(c).strip() for c in data.columns]
data = data[data["Material"].notna()].copy()
data["pn"] = data["Material"].map(norm_pn)
data["sold_to_sap"] = pd.to_numeric(data["Sold-to n°"], errors="coerce")
data["customer"] = data["Customer"].astype(str).str.strip()
data["saty"] = data["SaTy"].astype(str).str.strip()
data["open_qty"] = pd.to_numeric(data["Open Qty"], errors="coerce")
data["transit_qty"] = pd.to_numeric(data["Transit qty"], errors="coerce")
data["req_dlv"] = pd.to_datetime(data["Req.Dlv.Dt"], errors="coerce")
data["ship_loc"] = data["Shipping Location"].astype(str).str.strip()
data["desc"] = data["Material description"].astype(str).str.strip()

# price
fact = pd.read_parquet(FACT)
fact = fact[fact["net_sales_value"].notna() & (fact["billed_qty"] > 0)].copy()
fact["pn"] = fact["part_number"].map(norm_pn)
fact["sold_to_sap"] = pd.to_numeric(fact["sold_to_sap"], errors="coerce")
fact["unit_eur"] = fact["net_sales_value"] / fact["billed_qty"]
recent = fact[fact["billing_date"] >= "2024-10-01"]

cp = recent.groupby(["sold_to_sap", "pn"], as_index=False).agg(u=("unit_eur", "mean"))
np_ = recent.groupby("pn", as_index=False).agg(u2=("unit_eur", "mean"))
fk = (recent.sort_values("billing_date").groupby("pn", as_index=False).agg(fig=("fig_key", "last")))

d = data.merge(cp, on=["sold_to_sap", "pn"], how="left").merge(np_, on="pn", how="left")
d["unit_eur"] = d["u"].fillna(d["u2"])
d["open_eur"] = d["open_qty"] * d["unit_eur"]
d = d.merge(fk, on="pn", how="left")

asof = pd.Timestamp("2026-10-06")
d["age_days"] = (asof - d["req_dlv"]).dt.days
d["age_bucket"] = pd.cut(d["age_days"], [-10_000, 0, 90, 365, 3650, 100_000],
                         labels=["not yet due", "<=3 mth", "3-12 mth", "1-3 yr", ">3 yr"])

print("=== AGEING of open value (EUR) ===")
print(d.groupby("age_bucket", observed=True)["open_eur"].agg(["size", "sum"]).to_string(float_format=lambda x: f"{x:,.0f}"))
print("\n=== SaTy ===")
print(d.groupby("saty")["open_eur"].agg(["size", "sum"]).sort_values("sum", ascending=False).to_string(float_format=lambda x: f"{x:,.0f}"))
print("\n=== Shipping location ===")
print(d.groupby("ship_loc")["open_eur"].agg(["size", "sum"]).to_string(float_format=lambda x: f"{x:,.0f}"))

print("\n=== TOP 25 PARTS by open value ===")
top = (d.groupby(["pn", "desc"], as_index=False)
        .agg(lines=("pn", "size"), qty=("open_qty", "sum"), eur=("open_eur", "sum"),
             custs=("customer", "nunique"), oldest=("req_dlv", "min"))
        .sort_values("eur", ascending=False).head(25))
print(top.to_string(index=False, float_format=lambda x: f"{x:,.0f}"))

print("\n=== TOP 15 FAMILIES (fig_key) by open value ===")
fam = (d.groupby("fig", as_index=False)
        .agg(lines=("pn", "size"), qty=("open_qty", "sum"), eur=("open_eur", "sum"),
             custs=("customer", "nunique"), pns=("pn", "nunique"))
        .sort_values("eur", ascending=False).head(15))
print(fam.to_string(index=False, float_format=lambda x: f"{x:,.0f}"))

# ---- delay file picture ----
dly = pd.read_excel(DELAY, sheet_name="isze")
dly.columns = [str(c).strip() for c in dly.columns]
dly["qty"] = pd.to_numeric(dly["Q'ty"], errors="coerce")
dly["status"] = dly["Status"].astype(str).str.strip()
dly["exp_alloc"] = pd.to_datetime(dly["Expected Allocation date"], format="%y%m%d", errors="coerce")
dly["proceed"] = pd.to_datetime(dly["Procced"], format="%y%m%d", errors="coerce")
print("\n=== IML ORDER-STATUS (delay) file: status x pieces ===")
print(dly.groupby("status").agg(lines=("qty", "size"), pcs=("qty", "sum"),
                               earliest_exp=("exp_alloc", "min"),
                               latest_exp=("exp_alloc", "max")).to_string(float_format=lambda x: f"{x:,.0f}"))
print("\nback-order lines pcs:", f"{dly.loc[dly['status']=='BACK ORDER','qty'].sum():,.0f}")
print("order nos in delay file:", dly["Order No"].astype(str).str.strip().nunique())

# ---- supply visibility from ETD sheet ----
etd = pd.read_excel(BO, sheet_name="ETD", header=0)
etd.columns = [str(c).strip() for c in etd.columns]
etd["pn"] = etd["PART NUMBER"].map(norm_pn)
etd["tbc"] = etd["ETA"].astype(str).str.contains("TBC", case=False, na=False)
print("\n=== ETD sheet ===")
print("rows:", len(etd), "| PNs:", etd["pn"].nunique(), "| PO refs:", etd["PO REF"].astype(str).str.strip().nunique())
print("rows with ETA TBC (supplier estimate only):", int(etd["tbc"].sum()))
print("rows with a real ETD:", int(etd["ETD"].notna().sum()), "| real ETA ISZE:", int(etd["ETA ISZE"].notna().sum()))
print("MoT:", etd["MoT"].value_counts().to_dict())
bo_pns = set(d["pn"])
etd_pns = set(etd["pn"])
print("BO PNs covered by the IML supply sheet:", len(bo_pns & etd_pns), "of", len(bo_pns))
cov = d[d["pn"].isin(etd_pns)]
print("share of open EUR with an IML supply line:", f"{cov['open_eur'].sum():,.0f} / {d['open_eur'].sum():,.0f}")

d.to_csv(OUT / "backlog_wk41_enriched.csv", index=False)
print("\nwrote enriched csv")
