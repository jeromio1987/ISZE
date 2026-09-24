"""What axis each candidate column actually carries, and how many part numbers are on it."""
import os
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

DER = r"01_data\00_derived"


def norm(s: pd.Series) -> pd.Series:
    return (s.astype(str).str.strip()
            .str.replace(r"\.0$", "", regex=True)
            .str.lstrip("0")
            .replace("", "0"))


cols = [
    (r"aim_pn_classification.csv", "aim_l1"),
    (r"aim_pn_classification.csv", "catalog_l1"),
    (r"aim_pn_classification_20260920.csv", "workbook_l1"),
    (r"aim_pn_classification_20260920.csv", "catalog_l1"),
    (r"aim_pn_classification_20260920.csv", "aim_l1_fixed"),
    (r"aim_master_v2.csv", "aim_l1"),
    (r"aim_master_v2.csv", "aim_l1_fixed"),
    (r"aim_master_v2.csv", "cat_l1"),
]

for f, c in cols:
    df = pd.read_csv(os.path.join(DER, f), dtype=str, low_memory=False,
                     usecols=lambda x: x in ("part_number", c))
    if c not in df.columns:
        print(f"{f}  {c}: column absent")
        continue
    s = df[c].fillna("").astype(str).str.strip()
    vc = s.value_counts()
    print("=" * 96)
    print(f"{f}  ->  {c}")
    print(f"  rows {len(df):,}   blank {int(s.eq('').sum()):,}   distinct {s.nunique():,}")
    print("  top 12: " + " | ".join(f"{k or '(blank)'}={v:,}" for k, v in vc.head(12).items()))
