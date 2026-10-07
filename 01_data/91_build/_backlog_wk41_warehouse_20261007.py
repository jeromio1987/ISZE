"""IML warehouse picture (delay file) + customer backlog, both with AIM families.

Jerome 2026-10-07: which customers / parts / AIM families are stuck in the IML warehouse process,
and how long they have been waiting.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

DELAY = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\ISZE_Order Status as of 2 October 2026_request to check.xlsx")
BO = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_natalie_bo_wk41_20261007\2026-10-06_1147_Natalie_BO info VP 06-10-2026.xlsx")
AIM = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_master_v2.csv")
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_natalie_bo_wk41_20261007")

EXCLUDE_DBS = ("MIDI", "RUS", "KAZ", "CBC-TRANS", "GRAND AVTO", "KOMTRANS", "KIMA")


def norm_pn(v) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", str(v or ""))


def d2(x) -> pd.Timestamp:
    return pd.to_datetime(x, format="%y%m%d", errors="coerce")


aim = pd.read_csv(AIM, low_memory=False)
aim["pn"] = aim["part_number"].map(norm_pn)
aim_slim = (aim[["pn", "description", "aim_l1", "aim_l2", "fig_key"]]
            .dropna(subset=["pn"]).drop_duplicates("pn"))

asof = pd.Timestamp("2026-10-02")

# ================= IML warehouse (delay file) =================
dly = pd.read_excel(DELAY, sheet_name="isze")
dly.columns = [str(c).strip() for c in dly.columns]
dly["pn"] = dly["PN"].map(norm_pn)
dly["desc"] = dly["Part Name"].astype(str).str.strip()
dly["status"] = dly["Status"].astype(str).str.strip()
dly["qty"] = pd.to_numeric(dly["Q'ty"], errors="coerce").fillna(0)
dly["mode"] = dly["Mode"].astype(str).str.strip()
for col, out in [("Procced", "procced"), ("Allocated", "allocated"), ("Picked", "picked"),
                 ("Packed", "packed"), ("Invoice", "invoice"), ("Shipped", "shipped"),
                 ("ETD", "etd")]:
    dly[out] = d2(dly[col])
dly["order_no"] = dly["Order No"].astype(str).str.strip()
dly["age_days"] = (asof - dly["procced"]).dt.days
dly = dly.merge(aim_slim, on="pn", how="left")

print("=== IML file: date fill rates ===")
for c in ["procced", "allocated", "picked", "packed", "invoice", "shipped", "etd"]:
    print(f"  {c:10s} filled {dly[c].notna().sum():5d} / {len(dly)}")
print("  procced range:", dly["procced"].min(), "->", dly["procced"].max())

print("\n=== waiting age by status (days since the order was processed) ===")
g = dly.groupby("status").agg(lines=("qty", "size"), pcs=("qty", "sum"),
                              oldest=("age_days", "max"), median=("age_days", "median"),
                              over_30=("age_days", lambda s: (s > 30).sum()),
                              over_60=("age_days", lambda s: (s > 60).sum()),
                              over_90=("age_days", lambda s: (s > 90).sum()))
print(g.to_string(float_format=lambda x: f"{x:,.0f}"))

print("\n=== pcs sitting over 30 days, by status ===")
old = dly[dly["age_days"] > 30]
print(old.groupby("status").agg(lines=("qty", "size"), pcs=("qty", "sum"),
                                oldest=("age_days", "max")).to_string(float_format=lambda x: f"{x:,.0f}"))

print("\n=== age bucket x status (lines) ===")
dly["bucket"] = pd.cut(dly["age_days"], [-1, 7, 30, 60, 90, 180, 100_000],
                       labels=["0-7 d", "8-30 d", "31-60 d", "61-90 d", "91-180 d", ">180 d"])
print(pd.crosstab(dly["bucket"], dly["status"], margins=True).to_string())

print("\n=== Air vs Sea ===")
print(dly.groupby("mode").agg(lines=("qty", "size"), pcs=("qty", "sum"),
                              oldest=("age_days", "max")).to_string(float_format=lambda x: f"{x:,.0f}"))

print("\n=== IML warehouse: TOP 25 parts by pieces still open ===")
top = (dly.groupby(["pn", "desc", "aim_l1"], as_index=False, dropna=False)
         .agg(lines=("qty", "size"), pcs=("qty", "sum"), oldest=("age_days", "max"),
              statuses=("status", lambda s: "/".join(sorted(set(s)))))
         .sort_values("pcs", ascending=False).head(25))
print(top.to_string(index=False))

print("\n=== IML warehouse: pieces by AIM level 1 ===")
a = (dly.groupby("aim_l1", as_index=False, dropna=False)
       .agg(lines=("qty", "size"), pcs=("qty", "sum"), oldest=("age_days", "max"))
       .sort_values("pcs", ascending=False))
print(a.to_string(index=False, float_format=lambda x: f"{x:,.0f}"))

print("\n=== parts with the highest line counts (repeated chasing) ===")
rep = (dly.groupby(["pn", "desc"], as_index=False)
         .agg(lines=("qty", "size"), pcs=("qty", "sum"), orders=("order_no", "nunique"),
              oldest=("age_days", "max"))
         .sort_values("lines", ascending=False).head(15))
print(rep.to_string(index=False, float_format=lambda x: f"{x:,.0f}"))

# ================= Natalie backlog, AIM + ageing =================
data = pd.read_excel(BO, sheet_name="DATA", header=3).dropna(how="all")
data.columns = [str(c).strip() for c in data.columns]
data = data[data["Material"].notna()].copy()
data["pn"] = data["Material"].map(norm_pn)
data["customer"] = data["Customer"].astype(str).str.strip()
data["saty"] = data["SaTy"].astype(str).str.strip()
data["qty"] = pd.to_numeric(data["Open Qty"], errors="coerce").fillna(0)
data["req_dlv"] = pd.to_datetime(data["Req.Dlv.Dt"], errors="coerce")
data["age_days"] = (pd.Timestamp("2026-10-06") - data["req_dlv"]).dt.days
data["loc"] = data["Shipping Location"].astype(str).str.strip()
data = data.merge(aim_slim, on="pn", how="left")
data["is_midi"] = data["customer"].str.upper().str.contains("MIDI")
keep = ~data["customer"].str.upper().str.contains("|".join(EXCLUDE_DBS))
data["in_scope"] = keep & ~data["is_midi"]

print("\n\n=== CUSTOMER BACKLOG: full vs in-scope ===")
print(f"all lines {len(data)} | in scope {int(data['in_scope'].sum())} | removed {len(data) - int(data['in_scope'].sum())}")
scope = data[data["in_scope"]].copy()
print("in-scope customers:", scope["customer"].nunique(), "| pcs:", f"{scope['qty'].sum():,.0f}")

print("\n=== IN-SCOPE by customer (lines / pcs / urgent / oldest) ===")
cu = (scope.groupby("customer", as_index=False)
        .agg(lines=("pn", "size"), pns=("pn", "nunique"), pcs=("qty", "sum"),
             vor_rush=("saty", lambda s: s.isin(["VOR", "RUSH", "SVOR"]).sum()),
             oldest_days=("age_days", "max"), over_90=("age_days", lambda s: (s > 90).sum()))
        .sort_values("pcs", ascending=False))
cu["pct_urgent"] = (100 * cu["vor_rush"] / cu["lines"]).round(0)
print(cu.to_string(index=False, float_format=lambda x: f"{x:,.0f}"))

print("\n=== IN-SCOPE by AIM level 1 ===")
print(scope.groupby("aim_l1", dropna=False).agg(lines=("pn", "size"), pcs=("qty", "sum"),
      custs=("customer", "nunique")).sort_values("pcs", ascending=False).to_string(float_format=lambda x: f"{x:,.0f}"))

print("\n=== IN-SCOPE top 20 parts ===")
tp = (scope.groupby(["pn", "description"], as_index=False, dropna=False)
        .agg(lines=("pn", "size"), pcs=("qty", "sum"), custs=("customer", "nunique"),
             aim=("aim_l1", "first"), oldest=("age_days", "max"),
             satys=("saty", lambda s: "/".join(sorted(set(s)))))
        .sort_values("pcs", ascending=False).head(20))
print(tp.to_string(index=False, float_format=lambda x: f"{x:,.0f}"))

# ---- overlap: parts that are both on customer back order AND in the IML warehouse ----
bo_pns = set(scope["pn"])
iml_pns = set(dly["pn"])
both = bo_pns & iml_pns
print("\n=== OVERLAP ===")
print("parts on customer back order:", len(bo_pns))
print("parts open in the IML warehouse:", len(iml_pns))
print("in both:", len(both))
print("in-scope backlog pieces on those common parts:", f"{scope[scope['pn'].isin(both)]['qty'].sum():,.0f}",
      "of", f"{scope['qty'].sum():,.0f}")

dly.to_csv(OUT / "iml_warehouse_enriched.csv", index=False)
scope.to_csv(OUT / "backlog_wk41_in_scope.csv", index=False)
cu.to_csv(OUT / "backlog_wk41_customers_in_scope.csv", index=False)
print("\nwrote csvs")
