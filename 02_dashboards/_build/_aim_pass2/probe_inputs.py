"""Read-only probe: timestamps of the inputs the four builders read, and AIM coverage on IE40."""
import datetime
import os

import pandas as pd

DER = r"01_data\00_derived"

FILES = [
    "parts_catalog_dimension.csv",
    "pricing_pr00_ie40.parquet",
    "bvp_pn_dimension.csv",
    "distributor_dimension.csv",
    "sales_fact.parquet",
    "pms_capture_by_db_year.csv",
    "pricing_sim_pr00_l12m.parquet",
    "pricing_list_pn.parquet",
    "AIM_Master_PN_Categories_Figkey_20260921.csv",
    "AIM_Master_PN_Categories_Figkey_20260924.csv",
    "aim_pn_classification.csv",
    "aim_master_v2.csv",
]
print("== input stamps")
for f in FILES:
    p = os.path.join(DER, f)
    if os.path.exists(p):
        st = os.stat(p)
        print(f"{f:<58} {st.st_size:>12,}  "
              f"{datetime.datetime.fromtimestamp(st.st_mtime):%Y-%m-%d %H:%M:%S}")
    else:
        print(f"{f:<58} MISSING")


def norm(s: pd.Series) -> pd.Series:
    return (s.astype(str).str.strip()
            .str.replace(r"\.0$", "", regex=True)
            .str.lstrip("0")
            .replace("", "0"))


PLACE = {"", "nan", "none", "unknown", "unknown review", "null"}

pr = pd.read_parquet(os.path.join(DER, "pricing_pr00_ie40.parquet"))
pns = set(norm(pr["part_number"]).unique())
print(f"\n== IE40 price extract: {len(pr):,} rows, {len(pns):,} distinct part numbers")

for name in ["AIM_Master_PN_Categories_Figkey_20260921.csv",
             "AIM_Master_PN_Categories_Figkey_20260924.csv"]:
    a = pd.read_csv(os.path.join(DER, name), dtype=str, low_memory=False)
    a["pn"] = norm(a["part_number"])
    a = a.drop_duplicates("pn")
    sub = a[a["pn"].isin(pns)]
    l1 = sub["aim_level_1"].fillna("").astype(str).str.strip().str.lower()
    real = int((~l1.isin(PLACE)).sum())
    parts = int(sub["line_kind"].fillna("").astype(str).str.strip().eq("part").sum())
    print(f"{name}: rows {len(a):,} | IE40 pns present {len(sub):,} | "
          f"with a real aim_level_1 {real:,} | line_kind=part {parts:,}")
