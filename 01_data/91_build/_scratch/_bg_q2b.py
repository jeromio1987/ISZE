import pandas as pd, sys
sys.stdout.reconfigure(encoding='utf-8')

D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX"
dg = pd.read_csv(f"{D}\\_dg_parts.csv", dtype=str)
dg_pn = set(dg['Material'])

x = pd.read_csv(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\genuine_bvp_crossref.csv", dtype=str)
print("genuine_bvp_crossref rows:", len(x))
hit = x[x['genuine_pn'].isin(dg_pn)]
print("DG parts in genuine_bvp_crossref (vehicle_model available):", len(hit))
if len(hit):
    print(hit[['genuine_pn','product_family','vehicle_model','engine_type']].to_string(index=False))

# distinct vehicle_model examples to understand CV vs LCV coding
print("\nvehicle_model distinct count:", x['vehicle_model'].nunique())
print("examples:", x['vehicle_model'].dropna().unique()[:25])

# check parts_catalog / bvp for any part-number -> model link via fig_key (model-specific fig keys?)
# model_dimension columns
md = pd.read_csv(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\07_UIO\vin\model_dimension.csv", dtype=str)
print("\nmodel_dimension series values:", sorted(md['series'].dropna().unique()))
