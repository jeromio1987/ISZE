"""
GPS Data Cleaning Audit — Issue 1 & 2
Reads CY2023-2024.XLSX raw SAP extract and produces:
  1. Clean GPS-eligible revenue per DB per year (Issue 1)
  2. UMI / UTI split using Sold-to pt field (Issue 2)
Output: ISZE/01_data/derived/gps_clean_cy2023_2024.csv
"""
import pandas as pd
from pathlib import Path
import sys

_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS))
from _shared.paths import DERIVED_DIR, RAW_SALES_DIR  # noqa: E402

RAW = RAW_SALES_DIR / "CY2023-2024.XLSX"
OUT = DERIVED_DIR / "gps_clean_cy2023_2024.csv"

print(f"Reading {RAW} ...")
df = pd.read_excel(RAW, usecols=[
    'Billing Date','Payer','Sold-to pt','Material','BillT','SaTy','Net value'
])
df['year'] = pd.to_datetime(df['Billing Date']).dt.year
print(f"  Rows: {len(df):,}")

# ── EXCLUSION RULES (same as CY2025 parquet methodology) ──────────────────
excl_transport  = df['Material'] == 'TRANSPORT'
excl_g2         = df['BillT'] == 'G2'      # credit memos (rebates etc.)
excl_re         = df['BillT'] == 'RE'      # returns
excl_interest   = df['Material'].str.contains('LATE PAYMENT|INTEREST', case=False, na=False)
excl_service    = df['Material'].str.contains('SERVICE FEE|DEMURRAGE', case=False, na=False)
# Shell Rimula: material numbers starting with 550047 or 550070
excl_shell      = df['Material'].astype(str).str.match(r'^(550047|550070)')

any_excl = excl_transport | excl_g2 | excl_re | excl_interest | excl_service | excl_shell
clean    = df[~any_excl].copy()

# ── ISSUE 2: UMI / UTI SPLIT ──────────────────────────────────────────────
# When Payer=1797 (UMI) but Sold-to pt=1799 → these are UTI orders
# Re-assign DB based on Sold-to pt
def assign_db(row):
    payer   = int(row['Payer'])    if pd.notna(row['Payer'])      else None
    sold_to = int(row['Sold-to pt']) if pd.notna(row['Sold-to pt']) else None
    # UTI orders routed through UMI payer
    if payer == 1797 and sold_to == 1799:
        return 1799   # assign to UTI
    return payer

clean['db_code'] = clean.apply(assign_db, axis=1)

# ── SUMMARY ───────────────────────────────────────────────────────────────
print("\n=== Exclusion impact ===")
for y in [2023, 2024]:
    gross = df[df.year==y]['Net value'].sum()
    t     = df[(df.year==y) & excl_transport]['Net value'].sum()
    g2    = df[(df.year==y) & excl_g2]['Net value'].sum()
    re    = df[(df.year==y) & excl_re]['Net value'].sum()
    sh    = df[(df.year==y) & excl_shell]['Net value'].sum()
    net   = clean[clean.year==y]['Net value'].sum()
    print(f"CY{y}:")
    print(f"  Gross:     €{gross:>12,.0f}")
    print(f"  Transport: €{t:>12,.0f}")
    print(f"  G2 credit: €{g2:>12,.0f}")
    print(f"  RE return: €{re:>12,.0f}")
    print(f"  Shell lube:€{sh:>12,.0f}")
    print(f"  CLEAN:     €{net:>12,.0f}  ({(gross-net)/gross*100:.1f}% excluded)")

print("\n=== Issue 2: UMI vs UTI (clean revenue) ===")
for y in [2023, 2024]:
    umi = clean[(clean.year==y) & (clean['db_code']==1797)]['Net value'].sum()
    uti = clean[(clean.year==y) & (clean['db_code']==1799)]['Net value'].sum()
    print(f"CY{y}  UMI own: €{umi:,.0f}  |  UTI-via-UMI: €{uti:,.0f}")

# ── EXPORT ────────────────────────────────────────────────────────────────
summary = (
    clean.groupby(['year','db_code'])['Net value']
    .sum()
    .reset_index()
    .rename(columns={'Net value':'clean_gps_eur','db_code':'payer_corrected'})
)
summary.to_csv(OUT, index=False)
print(f"\nSaved: {OUT}")
