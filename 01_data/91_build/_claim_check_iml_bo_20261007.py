"""Claim check (2026-10-07).

Claim 1: the IML warehouse extract "stops at packing" - Invoice, Shipped and ETD are empty on all rows.
Claim 2: when a line leaves the weekly BO file, the file does not say whether it shipped, was
         cancelled or was pulled.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

IML = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\ISZE_Order Status as of 2 October 2026_request to check.xlsx")
BO = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_natalie_bo_wk41_20261007\2026-10-06_1147_Natalie_BO info VP 06-10-2026.xlsx")


def blank(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.strip().replace({"nan": ""}) == ""


print("=" * 78)
print("CLAIM 1 - does the IML warehouse extract stop at packing?")
print("=" * 78)
dly = pd.read_excel(IML, sheet_name="isze", dtype=str)
print(f"rows: {len(dly)}   columns: {len(dly.columns)}")
print()
print(f"{'column':<26}{'filled':>8}{'blank':>8}   sample non-blank value")
for c in dly.columns:
    b = blank(dly[c])
    filled = int((~b).sum())
    sample = ""
    nb = dly.loc[~b, c]
    if len(nb):
        sample = str(nb.iloc[0])[:34]
    flag = "   <-- EMPTY" if filled == 0 else ""
    print(f"{c:<26}{filled:>8}{int(b.sum()):>8}   {sample}{flag}")

for c in ["Invoice", "Shipped", "ETD"]:
    if c in dly.columns:
        filled = int((~blank(dly[c])).sum())
        print(f"\nVERDICT {c}: filled on {filled} of {len(dly)} rows")

print()
print("=" * 78)
print("CLAIM 2 - does the BO file say why a line left the list?")
print("=" * 78)
data = pd.read_excel(BO, sheet_name="DATA", header=3, dtype=str).dropna(how="all")
data.columns = [str(c).strip() for c in data.columns]
print("DATA columns:")
for c in data.columns:
    print("   ", c)
print()
if "Remark" in data.columns:
    r = data["Remark"].fillna("").astype(str).str.strip()
    nb = r[(r != "") & (r.str.lower() != "nan")]
    print(f"Remark column: {len(nb)} of {len(data)} rows carry anything")
    if len(nb):
        top = nb.value_counts().head(12)
        print("most common Remark values:")
        for v, k in top.items():
            print(f"   {k:>5}  {v[:70]}")
    else:
        print("Remark is empty on every row of the central file.")
else:
    print("No Remark column in the central file.")

# any column that looks like a status / reason / resolution?
print()
print("columns whose NAME suggests a status or reason:")
for c in data.columns:
    if re.search(r"(?i)status|reason|remark|cancel|resolv|confirm|confirm|deliv|hold", str(c)):
        vals = data[c].fillna("").astype(str).str.strip()
        nb = vals[(vals != "") & (vals.str.lower() != "nan")]
        print(f"   {c}: {len(nb)} of {len(data)} filled", end="")
        if len(nb):
            print(f" | example: {nb.iloc[0][:40]}")
        else:
            print(" | all blank")

print()
print("=" * 78)
print("CLAIM 2b - the ETD/supply sheet: any resolution or transit reference?")
print("=" * 78)
etd = pd.read_excel(BO, sheet_name="ETD", header=0, dtype=str)
etd.columns = [str(c).strip() for c in etd.columns]
for c in etd.columns:
    b = blank(etd[c])
    filled = int((~b).sum())
    sample = str(etd.loc[~b, c].iloc[0])[:36] if filled else ""
    print(f"{c:<22}{filled:>6} of {len(etd):<6} {sample}")
