"""Read-only: reconcile the 199 EPC-only part numbers against the master as it stands now.

Nothing is written. Two columns matter and they behave differently downstream:
  aim_l1 / aim_l2 / aim_l3            the base column
  aim_l1_fixed / aim_l2_fixed         the override, which the Power BI export reads FIRST
  has_aim                             the flag open_why.py classified on

The published pair is read too, because that is the file Jerome's Power BI actually loads.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
EQ = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"

PLACE = {"", "nan", "none", "null", "unknown", "unknown review", "unclassified", "to review"}


def real(s: pd.Series) -> pd.Series:
    return ~s.fillna("").astype(str).str.strip().str.lower().isin(PLACE)


pns = json.loads((EQ / "open_worklist_epc_only_20260924.json").read_text(encoding="utf-8"))
print(f"EPC-only list: {len(pns)} part numbers")

m = pd.read_csv(DER / "aim_master_v2.csv", dtype=str, low_memory=False)
m["k"] = m["part_number"].fillna("").astype(str).str.strip().str.upper()
mi = m.drop_duplicates("k", keep="first").set_index("k")
g = mi.reindex(pns)

on_master = g["part_number"].notna()
print(f"on the master now: {int(on_master.sum())} | not on the master: {int((~on_master).sum())}")

base_ok = real(g["aim_l1"])
fixed_ok = real(g["aim_l1_fixed"])
has_aim = pd.to_numeric(g["has_aim"], errors="coerce").fillna(0).astype(int) == 1

print()
print("still with no family (base aim_l1 blank or placeholder):", int((~base_ok).sum()))
print("carrying a real aim_l1_fixed override                  :", int(fixed_ok.sum()))
print("has_aim = 1 on the master                              :", int(has_aim.sum()))
print("read as the published file reads it (fixed wins, else base):",
      int((fixed_ok | base_ok).sum()), "closed /",
      int((~(fixed_ok | base_ok)).sum()), "still open")

print()
print("of the not-on-master 43, aim_source stamp is not applicable (no row)")
print()
print("aim_source of the rows that now carry a family:")
print(g.loc[(fixed_ok | base_ok), "aim_source"].fillna("(blank)").value_counts().to_string())

# the published pair, which is what Power BI loads
pair = DER / "AIM_Master_PN_Categories_Figkey_20260924.csv"
if pair.exists():
    p = pd.read_csv(pair, dtype=str, low_memory=False)
    p["k"] = p["part_number"].fillna("").astype(str).str.strip().str.upper()
    pi = p.drop_duplicates("k", keep="first").set_index("k")
    pg = pi.reindex(pns)
    l1 = pg["aim_level_1"].fillna("").astype(str)
    planted = real(l1)
    print()
    print(f"published pair {pair.name} (mtime {pd.Timestamp(pair.stat().st_mtime, unit='s')}):")
    print("  rows for the 199:", int(pg["part_number"].notna().sum()))
    print("  showing a real family:", int(planted.sum()))
    print("  showing Unknown / blank:", int((~planted).sum()))
    print("  of the blanks:", l1[~planted].replace("", "(blank)").value_counts().to_dict())

# do the 4 lamp rows that sit in DATA_NOT_IN_MASTER appear in the carve-out set too?
cls = pd.read_csv(ROOT / "01_data" / "91_build" / "export_aim_open_why_20260924" / "open_parts_classified.csv",
                  dtype=str, encoding="utf-8-sig")
carve = cls[cls["group"] == "DATA_CARVED_OUT_BY_HAND"]
print()
print("carve-out group (not added to the EPC-only list):", len(carve))
print(carve[["pnk", "description", "list_eur", "detail"]].to_string(index=False))
