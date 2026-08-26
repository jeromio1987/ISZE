import pandas as pd, numpy as np, sys
sys.stdout.reconfigure(encoding='utf-8')

D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX"
SRC = r"c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx"

cheap250 = pd.read_csv(f"{D}\\_cheap250.csv", dtype=str)
pc = pd.read_csv(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\parts_catalog_dimension.csv", dtype=str)

# hypothesis: 249/250 = "in catalog" not "PMS"
pc_pn = set(pc['part_number'].astype(str).str.strip())
c250 = set(cheap250['Material'].astype(str).str.strip())
print("250 cheap parts in parts_catalog (any row):", len(c250 & pc_pn))

# DG parts entity split
df = pd.read_excel(SRC, sheet_name='Data (joined)', header=3, dtype={'Material': str, 'Sold-to pt': str})
df['Material'] = df['Material'].astype(str).str.strip()
df['MoT'] = df['MoT'].astype(str).str.strip()
df['Entity'] = df['Entity'].astype(str).str.strip()
df['BillT'] = df['BillT'].astype(str).str.strip()
df['Is DG'] = df['Is DG'].astype(str).str.strip().str.lower()

g = df[(df['BillT']=='F2') & (df['Material']!='REBATE')].copy()
dg = g[g['Is DG']=='true'].copy()
print("\nDG shipped lines (F2, Is DG true):", len(dg))
dg_mats = dg.groupby('Material').agg(
    lines=('Qty','size'),
    qty=('Qty','sum'),
    value=('EUR Amount','sum'),
    air_lines=('MoT', lambda s: (s=='Air').sum()),
    sea_lines=('MoT', lambda s: (s=='Sea').sum()),
    entities=('Entity', lambda s: ','.join(sorted(set(s)))),
    desc=('Description','first'),
).reset_index()
print("distinct DG materials shipped:", len(dg_mats))

# family classification via description keyword
def fam(d):
    d = str(d).upper()
    if 'AIR BAG' in d: return 'Airbag'
    if 'BELT' in d and ('SEAT' in d or 'BUCKLE' in d or 'TONGUE' in d): return 'Seatbelt pretensioner'
    if 'CONTROL UNIT' in d: return 'SRS control unit'
    if 'OIL' in d or 'LUBRIC' in d or 'GREASE' in d: return 'Bulk lubricant'
    return 'OTHER'

dg_mats['family'] = dg_mats['desc'].apply(fam)
print("\nDG family counts:")
print(dg_mats['family'].value_counts())

print("\nentity split of DG parts (entities = which distributor shipped them):")
print(dg_mats['entities'].value_counts())

# per entity: UMI=LCV, UTI=CV proxy
dg_mats.to_csv(f"{D}\\_dg_parts.csv", index=False)
print("\n===== full DG parts list (42) =====")
for _, r in dg_mats.sort_values('value', ascending=False).iterrows():
    ent = r['entities']
    seg = 'LCV (UMI)' if ent=='UMI' else ('CV (UTI)' if ent=='UTI' else 'BOTH')
    print(f"{r['Material']} | {r['desc']} | {r['family']} | {ent} ({seg}) | lines {int(r['lines'])} (air {int(r['air_lines'])}/sea {int(r['sea_lines'])}) | {r['value']:.0f}€")
