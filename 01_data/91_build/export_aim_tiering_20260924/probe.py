import pandas as pd, numpy as np, json

EX = r'01_data\EXPORT.XLSX'
Q  = r'01_data\91_build\export_aim_eq_20260924\queue.csv'
M  = r'01_data\00_derived\aim_master_v2.csv'

x = pd.read_excel(EX, dtype=str)
print("EXPORT rows:", len(x))
print("EXPORT cols:", list(x.columns))
print()
for c in x.columns:
    nn = x[c].notna().sum()
    print(f"  {c:24s} nonnull={nn:5d}  distinct={x[c].nunique()}")

print()
print("Sales Org:", x['Sales Org'].value_counts(dropna=False).to_dict())
print("PN unique:", x['P/N'].nunique(), "Newest PN unique:", x['Newest P/N'].nunique())
print("Price Condition Type:", x['Price Condition Type'].value_counts(dropna=False).to_dict())
print("Currency:", x['Currency'].value_counts(dropna=False).to_dict())
print("ABC Code:", x['ABC Code'].value_counts(dropna=False).to_dict())
print()
print("--- Commodity Code raw ---")
cc = x['Commodity Code']
print("nonnull:", cc.notna().sum(), "distinct:", cc.nunique())
print(cc.value_counts(dropna=False).head(30).to_string())
print()
print("len distribution of commodity code (as string, stripping .0):")
ccs = cc.dropna().astype(str).str.replace(r'\.0$','',regex=True)
print(ccs.str.len().value_counts().sort_index().to_string())
print()
print("--- Weight column sample ---")
print(x['Weight'].head(10).tolist())
print()
print("--- Value column ---")
v = pd.to_numeric(x['Value'], errors='coerce')
p = pd.to_numeric(x['Price'], errors='coerce')
print("Value nonnull:", v.notna().sum(), "sum:", v.sum())
print("Price nonnull:", p.notna().sum(), "sum:", p.sum())
print()
print("--- Description sample distinct ---")
print("distinct descriptions:", x['Description'].nunique())
print(x['Description'].value_counts().head(25).to_string())
