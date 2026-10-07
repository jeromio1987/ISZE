"""Diagnose the join keys between Natalie's BO file, the ETD sheet, and the IML order-status delay file."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

BO = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_natalie_bo_wk41_20261007\2026-10-06_1147_Natalie_BO info VP 06-10-2026.xlsx")
DELAY = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\ISZE_Order Status as of 2 October 2026_request to check.xlsx")


def norm_pn(v) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", str(v or ""))


data = pd.read_excel(BO, sheet_name="DATA", header=3).dropna(how="all")
data.columns = [str(c).strip() for c in data.columns]
data = data[data["Material"].notna()].copy()
data["pn"] = data["Material"].map(norm_pn)
data["sales_doc"] = data["Sales Doc."].astype(str).str.strip()

etd = pd.read_excel(BO, sheet_name="ETD", header=0)
etd.columns = [str(c).strip() for c in etd.columns]
etd["pn"] = etd["PART NUMBER"].map(norm_pn)
etd["po_ref"] = etd["PO REF"].astype(str).str.strip()

dly = pd.read_excel(DELAY, sheet_name="isze")
dly.columns = [str(c).strip() for c in dly.columns]
dly["pn"] = dly["PN"].map(norm_pn)
dly["order_no"] = dly["Order No"].astype(str).str.strip()

print("BO sales_doc samples:", sorted(set(data["sales_doc"]))[:8], "| n distinct:", data["sales_doc"].nunique())
print("ETD PO REF samples :", sorted(set(etd["po_ref"]))[:8], "| n distinct:", etd["po_ref"].nunique())
print("DELAY Order No     :", sorted(set(dly["order_no"]))[:8], "| n distinct:", dly["order_no"].nunique())
print()
print("sales_doc set == order_no set?", set(data["sales_doc"]) == set(dly["order_no"]))
print("overlap sales_doc vs order_no:", len(set(data["sales_doc"]) & set(dly["order_no"])))
print("overlap ETD po_ref vs order_no:", len(set(etd["po_ref"]) & set(dly["order_no"])))
print("overlap ETD po_ref vs sales_doc:", len(set(etd["po_ref"]) & set(data["sales_doc"])))
print()
print("PN overlap BO vs DELAY:", len(set(data["pn"]) & set(dly["pn"])), "| BO pn:", data["pn"].nunique(), "| DELAY pn:", dly["pn"].nunique())
print("PN overlap BO vs ETD  :", len(set(data["pn"]) & set(etd["pn"])), "| ETD pn:", etd["pn"].nunique())
print()
print("BO sample PN:", data["pn"].head(5).tolist())
print("ETD sample PN:", etd["pn"].head(5).tolist())
print("DELAY sample PN:", dly["pn"].head(5).tolist())
print()
print("ETD ETA sample:", etd["ETA"].head(4).tolist())
print("ETD columns:", list(etd.columns))
print("DELAY status x exp alloc blank:", dly.groupby("Status")["Expected Allocation date"].apply(lambda s: s.isna().sum()).to_dict())
print()
key_etd = set(etd["po_ref"] + "|" + etd["pn"])
key_dly = set(dly["order_no"] + "|" + dly["pn"])
print("po_ref|pn overlap ETD vs DELAY:", len(key_etd & key_dly), "of ETD", len(key_etd))
