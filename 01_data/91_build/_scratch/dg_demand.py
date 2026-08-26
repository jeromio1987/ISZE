import sys, io, os, glob, csv
import pandas as pd
import openpyxl
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

P = r'c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx'
BASE = r'C:\Users\jerom\Desktop\claude\ISZE\01_data'

# ---------- DG universe ----------
dg = pd.read_excel(P, sheet_name='DG list (deduped)', header=3)
dg.columns = [str(c).strip() for c in dg.columns]
def norm(x):
    if x is None: return None
    s = str(x).strip()
    return s.zfill(10)
dg['_mat'] = dg['Material'].map(norm)
dg['_new'] = dg['Newest material no.'].map(norm)
dg_319 = set(dg['_mat'])
dg_union = set(dg['_mat']) | set(dg['_new'])

def fam(desc):
    x = str(desc).upper()
    if 'AIR BAG' in x or 'AIRBAG' in x: return 'Airbag'
    if 'BELT' in x: return 'Seatbelt pretensioner'
    if 'CONTROL UNIT' in x or 'SRS' in x: return 'SRS control unit'
    if any(k in x for k in ['OIL','LUB','FLUID','CLEAN','ATF','GREASE','DEF','ADBLUE','BATTERY']): return 'Bulk lubricant'
    return 'Other'
dg['_fam'] = dg['Description'].map(fam)

results = {}

def report(db, pn_qty, period, note=''):
    pn_qty = {norm(k): v for k, v in pn_qty.items() if norm(k)}
    total_pn = len(pn_qty)
    total_qty = sum(pn_qty.values())
    dg_hit_319 = {p: q for p, q in pn_qty.items() if p in dg_319}
    dg_hit_union = {p: q for p, q in pn_qty.items() if p in dg_union}
    # family of matched DG parts
    fammap = dict(zip(dg['_mat'], dg['_fam'])) | dict(zip(dg['_new'], dg['_fam']))
    fam_cnt = {}
    for p, q in dg_hit_union.items():
        f = fammap.get(p, '?')
        fam_cnt[f] = fam_cnt.get(f, 0) + q
    results[db] = dict(
        total_pn=total_pn, total_qty=round(total_qty,1),
        dg_pn_319=len(dg_hit_319), dg_qty_319=round(sum(dg_hit_319.values()),1),
        dg_pn_union=len(dg_hit_union), dg_qty_union=round(sum(dg_hit_union.values()),1),
        period=period, fam_qty=fam_cnt, note=note,
        dg_parts=sorted(dg_hit_union.keys()),
    )

# ---------- IUK ----------
for yr in ['CY2025','CY2026YTD']:
    f = os.path.join(BASE, '00_derived', f'dealer_sellout_long_IUK_{yr}.csv')
    df = pd.read_csv(f, dtype={'part_number':str})
    # use year-level (period_grain=='year') rows to avoid double counting month+year rows
    agg = df.groupby('part_number')['qty'].sum().to_dict()
    report('IUK_'+yr, agg, yr)

# ---------- IRELAND ----------
for yr in ['CY2025','CY2026YTD']:
    f = os.path.join(BASE, '00_derived', f'dealer_sellout_long_IRELAND_{yr}.csv')
    df = pd.read_csv(f, dtype={'part_number':str})
    agg = df.groupby('part_number')['qty'].sum().to_dict()
    report('IRELAND_'+yr, agg, yr)

# ---------- GREECE ----------
f = r'C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\Data\00_derived\dealer_sellout_long_GREECE_CY2025.csv'
df = pd.read_csv(f, dtype={'part_number':str})
agg = df.groupby('part_number')['qty'].sum().to_dict()
report('GREECE_CY2025', agg, 'CY2025')

# ---------- ITUK (raw) ----------
f = r'C:\Users\jerom\Desktop\claude\ISZE\01_data\12_raw\dealer_sales\ITUK\Sales to Dealers_ITUK_CY2025.xlsx'
wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
ws = wb['Sheet1']
agg = {}
hdr_seen = False
for i, r in enumerate(ws.iter_rows(values_only=True)):
    if i < 5: continue
    item = r[1]
    if item is None: continue
    s = str(item).strip()
    pn = s.split(' - ')[0].split(' ')[0].strip()
    if pn == 'Item Number' or not pn.isdigit(): continue
    qty = 0
    for c in r[3:15]:
        if c is not None:
            try: qty += float(c)
            except: pass
    agg[pn] = agg.get(pn, 0) + qty
report('ITUK_CY2025', agg, 'CY2025')

# ---------- UTI (raw monthly) ----------
utidir = r'C:\Users\jerom\Desktop\claude\ISZE\01_data\12_raw\dealer_sales\UTI'
all_pn = set()
ytd2025 = {}
ytd2026 = {}
for fn in sorted(os.listdir(utidir)):
    if not fn.endswith('.xlsx'): continue
    fp = os.path.join(utidir, fn)
    wb = openpyxl.load_workbook(fp, read_only=True, data_only=True)
    ws = wb['UTIPartSales']
    for i, r in enumerate(ws.iter_rows(values_only=True)):
        if i < 6: continue
        if not r or len(r) == 0: continue
        pn = r[0]
        if pn is None: continue
        pn = norm(pn)
        if not pn or not pn.isdigit(): continue
        all_pn.add(pn)
        qm = r[1] if len(r) > 1 and r[1] is not None else 0
        qy = r[2] if len(r) > 2 and r[2] is not None else 0
        if '2025-12' in fn:
            ytd2025[pn] = qy
        if '2026-06' in fn:
            ytd2026[pn] = qy
report('UTI_CY2025', ytd2025, 'CY2025 (YTD snapshot)')
report('UTI_CY2026YTD', ytd2026, '2026 Jan-Jun YTD')
# distinct coverage note
print("UTI distinct PNs across all monthly files:", len(all_pn))

# ---------- OUTPUT ----------
print("\n========== PER-DB DG DEMAND ==========")
cols = ['distributor','total_pn','total_qty','dg_pn_319','dg_qty_319','dg_pn_union','dg_qty_union','period','fam_qty']
for db, r in results.items():
    fams = ', '.join(f"{k}={int(v)}" for k,v in sorted(r['fam_qty'].items(), key=lambda x:-x[1]))
    print(f"\n{db} | period={r['period']}")
    print(f"  total distinct PNs={r['total_pn']}  total qty={r['total_qty']}")
    print(f"  DG PNs (319-list match)={r['dg_pn_319']}  DG qty={r['dg_qty_319']}")
    print(f"  DG PNs (incl supersession, 337)={r['dg_pn_union']}  DG qty={r['dg_qty_union']}")
    print(f"  DG family qty: {fams}")
