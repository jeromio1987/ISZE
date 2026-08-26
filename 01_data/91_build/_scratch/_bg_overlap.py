import pandas as pd, sys
sys.stdout.reconfigure(encoding='utf-8')

# Load study materials
df = pd.read_excel(r"c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx",
                   sheet_name='Data (joined)', header=3,
                   dtype={'Material': str})
mats = set(df['Material'].dropna().astype(str).str.strip())

pc = pd.read_csv(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\parts_catalog_dimension.csv", dtype=str)
bv = pd.read_csv(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\bvp_pn_dimension.csv", dtype=str)

pc_pn = set(pc['part_number'].dropna().astype(str).str.strip())
bv_pn = set(bv['part_number'].dropna().astype(str).str.strip())

print("study materials:", len(mats))
print("overlap with parts_catalog part_number:", len(mats & pc_pn))
print("overlap with bvp part_number:", len(mats & bv_pn))

# sample of study materials
print("\nsample study materials:", sorted(list(mats))[:10])

# check if parts_catalog has any 8/9/10 digit that look like genuine
import re
genuine_like = [x for x in pc_pn if re.fullmatch(r'[0-9]{10}', x)]
print("\nparts_catalog 10-digit part_numbers count:", len(genuine_like), genuine_like[:5])

# check bvp part numbers length distribution
lens = bv['part_number'].str.len().value_counts()
print("\nbvp part_number length dist:", dict(lens))

# maybe the mapping key is different. Check genuine_bvp_crossref.csv
try:
    x = pd.read_csv(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\genuine_bvp_crossref.csv", dtype=str)
    print("\ngenuine_bvp_crossref columns:", list(x.columns), "rows", len(x))
    print(x.head(5).to_string())
except Exception as e:
    print("crossref err", e)
