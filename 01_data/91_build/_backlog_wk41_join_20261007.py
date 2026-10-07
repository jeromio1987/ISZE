"""Backlog WK41 analysis - join Natalie's BO overview to the IML order-status (delay) file and price it.

Read-only analysis. No output shipped. Writes interim CSVs to the inbox folder.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

BO = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_natalie_bo_wk41_20261007\2026-10-06_1147_Natalie_BO info VP 06-10-2026.xlsx")
DELAY = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\ISZE_Order Status as of 2 October 2026_request to check.xlsx")
FACT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\sales_fact.parquet")
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_natalie_bo_wk41_20261007")
OUT.mkdir(parents=True, exist_ok=True)


def norm_pn(v) -> str:
    s = re.sub(r"[^0-9A-Za-z]", "", str(v or ""))
    return s


def main() -> int:
    # ---------- Natalie DATA sheet ----------
    data = pd.read_excel(BO, sheet_name="DATA", header=3)
    data = data.dropna(how="all")
    data.columns = [str(c).strip() for c in data.columns]
    print("DATA cols:", list(data.columns))
    rename = {
        "Sold-to n°": "sold_to_sap", "Sold-to n": "sold_to_sap", "Sold-to no": "sold_to_sap",
        "Customer": "customer", "Sales Doc.": "sales_doc", "Customer Reference": "cust_ref",
        "Material": "material", "Material description": "description", "SaTy": "saty",
        "Req.Dlv.Dt": "req_dlv", "Open Qty": "open_qty", "Transit qty": "transit_qty",
        "ETA": "eta", "Priority": "priority", "Next ETA Supplier": "next_eta_supplier",
        "Tentative future ETA I": "tentative_eta", "Confirmed Qty": "confirmed_qty",
        "MoT": "mot", "Remark": "remark", "Shipping Location": "ship_loc",
    }
    data = data.rename(columns={k: v for k, v in rename.items() if k in data.columns})
    data = data[data["material"].notna()].copy()
    data["pn"] = data["material"].map(norm_pn)
    data["open_qty"] = pd.to_numeric(data["open_qty"], errors="coerce")
    data["transit_qty"] = pd.to_numeric(data["transit_qty"], errors="coerce")
    data["req_dlv"] = pd.to_datetime(data["req_dlv"], errors="coerce")
    data["sold_to_sap"] = pd.to_numeric(data["sold_to_sap"], errors="coerce")
    data["customer"] = data["customer"].astype(str).str.strip()
    print("DATA usable rows:", len(data), "| open qty:", data["open_qty"].sum())

    # ---------- ETD sheet (IML supply view) ----------
    etd = pd.read_excel(BO, sheet_name="ETD", header=0)
    etd.columns = [str(c).strip() for c in etd.columns]
    etd["po_ref"] = etd["PO REF"].astype(str).str.strip().map(lambda s: re.sub(r"\.0$", "", s))
    etd["pn"] = etd["PART NUMBER"].map(norm_pn)
    etd["key"] = etd["po_ref"] + "|" + etd["pn"]
    print("ETD rows:", len(etd), "| unique keys:", etd["key"].nunique())

    # ---------- IML order status (the delay file) ----------
    dly = pd.read_excel(DELAY, sheet_name="isze")
    dly.columns = [str(c).strip() for c in dly.columns]
    dly["po_ref"] = dly["Order No"].astype(str).str.strip()
    dly["pn"] = dly["PN"].map(norm_pn)
    dly["key"] = dly["po_ref"] + "|" + dly["pn"]
    dly["qty"] = pd.to_numeric(dly["Q'ty"], errors="coerce")
    dly["status"] = dly["Status"].astype(str).str.strip()
    dly["proceed"] = pd.to_datetime(dly["Procced"], format="%y%m%d", errors="coerce")
    dly["exp_alloc"] = pd.to_datetime(dly["Expected Allocation date"], format="%y%m%d", errors="coerce")
    print("DELAY rows:", len(dly), "| unique keys:", dly["key"].nunique())
    print("DELAY status:", dly["status"].value_counts().to_dict())

    # ---------- join ETD key -> delay status ----------
    dly_first = (dly.sort_values("key")
                    .groupby("key", as_index=False)
                    .agg(delay_status=("status", lambda s: ";".join(sorted(set(s)))),
                         delay_qty=("qty", "sum"),
                         exp_alloc=("exp_alloc", "min")))
    etd_j = etd.merge(dly_first, on="key", how="left")
    print("ETD matched to a delay line:", etd_j["delay_status"].notna().sum(), "of", len(etd_j))

    # ---------- price from sales_fact ----------
    fact = pd.read_parquet(FACT)
    fact = fact[fact["net_sales_value"].notna() & (fact["billed_qty"] > 0)].copy()
    fact["pn"] = fact["part_number"].map(norm_pn)
    fact["sold_to_sap"] = pd.to_numeric(fact["sold_to_sap"], errors="coerce")
    fact["unit_eur"] = fact["net_sales_value"] / fact["billed_qty"]
    recent = fact[fact["billing_date"] >= "2024-10-01"]

    cust_price = (recent.groupby(["sold_to_sap", "pn"], as_index=False)
                        .agg(unit_cust=("unit_eur", "mean")))
    net_price = (recent.groupby("pn", as_index=False)
                       .agg(unit_net=("unit_eur", "mean")))
    print("price rows (customer x pn):", len(cust_price), "| (pn):", len(net_price))

    data = data.merge(cust_price, on=["sold_to_sap", "pn"], how="left")
    data = data.merge(net_price, on="pn", how="left")
    data["unit_eur"] = data["unit_cust"].fillna(data["unit_net"])
    data["price_basis"] = ["customer" if pd.notna(a) else ("network" if pd.notna(b) else "no price")
                           for a, b in zip(data["unit_cust"], data["unit_net"])]
    data["open_value_eur"] = data["open_qty"] * data["unit_eur"]
    priced = data["open_value_eur"].notna()
    print(f"priced lines {priced.sum()} / {len(data)}  ({100*priced.mean():.1f}%)")
    print(f"open value EUR {data['open_value_eur'].sum():,.0f} | unpriced open qty {data.loc[~priced,'open_qty'].sum():,.0f}")

    # ---------- attach supply status ----------
    data["key"] = ""
    # sales doc is the PO reference in the customer-facing BO
    data["key"] = (data["sales_doc"].astype(str).str.strip()
                   .map(lambda s: re.sub(r"\.0$", "", s)) + "|" + data["pn"])
    etd_slim = etd_j[["key", "MoT", "PRIORITY", "ETA", "ETD", "ETA ISZE",
                      "TTL BO QTY ISZE", "delay_status", "exp_alloc"]].drop_duplicates("key")
    merged = data.merge(etd_slim, on="key", how="left", suffixes=("", "_etd"))
    print("BO lines with an IML supply row:", merged["MoT"].notna().sum(), "/", len(merged))
    merged["etd_missing"] = merged["ETD"].isna() | (merged["ETD"].astype(str).str.strip() == "")
    merged["eta_tbc"] = merged["ETA"].astype(str).str.contains("TBC", case=False, na=False)

    # ---------- customer roll-up ----------
    g = (merged.groupby("customer", as_index=False)
         .agg(lines=("pn", "size"),
              pns=("pn", "nunique"),
              open_qty=("open_qty", "sum"),
              transit_qty=("transit_qty", "sum"),
              open_value_eur=("open_value_eur", "sum"),
              priced_lines=("open_value_eur", lambda s: s.notna().sum()),
              vor_rush=("saty", lambda s: s.isin(["VOR", "RUSH", "SVOR"]).sum()),
              no_etd=("etd_missing", "sum"),
              eta_tbc=("eta_tbc", "sum"),
              oldest_req=("req_dlv", "min"),
              newest_req=("req_dlv", "max")))
    g["pct_vor_rush"] = 100 * g["vor_rush"] / g["lines"]
    g["pct_no_etd"] = 100 * g["no_etd"] / g["lines"]
    g = g.sort_values("open_value_eur", ascending=False)
    pd.set_option("display.width", 250)
    print("\n=== BY CUSTOMER (EUR) ===")
    print(g.to_string(index=False, float_format=lambda x: f"{x:,.0f}"))

    g.to_csv(OUT / "backlog_wk41_by_customer.csv", index=False)
    merged.to_csv(OUT / "backlog_wk41_lines.csv", index=False)
    etd_j.to_csv(OUT / "iml_etd_status.csv", index=False)

    print("\n=== OVERALL ===")
    print("customers:", g["customer"].nunique())
    print("total open value EUR:", f"{g['open_value_eur'].sum():,.0f}")
    print("VOR+RUSH lines:", int(g["vor_rush"].sum()), "of", int(g["lines"].sum()))
    print("lines with no ETD:", int(g["no_etd"].sum()))
    print("lines with ETA 'TBC':", int(g["eta_tbc"].sum()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
