"""Read-only probe 6: do the three intermediates the builders read carry AIM classification?"""
import os

import pandas as pd

DER = r"01_data\00_derived"
for f in ["parts_catalog_dimension.csv", "bvp_pn_dimension.csv", "pms_capture_by_db_year.csv"]:
    p = os.path.join(DER, f)
    df = pd.read_csv(p, dtype=str, nrows=8, low_memory=False)
    print("=" * 90)
    print(f)
    print("columns:", list(df.columns))
    print(df.head(4).to_string())
