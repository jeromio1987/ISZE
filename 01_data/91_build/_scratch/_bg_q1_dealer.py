import pandas as pd, numpy as np, sys, os, glob, re
sys.stdout.reconfigure(encoding='utf-8')

D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\12_raw\dealer_sales\UTI"
files = sorted(glob.glob(os.path.join(D, "UTIPartSales_*.xlsx")))
print("files found:", len(files))

def month_from_name(fn):
    mm = re.search(r'UTIPartSales_(\d{4})-(\d{2})', os.path.basename(fn))
    return f"{mm.group(1)}-{mm.group(2)}"

frames = []
for f in files:
    df = pd.read_excel(f, sheet_name='UTIPartSales', header=5, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    # expected cols: 'Item Code', 'qty Month', 'qty Year TYD'
    df = df[df['Item Code'].notna()]
    df = df[df['Item Code'].astype(str).str.strip()!='']
    df['Item Code'] = df['Item Code'].astype(str).str.strip()
    qty = pd.to_numeric(df['qty Month'], errors='coerce').fillna(0)
    df['qty'] = qty
    df['month'] = month_from_name(f)
    frames.append(df[['Item Code','month','qty']])

all_sales = pd.concat(frames, ignore_index=True)
print("total sellout rows:", len(all_sales), "distinct items:", all_sales['Item Code'].nunique())
print("months covered:", sorted(all_sales['month'].unique()))

# UTI parts to inspect
uti_parts = [
    ('8972629330','RELAY; HTR & A/C'),
    ('8943967110','BOLT; EYE,WATER PIPE'),
    ('8984883520','HOSE; ATF'),
    ('8978715611','COVER; RADAR'),
    ('8973709860','SEAL; TIP,INJECTOR'),
]

# also a few more UTI repeat parts (from broader top list) for demand examples
extra = [
    ('8980377572','HOSE; FLEX,RR DISC'),
    ('7552360050','SWITCH; PTO'),
    ('7552887860','METER COMPL; CLUSTER'),
]

print("\n===== UTI part demand curve (dealer sellout, units/month) =====")
for pn, desc in uti_parts + extra:
    s = all_sales[all_sales['Item Code']==pn]
    total = s['qty'].sum()
    months_nz = (s['qty']>0).sum()
    # coefficient of variation of monthly (over months present)
    if len(s)>0:
        cv = s['qty'].std()/s['qty'].mean() if s['qty'].mean()>0 else np.nan
    else:
        cv = np.nan
    series = s.sort_values('month')['qty'].tolist()
    months = s.sort_values('month')['month'].tolist()
    present = 'YES' if len(s)>0 else 'no dealer data'
    print(f"\n{pn} | {desc} | dealer data: {present} | total {total:.0f} units | {months_nz} months w/ sales | CV={cv:.2f}")
    if len(s)>0:
        print("   ", dict(zip(months, [int(x) for x in series])))
