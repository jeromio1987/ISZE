"""Read-only probe 4: the newly-classified set between the two AIM pairs, and the page headline
counts (units not classified in AIM) that the four pages actually print."""
import os

import numpy as np
import pandas as pd

DER = r"01_data\00_derived"


def norm(s: pd.Series) -> pd.Series:
    return (s.astype(str).str.strip()
            .str.replace(r"\.0$", "", regex=True)
            .str.lstrip("0")
            .replace("", "0"))


PLACE = {"", "nan", "none", "unknown", "unknown review", "null"}

p21 = pd.read_csv(os.path.join(DER, "AIM_Master_PN_Categories_Figkey_20260921.csv"),
                  dtype=str, low_memory=False)
p24 = pd.read_csv(os.path.join(DER, "AIM_Master_PN_Categories_Figkey_20260924.csv"),
                  dtype=str, low_memory=False)

for df in (p21, p24):
    df["pn"] = norm(df["part_number"])
    df["l1"] = df["aim_level_1"].fillna("").astype(str).str.strip()
    df["isreal"] = ~df["l1"].str.lower().isin(PLACE)
    df["ispart"] = df["line_kind"].fillna("").astype(str).str.strip().eq("part")

s21 = p21.drop_duplicates("pn").set_index("pn")
s24 = p24.drop_duplicates("pn").set_index("pn")

real21 = set(s21.index[s21["isreal"]])
real24 = set(s24.index[s24["isreal"]])
newly = real24 - real21
lost = real21 - real24
print(f"rows 21 {len(p21):,}   rows 24 {len(p24):,}")
print(f"PNs with a real aim_level_1: 21 -> {len(real21):,}   24 -> {len(real24):,}")
print(f"newly classified (real on 24, not on 21): {len(newly):,}")
print(f"lost (real on 21, not on 24): {len(lost):,}")
print(f"of the newly classified, line_kind=part: "
      f"{int(s24.loc[sorted(newly)]['ispart'].sum()):,}")

pr = pd.read_parquet(os.path.join(DER, "pricing_pr00_ie40.parquet"))
ie = set(norm(pr["part_number"]).unique())
print(f"\nIE40 price extract part numbers: {len(ie):,}")
print(f"newly classified AND on the IE40 extract: {len(newly & ie):,}")
print(f"real on 24 AND on the IE40 extract: {len(real24 & ie):,}")
print(f"real on 21 AND on the IE40 extract: {len(real21 & ie):,}")

# level-1 mix on the newly classified set
sub = s24.loc[sorted(newly & ie)]
print("\nlevel 1 of the newly classified that sit on the IE40 extract:")
print(sub["l1"].value_counts().head(20).to_string())
