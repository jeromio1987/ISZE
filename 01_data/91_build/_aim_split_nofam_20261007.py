"""Split 'no AIM' into: not in the classification file at all, versus in the file but no family assigned."""
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
aim["fam"] = aim["aim_l1"].fillna("").str.strip()
print("AIM rows:", len(aim), "| rows with a family:", int((aim['fam'] != '').sum()),
      "| rows without one:", int((aim['fam'] == '').sum()))
fam_by_pn = aim.groupby("pn")["fam"].apply(lambda s: max(s, key=len) if len(s) else "").to_dict()
print("distinct part numbers in AIM:", len(fam_by_pn),
      "| of those with a family:", sum(1 for v in fam_by_pn.values() if v))


def split(name, pns, qtys):
    present_no_fam = 0
    absent = 0
    ok = 0
    for p, q in zip(pns, qtys):
        if p in fam_by_pn:
            if fam_by_pn[p]:
                ok += 1
            else:
                present_no_fam += 1
        else:
            absent += 1
    tot = len(pns)
    print(f"\n=== {name} ({tot} lines) ===")
    print(f"  has a family               {ok:5d}  ({100*ok/tot:5.1f}%)")
    print(f"  in the file, no family yet {present_no_fam:5d}  ({100*present_no_fam/tot:5.1f}%)")
    print(f"  not in the file at all     {absent:5d}  ({100*absent/tot:5.1f}%)")


dly = pd.read_excel(D, sheet_name="isze", dtype=str)
dly["pn"] = dly["PN"].map(norm)
dly["qty"] = pd.to_numeric(dly["Q'ty"], errors="coerce").fillna(0)
split("IML warehouse, all lines", dly["pn"], dly["qty"])

old = dly[dly["pn"].notna()]
data = pd.read_excel(B, sheet_name="DATA", header=3, dtype=str)
data = data[data["Material"].notna()].copy()
data["pn"] = data["Material"].map(norm)
data["qty"] = pd.to_numeric(data["Open Qty"], errors="coerce").fillna(0)
up = data["Customer"].fillna("").str.upper()
data = data[~up.str.contains("MIDI|RUS|KAZ|CBC-TRANS|GRAND AVTO|KOMTRANS|KIMA")].copy()
split("customer backlog, in scope", data["pn"], data["qty"])

print("\n=== what the 'in the file, no family yet' parts look like (backlog) ===")
nofam = [p for p in data["pn"] if p in fam_by_pn and not fam_by_pn[p]]
sub = data[data["pn"].isin(set(nofam))]
print(sub[["pn", "Material description", "Customer", "Open Qty"]].head(12).to_string(index=False))

print("\n=== and in the warehouse ===")
nofam_w = [p for p in dly["pn"] if p in fam_by_pn and not fam_by_pn[p]]
subw = dly[dly["pn"].isin(set(nofam_w))]
print("lines:", len(subw), "| pieces:", f"{subw['qty'].sum():,.0f}")
print(subw[["pn", "Part Name", "Q'ty", "Status"]].head(12).to_string(index=False))
