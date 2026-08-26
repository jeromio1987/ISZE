import pandas as pd, numpy as np, sys, json
sys.stdout.reconfigure(encoding='utf-8')

SRC = r"c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx"

df = pd.read_excel(SRC, sheet_name='Data (joined)', header=3, dtype={'Material': str, 'Sold-to pt': str})
print("raw rows", len(df))
print("columns", list(df.columns))

# clean
df['Material'] = df['Material'].astype(str).str.strip()
df['MoT'] = df['MoT'].astype(str).str.strip()
df['Entity'] = df['Entity'].astype(str).str.strip()
df['BillT'] = df['BillT'].astype(str).str.strip()

# filter genuine shipped
g = df[(df['BillT']=='F2') & (df['Material']!='REBATE')].copy()
print("genuine shipped lines (F2, no REBATE):", len(g))

# air/sea masks
air = g[g['MoT']=='Air']
sea = g[g['MoT']=='Sea']
print("air lines:", len(air), "sea lines:", len(sea))

def per_part_stats(sub):
    return sub.groupby('Material').agg(
        bookings=('Bill.Doc.','nunique'),
        qty=('Qty','sum'),
        value=('EUR Amount','sum'),
    ).reset_index()

air_p = per_part_stats(air).rename(columns={'bookings':'air_bookings','qty':'air_qty','value':'air_value'})
sea_p = per_part_stats(sea).rename(columns={'bookings':'sea_bookings','qty':'sea_qty','value':'sea_value'})

m = air_p.merge(sea_p, on='Material', how='outer').fillna(0)
for c in ['air_bookings','sea_bookings','air_qty','sea_qty']:
    m[c] = m[c].astype(int)
m['air_value'] = m['air_value'].round(2)
m['sea_value'] = m['sea_value'].round(2)

# description
desc = g.groupby('Material')['Description'].first().reset_index()
m = m.merge(desc, on='Material', how='left')

# entity per part (air lines)
ent = air.groupby('Material')['Entity'].agg(lambda s: ','.join(sorted(set(s)))).reset_index().rename(columns={'Entity':'air_entities'})
m = m.merge(ent, on='Material', how='left')

# 250 cheap repeat parts: air bookings >=5 AND avg value per air booking < 50
m['avg_per_booking'] = m['air_value'] / m['air_bookings'].replace(0, np.nan)
cheap250 = m[(m['air_bookings']>=5) & (m['avg_per_booking']<50)].copy()
print("\n250 cheap repeat parts (>=5 air bookings, avg<50):", len(cheap250))
print("their total air bookings:", cheap250['air_bookings'].sum(), "air value EUR:", round(cheap250['air_value'].sum(),2))

# 80 top flyers
top80 = m.sort_values('air_bookings', ascending=False).head(80).copy()
print("80 top flyers: min air bookings =", top80['air_bookings'].min())

# verify rank-1 part
r1 = m[m['Material']=='8978808250']
print("\nverify 8978808250:", r1[['Material','air_bookings','sea_bookings','air_qty','air_value']].to_dict('records'))

# top 25 by air bookings with sea
top25 = m.sort_values('air_bookings', ascending=False).head(25).copy()
print("\n===== TOP 25 air parts (air vs sea) =====")
cols = ['Material','Description','air_entities','air_bookings','air_qty','air_value','sea_bookings','sea_qty','sea_value']
for _, r in top25[cols].iterrows():
    verdict = 'SEA-COVERED' if r['sea_bookings']>0 else 'AIR-ONLY'
    print(f"{r['Material']} | {r['Description']} | {r['air_entities']} | air {int(r['air_bookings'])}b {int(r['air_qty'])}q {r['air_value']:.0f}€ | sea {int(r['sea_bookings'])}b {int(r['sea_qty'])}q {r['sea_value']:.0f}€ | {verdict}")

# save m for later scripts
m.to_csv(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_part_stats.csv", index=False)
cheap250.to_csv(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_cheap250.csv", index=False)
top80.to_csv(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_top80.csv", index=False)

# UTI subset of top25
uti25 = top25[top25['air_entities'].astype(str).str.contains('UTI', na=False)]
print("\n===== UTI subset of top 25 =====")
print(len(uti25), "parts have UTI air bookings")
print(uti25[cols].to_string(index=False))
