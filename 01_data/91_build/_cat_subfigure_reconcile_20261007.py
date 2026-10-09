"""Reconcile the two sub-figures in the scope addition: the 'shared first six digits' count and the 163 families."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DELAY = ROOT / "01_data" / "ISZE_Order Status as of 2 October 2026_request to check.xlsx"
AIM = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
FACT = ROOT / "01_data" / "00_derived" / "sales_fact.parquet"
OLD = ROOT / "01_data" / "00_derived" / "aim_pn_classification.csv.bak_pre_eq_20260917"


def norm(v) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", str(v if v is not None else ""))


aim = pd.read_csv(AIM, dtype=str, low_memory=False)
aim["pn"] = aim["part_number"].fillna("").map(norm)
fam = {}
for p, f, fx in zip(aim["pn"], aim["aim_l1"].fillna("").str.strip(), aim["aim_l1_fixed"].fillna("").str.strip()):
    if not p:
        continue
    v = f or fx
    k = p.lstrip("0")
    if v and (k not in fam or not fam[k]):
        fam[k] = v
master_keys = {p.lstrip("0") for p in aim["pn"] if p}
cat_names = {c for c in aim["cat_l1"].fillna("").str.strip() if c}

dly = pd.read_excel(DELAY, sheet_name="isze", dtype=str)
dly["pn"] = dly["PN"].map(norm)
absent = sorted({p for p in dly["pn"] if p.lstrip("0") not in master_keys})
print(f"absent warehouse part numbers: {len(absent)}")

fact = pd.read_parquet(FACT)
fact["pn"] = fact["part_number"].map(norm)
billed_keys = {p.lstrip("0") for p in fact["pn"] if p}

# method A: compare first six digits against parts we BILLED
pref6_billed = {p[:6] for p in billed_keys if len(p) >= 6}
a = sum(1 for p in absent if p[:6] in pref6_billed)
print(f"shared first 6 against parts we BILLED          : {a} of {len(absent)}")

# method B: compare against every part number in the classification master
pref6_master = {p[:6] for p in master_keys if len(p) >= 6}
b = sum(1 for p in absent if p[:6] in pref6_master)
print(f"shared first 6 against the CLASSIFICATION master: {b} of {len(absent)}")

# method C: any 6 consecutive digits rather than the leading six
pref_any_billed = set()
for p in billed_keys:
    for i in range(0, len(p) - 5):
        pref_any_billed.add(p[i:i + 6])
c = sum(1 for p in absent if p[:6] in pref_any_billed)
print(f"leading 6 digits appearing anywhere in a billed part: {c} of {len(absent)}")

# --- the 163 question: at family-NAME level ---
old = pd.read_csv(OLD, dtype=str, low_memory=False)
old["pn"] = old["part_number"].map(norm)
old = old[old["pn"].notna() & (old["pn"] != "")]
old["oldfam"] = old["aim_l1"].fillna("").str.strip()
old_fams = {v for v in old["oldfam"] if v}
print(f"\nold file: distinct aim_l1 values {len(old_fams)}")
now_fams = set(fam.values())
as_catalogue = {v for v in old_fams if v in cat_names}
print(f"  of those, values that are really catalogue category names: {len(as_catalogue)}")
real_old_fams = old_fams - as_catalogue
print(f"  real family names in the old file: {len(real_old_fams)}")
gone = {v for v in real_old_fams if v not in now_fams}
print(f"  real family names that no longer appear in the current master: {len(gone)}")
print("  sample:", sorted(gone)[:12])
