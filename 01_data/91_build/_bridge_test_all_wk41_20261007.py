"""Bridge test across every WK41 per-distributor BO overview: any column that joins to IML's Order No?"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
MAIL = ROOT / "01_data" / "90_INBOX" / "_iml_delay_wk41_20261007" / "bo_overview"
DELAY = ROOT / "01_data" / "ISZE_Order Status as of 2 October 2026_request to check.xlsx"


def digits(v) -> str:
    return re.sub(r"[^0-9]", "", str(v if v is not None else ""))


def norm(v) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", str(v if v is not None else ""))


dly = pd.read_excel(DELAY, sheet_name="isze", dtype=str)
dly.columns = [str(c).strip() for c in dly.columns]
iml_orders = {d for d in dly["Order No"].fillna("").map(digits) if d}
iml_pn = {p for p in dly["PN"].fillna("").map(norm) if p}
print(f"IML Order No: {len(iml_orders)} | part numbers: {len(iml_pn)}\n")

files = sorted(MAIL.glob("20261006_BO OVERVIEW - *.xlsx"))
print(f"WK41 per-distributor files: {len(files)}\n")

cols_wanted = ["Sold-to n°", "Customer", "Sales Doc.", "Customer Reference", "Material"]
summary = []
detail = {}

for f in files:
    try:
        df = pd.read_excel(f, sheet_name="DATA", header=3, dtype=str)
    except Exception as exc:
        print(f"FAIL {f.name}: {exc}")
        continue
    df.columns = [str(c).strip() for c in df.columns]
    df = df[df.get("Material").notna()] if "Material" in df.columns else df
    name = f.stem.replace("20261006_BO OVERVIEW - ", "")
    row = {"file": name, "lines": len(df)}

    if "Sales Doc." in df.columns:
        sd = {d for d in df["Sales Doc."].map(digits) if d}
        row["sales_doc_n"] = len(sd)
        row["sales_doc_hits"] = len(sd & iml_orders)

    if "Customer Reference" in df.columns:
        cr = {norm(v) for v in df["Customer Reference"].fillna("")}
        cr.discard("")
        row["cust_ref_n"] = len(cr)
        row["cust_ref_hits"] = len(cr & iml_orders)
        detail[name] = {"sales_doc": sorted(sd)[:3] if "Sales Doc." in df.columns else [],
                        "cust_ref": sorted(cr)[:3]}

    if "Material" in df.columns:
        pn = {norm(v) for v in df["Material"].fillna("")}
        pn.discard("")
        row["pn_n"] = len(pn)
        row["pn_hits"] = len(pn & iml_pn)

    summary.append(row)

s = pd.DataFrame(summary)
pd.set_option("display.width", 220)
print("=== per file: do its references match IML's Order No? ===")
print(s.to_string(index=False))
print()
print("=== totals ===")
for c in ["lines", "sales_doc_n", "sales_doc_hits", "cust_ref_n", "cust_ref_hits", "pn_n", "pn_hits"]:
    if c in s.columns:
        print(f"  {c:16s} {s[c].sum():,.0f}")

print("\n=== sample references, to eyeball the number ranges ===")
for k, v in list(detail.items())[:8]:
    print(f"  {k[:46]:48s} sales_doc {v['sales_doc']}  cust_ref {v['cust_ref']}")
print(f"\nIML Order No sample: {sorted(iml_orders)[:6]}")
