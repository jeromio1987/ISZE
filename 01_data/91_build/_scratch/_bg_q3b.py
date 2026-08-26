import pandas as pd, numpy as np, sys
sys.stdout.reconfigure(encoding='utf-8')

SRC = r"c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx"

df = pd.read_excel(SRC, sheet_name='Data (joined)', header=3, dtype={'Material': str})
df['Material'] = df['Material'].astype(str).str.strip()
df['MoT'] = df['MoT'].astype(str).str.strip()
df['BillT'] = df['BillT'].astype(str).str.strip()

g = df[(df['BillT']=='F2') & (df['Material']!='REBATE')].copy()
air = g[g['MoT']=='Air'].copy()
print("air lines:", len(air))

gross = pd.to_numeric(air['Gross weight (kg)'], errors='coerce')
vol = pd.to_numeric(air['Volume (m3)'], errors='coerce')

print("gross NaN:", gross.isna().sum(), "vol NaN:", vol.isna().sum())

# drop lines with missing gross/vol (v4 likely excluded them)
mask = gross.notna() & vol.notna()
print("lines with both gross & vol:", mask.sum())

gw = gross[mask]
vv = vol[mask] * 167
chg = np.maximum(gw, vv)

print("\n===== clean recompute (exclude missing) =====")
print("gross kg:", round(gw.sum(),1))
print("volumetric kg (vol*167):", round(vv.sum(),1))
print("chargeable kg (max per line):", round(chg.sum(),1))
print("% vol>gross:", round(100*(vv>gw).mean(),1), f"({int((vv>gw).sum())} of {len(gw)})")

# what if we DON'T exclude missing (treat NaN as 0)?
print("\n===== treat NaN as 0 =====")
gw0 = gross.fillna(0); vv0 = vol.fillna(0)*167; chg0 = np.maximum(gw0, vv0)
print("gross kg:", round(gw0.sum(),1))
print("volumetric kg:", round(vv0.sum(),1))
print("chargeable kg:", round(chg0.sum(),1))

# Also: does v4's gross 44377.6 correspond to something? check booking-level (Orders sheet)
ord_ = pd.read_excel(SRC, sheet_name='Orders', header=3, dtype={'Bill.Doc.': str})
ord_['MoT'] = ord_['MoT'].astype(str).str.strip()
air_o = ord_[ord_['MoT']=='Air']
print("\nOrders sheet Air bookings:", len(air_o), "total weight kg:", round(pd.to_numeric(air_o['Total weight (kg)'], errors='coerce').sum(),1))
