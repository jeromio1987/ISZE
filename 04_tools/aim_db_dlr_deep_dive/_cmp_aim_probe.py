"""Probe AIM tree, PMS/BVP maps, and the size of the comparison payload."""
from pathlib import Path
import pandas as pd
import numpy as np

DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")


def norm(s):
    return (s.astype(str).str.strip()
            .str.replace(r"\.0$", "", regex=True)
            .str.lstrip("0").replace("", "0"))


aim = pd.read_csv(DER / "AIM_Master_PN_Categories_Figkey_20260921.csv",
                  dtype=str, low_memory=False)
aim["pn"] = norm(aim["part_number"])
aim = aim.drop_duplicates("pn")
lk = aim["line_kind"].fillna("").astype(str).str.strip()
print("AIM rows", len(aim), "line_kind counts:", lk.value_counts().to_dict())
part = aim[lk == "part"]
print("with aim_level_1:", part["aim_level_1"].notna().sum())
print("\nAIM level 1 values (line_kind=part):")
print(part["aim_level_1"].fillna("(blank)").value_counts().to_string())
print("\ndistinct L1:", part["aim_level_1"].nunique(),
      "L2:", part["aim_level_2"].nunique(), "L3:", part["aim_level_3"].nunique())
print("\nhow many part rows have no L1:",
      int(part["aim_level_1"].isna().sum() + (part["aim_level_1"].fillna("").str.lower()
                                              .isin(["", "nan", "none", "unknown",
                                                     "unknown review", "null"])).sum()))
