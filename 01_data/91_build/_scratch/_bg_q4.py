import pandas as pd, numpy as np, sys
sys.stdout.reconfigure(encoding='utf-8')

D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX"

cheap250 = pd.read_csv(f"{D}\\_cheap250.csv", dtype=str)
top80 = pd.read_csv(f"{D}\\_top80.csv", dtype=str)
pc = pd.read_csv(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\parts_catalog_dimension.csv", dtype=str)
bv = pd.read_csv(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\bvp_pn_dimension.csv", dtype=str)

# PMS def: pms_category non-empty (either source)
pc['pms_category'] = pc['pms_category'].fillna('').astype(str).str.strip()
bv['pms_category'] = bv['pms_category'].fillna('').astype(str).str.strip()
bv['pms_flag'] = bv['pms_flag'].fillna('').astype(str).str.strip()

pc_pms = pc[pc['pms_category']!=''][['part_number','pms_category','pms_registry','classification_source','fig_key','fig_key_label']].drop_duplicates('part_number')
bv_pms = bv[(bv['pms_category']!='') | (bv['pms_flag']=='True')][['part_number','pms_category','pms_flag','product_family']].drop_duplicates('part_number')

print("parts_catalog PMS-tagged parts:", len(pc_pms))
print("bvp PMS-tagged parts:", len(bv_pms))

def join_pms(set_df, name):
    pn = set_df['Material'].astype(str).str.strip()
    m1 = set_df.merge(pc_pms, left_on='Material', right_on='part_number', how='left')
    m2 = m1.merge(bv_pms, left_on='Material', right_on='part_number', how='left', suffixes=('_pc','_bv'))
    in_pc = m2['pms_category_pc'].notna()
    in_bv = m2['pms_category_bv'].notna()
    m2['is_pms'] = in_pc | in_bv
    m2['pms_cat'] = m2['pms_category_pc'].fillna(m2['pms_category_bv'])
    print(f"\n===== {name} =====")
    print("n =", len(m2))
    print("PMS via parts_catalog:", int(in_pc.sum()))
    print("PMS via bvp:", int(in_bv.sum()))
    print("PMS via union:", int(m2['is_pms'].sum()))
    print("NOT PMS:", int((~m2['is_pms']).sum()))
    return m2

r250 = join_pms(cheap250, "250 cheap repeat parts")
r80 = join_pms(top80, "80 top flyers")

# list matches
def list_matches(m2, name):
    hits = m2[m2['is_pms']].sort_values('air_bookings', ascending=False)
    print(f"\n===== {name} PMS matches (n={len(hits)}) =====")
    for _, r in hits.iterrows():
        print(f"{r['Material']} | {r['Description']} | {r['pms_cat']} | air {r['air_bookings']}b")

list_matches(r80, "80 top flyers")
list_matches(r250, "250 cheap repeat parts")

# save
r250.to_csv(f"{D}\\_cheap250_pms.csv", index=False)
r80.to_csv(f"{D}\\_top80_pms.csv", index=False)
