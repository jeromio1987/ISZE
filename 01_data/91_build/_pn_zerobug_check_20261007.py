"""Measure the part-number leading-zero bug: numeric Excel read vs string read, against AIM coverage."""
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
aimset = set(p for p in aim["pn"] if p)
print("AIM part numbers in the classification file:", len(aimset))
print("AIM rows with a usable part number:", int((aim['pn'] != '').sum()), "of", len(aim))
print()

bo_num = pd.read_excel(B, sheet_name="DATA", header=3)["Material"].dropna().map(norm)
bo_str = pd.read_excel(B, sheet_name="DATA", header=3, dtype=str)["Material"].dropna().map(norm)
iml_num = pd.read_excel(D, sheet_name="isze")["PN"].dropna().map(norm)
iml_str = pd.read_excel(D, sheet_name="isze", dtype=str)["PN"].dropna().map(norm)

for label, s in [("backlog, read as text", bo_str), ("backlog, read as numbers", bo_num),
                 ("warehouse, read as text", iml_str), ("warehouse, read as numbers", iml_num)]:
    u = sorted(set(s))
    hit = sum(1 for x in u if x in aimset)
    print(f"{label:28s} distinct parts {len(u):5d}   matched in AIM {hit:5d}  ({100*hit/len(u):5.1f}%)")

print()
lost_bo = sum(1 for x in set(bo_str) if x.startswith("0") and x.lstrip("0") not in aimset)
print("backlog parts that start with a zero in the file:", len([x for x in set(bo_str) if x.startswith('0')]))
print("  of those, how many the numeric read would have broken:", lost_bo)
print("warehouse parts that start with a zero:", len([x for x in set(iml_str) if x.startswith('0')]))
print()
print("sample: file value -> wrongly digit-stripped value")
for x in [x for x in sorted(set(bo_str)) if x.startswith("0")][:8]:
    print(f"  {x}  ->  {x.lstrip('0')}   (in AIM as written: {x in aimset}, as stripped: {x.lstrip('0') in aimset})")
