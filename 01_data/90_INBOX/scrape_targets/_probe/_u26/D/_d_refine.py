# -*- coding: utf-8 -*-
"""Split REQUIRED_FIELD_EMPTY into the two real cases, and record what the raw row does carry."""
import re
from pathlib import Path

import pandas as pd

MAIN = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = Path(__file__).resolve().parent
F_ONL = MAIN / "01_data" / "Eucon_Online28072025.xlsx"


def find10(x):
    if pd.isna(x):
        return []
    return re.findall(r"\b\d{10}\b", str(x))


def num(s):
    return pd.to_numeric(s.astype(str).str.replace(",", ".", regex=False), errors="coerce")


def z(s):
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(10)


onl = pd.read_excel(F_ONL, sheet_name="Fresh list_Export_28072025_0932", dtype=str)
onl["rrp"] = num(onl["RRP"])
onl["oerrp"] = num(onl["OE RRP"])
onl["key"] = onl["Brand"].astype(str).str.upper().str.replace(r"[^A-Z0-9]", "", regex=True) + "|" + \
             onl["Part Number"].astype(str).str.upper().str.replace(r"[^A-Z0-9]", "", regex=True)
oe_by_brandpn = {}
for _, r in onl.iterrows():
    oe_by_brandpn.setdefault(r.key, []).append(r.oerrp)

mo = pd.read_csv(OUT / "missing_observations.csv", dtype=str)
mo["raw_oe_price"] = ""
mo["note_detail"] = ""

n_split = 0
for i, r in mo.iterrows():
    if r.why_missing != "REQUIRED_FIELD_EMPTY":
        continue
    k = re.sub(r"[^A-Z0-9]", "", str(r.competitor_brand).upper()) + "|" + \
        re.sub(r"[^A-Z0-9]", "", str(r.competitor_pn).upper())
    vals = [v for v in oe_by_brandpn.get(k, []) if pd.notna(v)]
    if vals:
        mo.at[i, "raw_oe_price"] = "%.2f" % vals[0]
        mo.at[i, "why_missing"] = "NO_COMPETITOR_PRICE_BUT_OUR_NUMBER_PRICED"
        mo.at[i, "note_detail"] = ("the row states no competitor price (RRP blank); it does state "
                                   "OE RRP %.2f EUR for our own number, which the loader is not allowed to load" % vals[0])
    else:
        mo.at[i, "why_missing"] = "ROW_HAS_NO_PRICE_AT_ALL"
        mo.at[i, "note_detail"] = "no competitor price and no own-number price on the row"
    n_split += 1

mo.to_csv(OUT / "missing_observations.csv", index=False, encoding="utf-8")
print("rows re-coded:", n_split)
print(mo.why_missing.value_counts().to_dict())
print()
print("per file:")
print(mo.groupby(["why_missing", "raw_file"]).size().to_string())
