import pandas as pd, numpy as np, sys
sys.stdout.reconfigure(encoding='utf-8')

D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX"
m = pd.read_csv(f"{D}\\_part_stats.csv", dtype=str)
for c in ['air_bookings','sea_bookings','air_qty','sea_qty']:
    m[c] = m[c].astype(int)
for c in ['air_value','sea_value']:
    m[c] = m[c].astype(float)

top25 = m.sort_values('air_bookings', ascending=False).head(25)
top25['verdict'] = np.where(top25['sea_bookings']==0, 'AIR-ONLY (no sea history)',
                   np.where(top25['sea_qty']>=top25['air_qty'], 'sea-covered (sea qty >= air qty)',
                            'sea exists but sea qty < air qty'))

print("verdict counts in top 25:")
print(top25['verdict'].value_counts())

print("\n===== TOP 25 clean table =====")
cols = ['Material','Description','air_entities','air_bookings','air_qty','air_value','sea_bookings','sea_qty','sea_value','verdict']
for _, r in top25.iterrows():
    print(f"{r['Material']} | {r['Description']} | {r['air_entities']} | air {r['air_bookings']}b/{r['air_qty']}q/{r['air_value']:.0f}€ | sea {r['sea_bookings']}b/{r['sea_qty']}q/{r['sea_value']:.0f}€ | {r['verdict']}")

# overall study-wide: how many parts have both air & sea
both = (m['air_bookings']>0) & (m['sea_bookings']>0)
air_only = (m['air_bookings']>0) & (m['sea_bookings']==0)
print(f"\nstudy-wide: parts with BOTH air&sea = {both.sum()}, air-only = {air_only.sum()}, total air-shipped parts = {(m['air_bookings']>0).sum()}")

# total air value & qty for the top25 vs all
print("\ntop25 air qty total:", top25['air_qty'].sum(), "value:", round(top25['air_value'].sum(),0))
print("all air qty total:", m[m['air_bookings']>0]['air_qty'].sum())
