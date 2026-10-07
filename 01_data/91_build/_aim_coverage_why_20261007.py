"""Who are the parts with no AIM classification, and why do they look heavy on the page?"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\ISZE_Order Status as of 2 October 2026_request to check.xlsx")
B = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_natalie_bo_wk41_20261007\2026-10-06_1147_Natalie_BO info VP 06-10-2026.xlsx")
A = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_master_v2.csv")


def norm(v) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", str(v if v is not None else ""))


aim = pd.read_csv(A, dtype=str, low_memory=False)
aim["pn"] = aim["part_number"].fillna("").map(norm)
aim["pn_nz"] = aim["pn"].str.lstrip("0")
aimset = set(aim["pn"]) | set(aim["pn_nz"])          # match both forms
aim_has = {p: (str(l1) if pd.notna(l1) else "") for p, l1 in
           zip(aim["pn"], aim["aim_l1"])}
aim_has.update({p: v for p, v in zip(aim["pn_nz"], aim["aim_l1"]) if pd.notna(v)})

# ---------- warehouse ----------
dly = pd.read_excel(D, sheet_name="isze", dtype=str)
dly["pn"] = dly["PN"].map(norm)
dly["part"] = dly["Part Name"].fillna("").str.strip()
dly["qty"] = pd.to_numeric(dly["Q'ty"], errors="coerce").fillna(0)
dly["has_aim"] = dly["pn"].isin(aimset)

print("=== WAREHOUSE, counted by LINES ===")
print(dly.groupby("has_aim").agg(lines=("pn", "size"), pcs=("qty", "sum")).to_string(float_format=lambda x: f"{x:,.0f}"))
print()
print("=== WAREHOUSE, counted by DISTINCT PART ===")
u = dly.drop_duplicates("pn")
print(u.groupby("has_aim").agg(parts=("pn", "size")).to_string())
print()
print("lines per part: classified %.2f | unclassified %.2f"
      % (dly[dly.has_aim].groupby("pn").size().mean(), dly[~dly.has_aim].groupby("pn").size().mean()))

miss = dly[~dly.has_aim]
print("\n=== the unclassified warehouse parts with the most lines ===")
m = (miss.groupby(["pn", "part"], as_index=False)
      .agg(lines=("qty", "size"), pcs=("qty", "sum"))
      .sort_values("lines", ascending=False).head(20))
print(m.to_string(index=False, float_format=lambda x: f"{x:,.0f}"))

print("\n=== shape of the unclassified part numbers ===")
lens = miss.drop_duplicates("pn")["pn"].str.len().value_counts().sort_index()
print("length :", lens.to_dict())
print("start with a zero:", int(miss.drop_duplicates('pn')['pn'].str.startswith('0').sum()),
      "of", miss['pn'].nunique())
print("non numeric inside:", int(miss.drop_duplicates('pn')['pn'].str.contains('[^0-9]', regex=True).sum()))

print("\n=== do those part numbers exist anywhere in our billed history? ===")
try:
    fact = pd.read_parquet(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\sales_fact.parquet")
    fact["pn"] = fact["part_number"].map(norm)
    billed = set(fact["pn"]) | set(fact["pn"].str.lstrip("0"))
    mu = miss.drop_duplicates("pn")
    ever = mu["pn"].isin(billed).sum()
    print(f"unclassified warehouse parts that we have billed at some point: {ever} of {len(mu)}")
except Exception as exc:
    print("sales_fact read failed:", exc)

# ---------- backlog ----------
data = pd.read_excel(B, sheet_name="DATA", header=3, dtype=str)
data = data[data["Material"].notna()].copy()
data["pn"] = data["Material"].map(norm)
data["qty"] = pd.to_numeric(data["Open Qty"], errors="coerce").fillna(0)
data["has_aim"] = data["pn"].isin(aimset)
up = data["Customer"].fillna("").str.upper()
data = data[~up.str.contains("MIDI|RUS|KAZ|CBC-TRANS|GRAND AVTO|KOMTRANS|KIMA")].copy()

print("\n\n=== BACKLOG (in scope), counted by LINES ===")
print(data.groupby("has_aim").agg(lines=("pn", "size"), pcs=("qty", "sum")).to_string(float_format=lambda x: f"{x:,.0f}"))
print("=== BACKLOG, counted by DISTINCT PART ===")
print(data.drop_duplicates("pn").groupby("has_aim").agg(parts=("pn", "size")).to_string())
print("lines per part: classified %.2f | unclassified %.2f"
      % (data[data.has_aim].groupby("pn").size().mean(), data[~data.has_aim].groupby("pn").size().mean()))

print("\n=== the unclassified backlog parts with the most lines ===")
mb = (data[~data.has_aim].groupby(["pn", "Material description"], as_index=False)
      .agg(lines=("qty", "size"), pcs=("qty", "sum"))
      .sort_values("lines", ascending=False).head(15))
print(mb.to_string(index=False, float_format=lambda x: f"{x:,.0f}"))

print("\n=== coverage, matching BOTH the written and the zero-stripped form ===")
for label, s in [("backlog", data["pn"]), ("warehouse", dly["pn"])]:
    uu = set(s)
    hit = sum(1 for x in uu if x in aimset)
    print(f"  {label:10s} distinct parts {len(uu):5d}  classified {hit:5d}  ({100*hit/len(uu):.1f}%)")
