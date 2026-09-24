"""Read-only probe 5: try to reproduce the brief's 1,303 / 1,225 / 0 figures on a narrower subset."""
import os

import pandas as pd

DER = r"01_data\00_derived"


def norm(s: pd.Series) -> pd.Series:
    return (s.astype(str).str.strip()
            .str.replace(r"\.0$", "", regex=True)
            .str.lstrip("0")
            .replace("", "0"))


PLACE = {"", "nan", "none", "unknown", "unknown review", "null"}

m = pd.read_parquet(os.path.join(DER, "sales_fact.parquet"), columns=["part_number"])
# master columns
hdr = pd.read_csv(os.path.join(DER, "aim_master_v2.csv"), dtype=str, nrows=5, low_memory=False)
print("aim_master_v2 columns:", list(hdr.columns))

pr = pd.read_parquet(os.path.join(DER, "pricing_pr00_ie40.parquet"))
ie = set(norm(pr["part_number"]).unique())

for name in ["AIM_Master_PN_Categories_Figkey_20260921.csv",
             "AIM_Master_PN_Categories_Figkey_20260924.csv"]:
    a = pd.read_csv(os.path.join(DER, name), dtype=str, low_memory=False)
    a["pn"] = norm(a["part_number"])
    a["l1"] = a["aim_level_1"].fillna("").astype(str).str.strip()
    a["isreal"] = ~a["l1"].str.lower().isin(PLACE)
    if "aim_source" in a.columns:
        print(f"\n{name} aim_source mix:")
        print(a["aim_source"].fillna("(blank)").value_counts().head(12).to_string())
        print("l12m_billed_eur present rows:",
              int(pd.to_numeric(a["l12m_billed_eur"], errors="coerce").notna().sum()))
