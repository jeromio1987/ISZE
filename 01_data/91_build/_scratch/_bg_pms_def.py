import pandas as pd, sys
sys.stdout.reconfigure(encoding='utf-8')

pc = pd.read_csv(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\parts_catalog_dimension.csv", dtype=str)
bv = pd.read_csv(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\bvp_pn_dimension.csv", dtype=str)

print("=== parts_catalog_dimension ===")
print("rows", len(pc), "unique part_number", pc['part_number'].nunique())
print("columns:", list(pc.columns))
print("\npms_category value counts (top 30):")
print(pc['pms_category'].fillna('<NA>').value_counts().head(30))
print("\npms_registry value counts:")
print(pc['pms_registry'].fillna('<NA>').value_counts())
print("\nclassification_source value counts:")
print(pc['classification_source'].fillna('<NA>').value_counts())

print("\n\n=== bvp_pn_dimension ===")
print("rows", len(bv), "unique part_number", bv['part_number'].nunique())
print("\npms_flag value counts:")
print(bv['pms_flag'].fillna('<NA>').value_counts())
print("\npms_category value counts:")
print(bv['pms_category'].fillna('<NA>').value_counts().head(30))

# any column that looks CV/LCV?
print("\n\n=== search for CV/LCV/segment/model columns ===")
for df, name in [(pc,'pc'), (bv,'bv')]:
    for c in df.columns:
        cl = c.lower()
        if any(k in cl for k in ['cv','lcv','segment','model','application','vehicle','range','truck','dmax','d-max']):
            print(name, c, df[c].fillna('<NA>').value_counts().head(10))
