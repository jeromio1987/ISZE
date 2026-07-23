"""
GPS Full Run v2 — Clean from raw SAP files only (no parquet)
Produces: gps_clean_all_fy.csv  (GPS-eligible revenue per DB per FY)
          gps_warranty.csv       (warranty deduction per DB per FY)
          gps_net_fy.csv         (GPS-eligible net of warranty per DB per FY)

FY convention: Apr–Mar (ISZE). FY2024 = Apr 2023–Mar 2024.

DATA SOURCES
  FY2024 (Apr23–Mar24): raw/sales/CY2023-2024.XLSX
  FY2025 (Apr24–Mar25): raw/sales/CY2023-2024.XLSX (Apr–Dec24)
                        + raw/sales/CY2025.XLSX (Jan–Mar25)
  FY2026 (Apr25–Mar26): raw/sales/CY2025.XLSX (Apr–Dec25)
                        + 01_data/sales_2026tillApril.XLSX (Jan–Mar26)

WARRANTY SOURCES
  CV CY2025 (covers repairs Jan25–Oct25, split to FY by REPA6):
    01_data/Warranty_CV_2025.xlsx — MIDI rows in JPY, others in EUR
  LCV FY2026 (Jan–May 2026 assessed):
    01_data/ExportClaimAssessment202601-202605 with EV.xls.xlsx
  GAPS: LCV warranty FY2024/FY2025 not available at DB level.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

_TOOLS = Path(__file__).resolve().parent.parent / "04_tools"
sys.path.insert(0, str(_TOOLS))
from _shared.paths import DATA_ROOT, DERIVED_DIR, RAW_SALES_DIR  # noqa: E402

BASE = _TOOLS.parent
SALES_RAW = RAW_SALES_DIR
DATA = DATA_ROOT
OUT = DERIVED_DIR
OUT.mkdir(exist_ok=True)

# ── FX rate for warranty MIDI (JPY → EUR) ──────────────────────────────────
FX_JPY_EUR = 163.7   # FY2026 confirmed rate

# ── Exclusion helpers ───────────────────────────────────────────────────────
EXCL_BILLT  = {'G2', 'RE', 'S1', 'S2'}
EXCL_SATY   = {'CR', 'ZDR'}
SHELL_PFX   = ('550047', '550070')

SURCHARGE = {
    'SOR': 1.00, 'RUSH': 1.03, 'VOR': 1.07,
    'SVOR': 1.11, 'PRD': 0.97,
}

def is_shell(mat_num):
    s = str(mat_num).strip() if pd.notna(mat_num) else ''
    return s.startswith(SHELL_PFX)

def fy(dt):
    return dt.year + 1 if dt.month >= 4 else dt.year

# ── READER: CY2023-2024.XLSX and sales_2026tillApril.XLSX ──────────────────
# Shared schema: Billing Date | Bill.Doc. | BillT | SOrg. | Payer | Sold-to pt
#                | Payer(=DB name) | Material | Material Number | Billed Qty | SU
#                | Order Qty | SU | Net value | Curr. | Net Price | Curr.
#                | Purchase order no. | SaTy | Doc. Date | Sales Doc.
# Col indices:    0             1        2      3      4      5
#                 6              7        8              9         10
#                 11        12   13           14     15      16
#                 17                18      19          20

def read_std(path, label):
    print(f"Reading {label} ...")
    df = pd.read_excel(path, sheet_name='Sheet1', header=0)
    # rename duplicate columns by position
    cols = list(df.columns)
    seen = {}
    new_cols = []
    for c in cols:
        if c in seen:
            seen[c] += 1
            new_cols.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 0
            new_cols.append(c)
    df.columns = new_cols

    df = df.rename(columns={
        'Billing Date':     'billing_date',
        'BillT':            'billt',
        'Payer':            'payer',
        'Payer_1':          'db_name',
        'Sold-to pt':       'sold_to',
        'Material':         'material_num',
        'Material Number':  'material_desc',
        'Net value':        'net_value',
        'SaTy':             'saty',
    })
    df['billing_date'] = pd.to_datetime(df['billing_date'], errors='coerce')
    df = df.dropna(subset=['billing_date'])
    df['payer']    = pd.to_numeric(df['payer'],    errors='coerce')
    df['sold_to']  = pd.to_numeric(df['sold_to'],  errors='coerce')
    df['net_value']= pd.to_numeric(df['net_value'],errors='coerce').fillna(0)
    df['billt']    = df['billt'].astype(str).str.strip().str.upper()
    df['saty']     = df['saty'].astype(str).str.strip().str.upper()
    df['material_num'] = df['material_num'].astype(str).str.strip()
    print(f"  → {len(df):,} rows, {df['billing_date'].min().date()} – {df['billing_date'].max().date()}")
    return df

# ── READER: CY2025.XLSX (different schema — no BillT, DB column direct) ────
# Billing Date | Sold-to pt | DB | Material | Material Number | Billed Qty | SU
# | Order Qty | SU | Net value | Net price | Purchase order no. | SaTy | Doc.Date | Sales Doc.
# Indices: 0         1        2    3(num)       4(desc)

def read_cy2025(path):
    print(f"Reading CY2025 ...")
    df = pd.read_excel(path, sheet_name='Sheet1', header=0)
    cols = list(df.columns)
    seen = {}
    new_cols = []
    for c in cols:
        if c in seen:
            seen[c] += 1
            new_cols.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 0
            new_cols.append(c)
    df.columns = new_cols

    df = df.rename(columns={
        'Billing Date':     'billing_date',
        'Sold-to pt':       'payer',       # in CY2025, Sold-to pt IS the payer code
        'DB':               'db_name',
        'Material':         'material_num',
        'Material Number':  'material_desc',
        'Net value':        'net_value',
        'SaTy':             'saty',
    })
    df['billing_date'] = pd.to_datetime(df['billing_date'], errors='coerce')
    df = df.dropna(subset=['billing_date'])
    df['payer']      = pd.to_numeric(df['payer'],    errors='coerce')
    df['sold_to']    = df['payer'].copy()   # no separate sold-to in CY2025 schema
    df['net_value']  = pd.to_numeric(df['net_value'],errors='coerce').fillna(0)
    df['billt']      = 'UNKNOWN'            # not present in CY2025 raw
    df['saty']       = df['saty'].astype(str).str.strip().str.upper()
    df['material_num'] = df['material_num'].astype(str).str.strip()
    print(f"  → {len(df):,} rows, {df['billing_date'].min().date()} – {df['billing_date'].max().date()}")
    return df

# ── LOAD ALL FILES ──────────────────────────────────────────────────────────
df_2324 = read_std(SALES_RAW / 'CY2023-2024.XLSX', 'CY2023-2024')
df_2025 = read_cy2025(SALES_RAW / 'CY2025.XLSX')
df_2026 = read_std(DATA / 'sales_2026tillApril.XLSX', 'sales_2026tillApril')

# Combine
df = pd.concat([df_2324, df_2025, df_2026], ignore_index=True)
print(f"\nCombined: {len(df):,} rows")

# ── FY ASSIGNMENT ───────────────────────────────────────────────────────────
df['FY'] = df['billing_date'].apply(fy)
print(f"FY distribution:\n{df['FY'].value_counts().sort_index()}")

# ── UMI / UTI SPLIT ────────────────────────────────────────────────────────
# Payer=1797 (UMI) but Sold-to=1799 → reassign to UTI (1799)
umi_uti_mask = (df['payer'] == 1797) & (df['sold_to'] == 1799)
df.loc[umi_uti_mask, 'payer'] = 1799
df.loc[umi_uti_mask, 'db_name'] = 'UTI (via UMI)'
print(f"\nUMI→UTI reassigned rows: {umi_uti_mask.sum():,}")

# ── DB NAME: fill from payer where CY2025 rows have no name ────────────────
# CY2025 has DB names directly. Cross-reference from other files for any gaps.
payer_name_map = (
    df[df['db_name'].notna() & (df['db_name'] != 'UNKNOWN')]
    .groupby('payer')['db_name']
    .agg(lambda x: x.value_counts().index[0])
    .to_dict()
)
df['db_name'] = df.apply(
    lambda r: payer_name_map.get(r['payer'], r['db_name'])
    if (pd.isna(r['db_name']) or r['db_name'] == 'UNKNOWN') else r['db_name'],
    axis=1
)

# ── EXCLUSION FLAGS ─────────────────────────────────────────────────────────
excl_billt   = df['billt'].isin(EXCL_BILLT)
excl_saty    = df['saty'].isin(EXCL_SATY)
excl_transp  = df['material_num'].str.upper() == 'TRANSPORT'
excl_interest= df['material_num'].str.upper().str.contains('LATE PAYMENT|INTEREST', na=False)
excl_service = df['material_num'].str.upper().str.contains('SERVICE FEE|DEMURRAGE', na=False)
excl_shell   = df['material_num'].apply(is_shell)

any_excl = excl_billt | excl_saty | excl_transp | excl_interest | excl_service | excl_shell

print("\n=== Exclusion waterfall ===")
for fy_val in sorted(df['FY'].unique()):
    m = df['FY'] == fy_val
    gross = df.loc[m, 'net_value'].sum()
    ex_bt = df.loc[m & excl_billt, 'net_value'].sum()
    ex_sy = df.loc[m & ~excl_billt & excl_saty, 'net_value'].sum()
    ex_tr = df.loc[m & ~excl_billt & ~excl_saty & excl_transp, 'net_value'].sum()
    ex_sh = df.loc[m & ~excl_billt & ~excl_saty & ~excl_transp & excl_shell, 'net_value'].sum()
    ex_ot = df.loc[m & (excl_interest | excl_service) & ~excl_billt & ~excl_saty & ~excl_transp & ~excl_shell, 'net_value'].sum()
    net   = df.loc[m & ~any_excl, 'net_value'].sum()
    print(f"FY{fy_val}: Gross={gross:>12,.0f}  BillT={ex_bt:>10,.0f}  SaTy-CR={ex_sy:>10,.0f}  "
          f"Transport={ex_tr:>8,.0f}  Shell={ex_sh:>10,.0f}  Other={ex_ot:>8,.0f}  "
          f"CLEAN={net:>12,.0f}")

clean = df[~any_excl].copy()

# ── SURCHARGE NEUTRALISATION ────────────────────────────────────────────────
factor = clean['saty'].map(SURCHARGE).fillna(1.0)
clean['net_gps'] = clean['net_value'] / factor

print(f"\nSurcharge neutralisation:")
for s in ['RUSH','VOR','SVOR','PRD']:
    m = clean['saty'] == s
    orig = clean.loc[m, 'net_value'].sum()
    neut = clean.loc[m, 'net_gps'].sum()
    if orig > 0:
        print(f"  {s}: orig={orig:>10,.0f}  neutralised={neut:>10,.0f}  delta={neut-orig:>10,.0f}")
clean.loc[clean['saty'].map(SURCHARGE).notna() == False, 'net_gps'] = (
    clean.loc[clean['saty'].map(SURCHARGE).notna() == False, 'net_value']
)

# ── GPS REVENUE PER DB PER FY ───────────────────────────────────────────────
gps_rev = (
    clean.groupby(['FY', 'payer', 'db_name'])['net_gps']
    .sum()
    .reset_index()
    .rename(columns={'net_gps': 'gps_revenue_eur'})
)

# ── WARRANTY DEDUCTION ──────────────────────────────────────────────────────
print("\n=== Building warranty table ===")

# --- CV warranty (Warranty_CV_2025.xlsx) ---
# FY assignment via REPA6 (repair month YYYYMM)
# MIDI rows: CRNCY = 'JPY EUR' → TTL_PARTS in JPY → convert
# Others: TTL_PARTS in EUR
wcv = pd.read_excel(DATA / 'Warranty_CV_2025.xlsx',
                    usecols=['DST_Name', 'REPA6', 'CRNCY', 'TTL_PARTS'])
wcv = wcv.dropna(subset=['REPA6'])
wcv['REPA6']  = wcv['REPA6'].astype(str).str.strip()
wcv['year']   = pd.to_numeric(wcv['REPA6'].str[:4], errors='coerce')
wcv['month']  = pd.to_numeric(wcv['REPA6'].str[4:6], errors='coerce')
wcv['FY']     = wcv.apply(lambda r: int(r['year'])+1 if r['month']>=4 else int(r['year']), axis=1)

# Convert JPY rows to EUR
wcv['eur_parts'] = wcv.apply(
    lambda r: r['TTL_PARTS'] / FX_JPY_EUR if str(r['CRNCY']).startswith('JPY') else r['TTL_PARTS'],
    axis=1
)

warranty_cv = (
    wcv.groupby(['FY', 'DST_Name'])['eur_parts']
    .sum()
    .reset_index()
    .rename(columns={'DST_Name': 'db_warranty_name', 'eur_parts': 'warranty_cv_eur'})
)
print("CV warranty by FY and DB:")
print(warranty_cv.to_string())

# --- LCV warranty (ExportClaimAssessment — FY2026 only) ---
wlcv = pd.read_excel(DATA / 'ExportClaimAssessment202601-202605 with EV.xls.xlsx',
                     usecols=['DistributorName', 'AssessMonth', 'AdmitPartsCost', 'CurrencyParts'])
wlcv = wlcv[wlcv['CurrencyParts'] == 'EUR'].copy()
wlcv['AssessMonth'] = wlcv['AssessMonth'].astype(str).str.strip()
wlcv['year']  = pd.to_numeric(wlcv['AssessMonth'].str[:4], errors='coerce')
wlcv['month'] = pd.to_numeric(wlcv['AssessMonth'].str[4:6], errors='coerce')
wlcv['FY']    = wlcv.apply(lambda r: int(r['year'])+1 if r['month']>=4 else int(r['year']), axis=1)

warranty_lcv = (
    wlcv.groupby(['FY', 'DistributorName'])['AdmitPartsCost']
    .sum()
    .reset_index()
    .rename(columns={'DistributorName': 'db_warranty_name', 'AdmitPartsCost': 'warranty_lcv_eur'})
)
print("\nLCV warranty by FY and DB:")
print(warranty_lcv.to_string())

# ── SAVE INTERMEDIATES ──────────────────────────────────────────────────────
gps_rev.to_csv(OUT / 'gps_clean_all_fy.csv', index=False)
warranty_cv.to_csv(OUT / 'warranty_cv.csv', index=False)
warranty_lcv.to_csv(OUT / 'warranty_lcv.csv', index=False)

print(f"\n✅ Saved gps_clean_all_fy.csv  ({len(gps_rev)} rows)")
print(f"✅ Saved warranty_cv.csv")
print(f"✅ Saved warranty_lcv.csv")
print("\n=== GPS REVENUE SUMMARY PER FY ===")
print(gps_rev.groupby('FY')['gps_revenue_eur'].sum().apply(lambda x: f"€{x:,.0f}"))
