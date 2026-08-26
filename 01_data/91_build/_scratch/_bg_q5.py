import pandas as pd, numpy as np, sys
sys.stdout.reconfigure(encoding='utf-8')

D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX"
BO = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\08_Distributor\BO OVERVIEW - UNIVERSAL TRUCKS ISRAEL LTD 01-07-2026 (1).xlsx"

bo = pd.read_excel(BO, sheet_name='DATA', header=3, dtype=str)
bo.columns = [str(c).strip() for c in bo.columns]
print("BO columns:", list(bo.columns))
print("BO rows:", len(bo))

# identify key cols
mat_col = [c for c in bo.columns if 'Material' in c][0]
desc_col = [c for c in bo.columns if 'description' in c.lower()][0]
oq_col = [c for c in bo.columns if c.strip().startswith('Open')][0]
print("using cols:", mat_col, desc_col, oq_col)

bo['Material'] = bo[mat_col].astype(str).str.strip()
bo['Open Qty'] = pd.to_numeric(bo[oq_col], errors='coerce').fillna(0)
bo = bo[bo['Material']!='nan']
bo = bo[bo['Material']!='']

open_bo = bo[bo['Open Qty'] > 0].copy()
print("\nopen BO rows:", len(open_bo), "distinct materials:", open_bo['Material'].nunique())
print("total open qty:", open_bo['Open Qty'].sum())

# join to 250 cheap parts
cheap250 = pd.read_csv(f"{D}\\_cheap250.csv", dtype=str)
m = pd.read_csv(f"{D}\\_part_stats.csv", dtype=str)
m['air_bookings'] = m['air_bookings'].astype(int)
m['sea_bookings'] = m['sea_bookings'].astype(int)

join = open_bo.merge(cheap250[['Material','Description','air_bookings','avg_per_booking']], on='Material', how='inner')
print("\n===== Q5: cheap/repeat parts with OPEN backorder =====")
print("distinct parts:", join['Material'].nunique(), "| lines:", len(join), "| open qty:", join['Open Qty'].sum())

# per part aggregate
agg = join.groupby('Material').agg(
    desc=('Description','first'),
    bo_lines=('Material','size'),
    open_qty=('Open Qty','sum'),
    air_bookings=('air_bookings','first'),
).reset_index()
agg = agg.merge(m[['Material','sea_bookings']], on='Material', how='left')
agg = agg.sort_values('air_bookings', ascending=False)
for _, r in agg.iterrows():
    print(f"{r['Material']} | {r['desc']} | BO {int(r['bo_lines'])} lines / {int(r['open_qty'])} open qty | air {int(r['air_bookings'])}b | sea {int(r['sea_bookings'])}b")

# Q4 part 2: PMS parts on backorder
# PMS parts = 9 from 250 + 5 from 80 (union)
r250 = pd.read_csv(f"{D}\\_cheap250_pms.csv", dtype=str)
r80 = pd.read_csv(f"{D}\\_top80_pms.csv", dtype=str)
# recompute is_pms consistently
pms250 = r250[r250['is_pms'].astype(str)=='True'][['Material','Description','pms_cat','air_bookings']]
pms80 = r80[r80['is_pms'].astype(str)=='True'][['Material','Description','pms_cat','air_bookings']]
pms_all = pd.concat([pms250, pms80]).drop_duplicates('Material')
print("\n===== Q4 part 2: PMS parts (union of 250+80) =====")
print("distinct PMS parts:", len(pms_all))
pms_bo = pms_all.merge(open_bo[['Material','Open Qty','SaTy']], on='Material', how='inner')
print("PMS parts on open backorder:", pms_bo['Material'].nunique())
print(pms_bo.to_string(index=False))

# also: ALL study PMS parts on backorder? The question says "for the PMS-tagged parts" - the 9+5 set.
# also list all 9 PMS of 250 and 5 of 80 with backorder status
print("\nPMS parts (250 set) + BO status:")
pms250_bo = pms250.merge(open_bo[['Material','Open Qty']].groupby('Material').sum().reset_index().rename(columns={'Open Qty':'BO_open_qty'}), on='Material', how='left')
print(pms250_bo.to_string(index=False))
print("\nPMS parts (80 set) + BO status:")
pms80_bo = pms80.merge(open_bo[['Material','Open Qty']].groupby('Material').sum().reset_index().rename(columns={'Open Qty':'BO_open_qty'}), on='Material', how='left')
print(pms80_bo.to_string(index=False))
