"""The APL parts lists carry a vehicle_code per part number. Does it band the billing?"""

import pandas as pd

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
DER = ROOT + r"\01_data\00_derived"
norm = lambda x: (str(x).strip().lstrip("0") or "0")

apl = pd.read_csv(DER + r"\apl_pn_list_long_20260812.csv", low_memory=False,
                  usecols=["part_number", "vehicle_code", "source_pack", "description"])
apl["_pn"] = apl.part_number.map(norm)
vc = apl.vehicle_code.astype(str).str.strip()
print(f"APL rows {len(apl):,}   distinct PNs {apl._pn.nunique():,}")
print(f"vehicle_code empty/nan: {vc.isin(['','nan','None','-']).mean()*100:.1f}%")
print(f"distinct vehicle_code values: {vc.nunique()}")
print()
print("the 40 most common vehicle_code values:")
print(vc.value_counts().head(40).to_string())
print()
print("source_pack values:")
print(apl.source_pack.astype(str).value_counts().head(15).to_string())

# How much of the billed book does this reach?
sf = pd.read_parquet(DER + r"\sales_fact.parquet")
sf["_pn"] = sf.part_number.map(norm)
book = sf.groupby("_pn").net_sales_value.sum()
tot = book.sum()
covered = book.reindex(apl._pn.unique())
print()
print(f"billed book            : EUR {tot:,.0f}")
print(f"reached by the APL file : EUR {covered.sum():,.0f}  ({100*covered.sum()/tot:.1f}%)")
single = apl.drop_duplicates("_pn")
c = book.reindex(single._pn)
print(f"PNs with exactly one vehicle_code in APL: {len(single):,}, EUR {c.sum():,.0f} "
      f"({100*c.sum()/tot:.1f}%)")
