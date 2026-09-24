"""Probe the inputs for the AIM comparison build. Read-only, derived files only."""
import pandas as pd
from pathlib import Path

DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")

for f in ["pricing_pr00_ie40.parquet", "pricing_sim_pr00_l12m.parquet",
          "pricing_list_pn.parquet"]:
    p = DER / f
    print("=" * 70)
    print(f, "exists:", p.exists())
    if not p.exists():
        continue
    df = pd.read_parquet(p)
    print("shape", df.shape)
    print("cols", list(df.columns))
    print(df.head(3).to_string())

print("=" * 70)
sf = pd.read_parquet(DER / "sales_fact.parquet")
print("sales_fact", sf.shape, list(sf.columns))
print(sf.dtypes.to_string())
print(sf.head(3).to_string())
print("date range", sf.billing_date.min(), sf.billing_date.max())
