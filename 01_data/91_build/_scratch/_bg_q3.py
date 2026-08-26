import pandas as pd, numpy as np, sys
sys.stdout.reconfigure(encoding='utf-8')

SRC = r"c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx"

# Master data
md = pd.read_excel(SRC, sheet_name='Master data', header=0, dtype=str)
print("Master data rows:", len(md))
print("columns:", list(md.columns))
print(md[['P/N','Weight','Length','Width','Height']].head(8).to_string())

def to_float(s):
    if s is None: return np.nan
    s = str(s).strip()
    if s in ('','-','nan','None'): return np.nan
    # comma decimal -> dot
    s = s.replace(',', '.')
    # remove thousand separators (dots used as thousands? unlikely here)
    try:
        return float(s)
    except:
        return np.nan

md['L'] = md['Length'].apply(to_float)
md['W'] = md['Width'].apply(to_float)
md['H'] = md['Height'].apply(to_float)
md['Wt'] = md['Weight'].apply(to_float)

print("\nL/W/H non-null:", md['L'].notna().sum(), md['W'].notna().sum(), md['H'].notna().sum())
print("L range:", md['L'].min(), md['L'].max(), "| W range:", md['W'].min(), md['W'].max(), "| H range:", md['H'].min(), md['H'].max())
print("Weight range:", md['Wt'].min(), md['Wt'].max())

# unit volume = L*W*H (m3)
md['unit_vol'] = md['L'] * md['W'] * md['H']
print("unit volume range:", md['unit_vol'].min(), md['unit_vol'].max())

# Load joined data
df = pd.read_excel(SRC, sheet_name='Data (joined)', header=3, dtype={'Material': str})
df['Material'] = df['Material'].astype(str).str.strip()
df['MoT'] = df['MoT'].astype(str).str.strip()
df['BillT'] = df['BillT'].astype(str).str.strip()

g = df[(df['BillT']=='F2') & (df['Material']!='REBATE')].copy()
air = g[g['MoT']=='Air'].copy()
print("\nair lines:", len(air))

# join master unit_vol via Material -> P/N (and Newest P/N)
md_map = md[['P/N','unit_vol','Wt']].dropna(subset=['P/N'])
md_map = md_map.rename(columns={'P/N':'Material','unit_vol':'md_unit_vol','Wt':'md_unit_wt'})
air2 = air.merge(md_map, on='Material', how='left')

# also try newest P/N
md2 = md[['Newest P/N','unit_vol','Wt']].dropna(subset=['Newest P/N']).rename(columns={'Newest P/N':'Material','unit_vol':'md2_unit_vol','Wt':'md2_unit_wt'})
air2 = air2.merge(md2, on='Material', how='left')

# compute volumetric from master dims: unit_vol * qty * 167
air2['vol_m3_joined'] = air2['Volume (m3)']  # pre-joined volume column
air2['vol_m3_master'] = air2['md_unit_vol'] * air2['Qty']
air2['gross'] = air2['Gross weight (kg)']
air2['volwt_joined'] = air2['vol_m3_joined'] * 167
air2['volwt_master'] = air2['vol_m3_master'] * 167

# chargeable per line
air2['charge_joined'] = air2[['gross','volwt_joined']].max(axis=1)
air2['charge_master'] = air2[['gross','volwt_master']].max(axis=1)

print("\n===== Q3 recompute =====")
print("gross sum (joined gross weight):", round(air2['gross'].sum(),1))
print("volume m3 sum (joined):", round(air2['vol_m3_joined'].sum(),1))
print("volumetric kg (joined vol *167):", round(air2['volwt_joined'].sum(),1))
print("chargeable (max gross/vol, joined):", round(air2['charge_joined'].sum(),1))
print("volumetric kg (MASTER dims):", round(air2['volwt_master'].sum(),1))
print("chargeable (MASTER dims):", round(air2['charge_master'].sum(),1))
print("lines where volwt>gross (joined):", int((air2['volwt_joined']>air2['gross']).sum()), "of", len(air2), f"= {100*(air2['volwt_joined']>air2['gross']).mean():.1f}%")
print("lines where volwt>gross (master):", int((air2['volwt_master']>air2['gross']).sum()), f"= {100*(air2['volwt_master']>air2['gross']).mean():.1f}%")

# how many air lines have missing master dims
print("\nair lines missing master unit_vol:", air2['md_unit_vol'].isna().sum())
print("air lines missing joined volume:", air2['vol_m3_joined'].isna().sum())
print("air lines missing gross:", air2['gross'].isna().sum())

# verify joined volume == master unit vol * qty for a sample
samp = air2.dropna(subset=['md_unit_vol','vol_m3_joined']).head(5)
print("\nsample vol compare (joined vs master L*W*H*qty):")
print(samp[['Material','Qty','vol_m3_joined','vol_m3_master','gross']].to_string(index=False))
