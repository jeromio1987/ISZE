"""
build_isuzu_uio.py
══════════════════════════════════════════════════════════════════════════════
ISUZU UIO Overview – standalone build script
Place this script in the same folder as the four source files and run:

    python build_isuzu_uio.py

Required packages:
    pip install pandas openpyxl matplotlib xlrd

Source files expected in the same folder:
    • IML calculation.xlsx
    • UIO.xlsx
    • LCV UIO (November 2025)_EU_Study_Imit.xlsx
    • ISZE CV_FY2025-FY2030_mid-term plan & 12RS.xlsx

Outputs (saved in same folder):
    • ISUZU_UIO_Overview_2026.xlsx   – full UIO data table (84 rows × 41 years)
    • ISUZU_UIO_Dashboard_2026.xlsx  – dashboard with KPI strip + 4 charts
    • ISUZU_UIO_Dashboard_2026.html  – interactive HTML dashboard (Chart.js)
══════════════════════════════════════════════════════════════════════════════

⚠ ⚠ ⚠  DO NOT RUN WITHOUT READING THIS  ⚠ ⚠ ⚠
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This script was last updated: 2026-04-12.
Canonical workbook is now: ISUZU_UIO_Overview_2026_v18.xlsx (Jun 2026)

v18 contains TWO manual patches that this script does NOT reproduce:

  1. 90% override fix
     Unknown cells — check 'Changelog' sheet in v18 workbook before touching.

  2. Sheet 1 → Sheet 4 live links
     Sheet '1.UIO Overview', rows 22 + 24 (U KING), cols 2025–2030 are
     live-linked to Sheet '4. ITUK UIO Projection' Section C.
     The script writes static values here — the links would be lost.

Running this script as-is will produce an UNPATCHED workbook and overwrite
the HTML dashboard. The v18 patches will be silently lost.

TO USE THIS SCRIPT SAFELY:
  • Open ISUZU_UIO_Overview_2026_v18.xlsx, go to 'Changelog' sheet
  • Document the 90% override fix (cells + values)
  • Add post-build patch code below to re-apply both fixes
  • Then pass --force flag:   python build_isuzu_uio.py --force

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import sys
if "--force" not in sys.argv:
    raise SystemExit(
        "\n⚠  build_isuzu_uio.py is out of sync with v18 patches.\n"
        "   Read the warning in this script's docstring, embed the patches,\n"
        "   then re-run with:  python build_isuzu_uio.py --force\n"
    )

import os, io, json, warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import openpyxl
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as XLImage

warnings.filterwarnings('ignore')

# ── Base path: folder where this script lives ─────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__)) + os.sep

print("=" * 60)
print("ISUZU UIO Build Script")
print(f"Working folder: {BASE}")
print("=" * 60)

# ════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ════════════════════════════════════════════════════════════════════════════
ALL_YEARS   = list(range(1990, 2031))
HIST_YEARS  = list(range(1990, 2027))
FORE_YEARS  = list(range(2027, 2031))

# CV Advanced Economy survival rates (IML, 16-year window)
SURV_CV = {1:1.00,2:0.99,3:0.98,4:0.97,5:0.96,6:0.95,7:0.90,
           8:0.80,9:0.70,10:0.55,11:0.40,12:0.30,13:0.20,14:0.10,
           15:0.05,16:0.00}

# LCV / IMIT survival rates (12-year window)
SURV_LCV = {1:1.00,2:0.98,3:0.95,4:0.92,5:0.89,6:0.84,7:0.80,
            8:0.65,9:0.50,10:0.40,11:0.20,12:0.00}

def surv_cv(age):
    return SURV_CV.get(age, 0.0) if age >= 1 else 0.0

def calc_uio(sales_dict, years, surv_fn=surv_cv):
    """Compute UIO for each year given annual sales dict and survival function."""
    uio = {}
    for t in years:
        total = sum(sales_dict.get(s, 0) * surv_fn(t - s + 1)
                    for s in range(1990, t + 1))
        uio[t] = total
    return uio

DECAY = 0.97   # net annual fleet decay used for CV UIO roll-forward forecasts

# ════════════════════════════════════════════════════════════════════════════
# STEP 1 – IML BACKBONE
# Load ISZE + MIDI rows, model types MD / LD / LCV, 1990–2026
# ════════════════════════════════════════════════════════════════════════════
print("\n[1/8] Loading IML backbone...")

df_iml_raw = pd.read_excel(BASE + "IML calculation.xlsx", sheet_name="1.UIO", header=None)
hr = df_iml_raw.iloc[5, :]
ylbls = [str(int(float(v))) if str(v) not in
         ['nan', '国コード', '国名', 'CV/LCV', '種類', 'ASC/DB'] else v
         for v in hr[5:]]
df_iml = df_iml_raw.iloc[6:].copy()
df_iml.columns = ['ctry_code', 'country', 'cv_lcv', 'model_type', 'asc_db'] + ylbls

df_base = df_iml[
    df_iml['asc_db'].isin(['ISZE', 'MIDI']) &
    df_iml['model_type'].isin(['MD', 'LD', 'LCV'])
].copy().reset_index(drop=True)

for y in [str(yr) for yr in range(1990, 2027)]:
    df_base[y] = pd.to_numeric(df_base[y], errors='coerce').fillna(0)
for y in range(2027, 2031):
    df_base[str(y)] = 0.0

print(f"    IML base: {len(df_base)} rows")

# ════════════════════════════════════════════════════════════════════════════
# STEP 2 – ITUK: UK CV ACTUAL CAR PARK
# The ITUK sheet is a car-park snapshot (vehicles currently in service,
# grouped by registration year). Summing all cohorts gives 2024 car park.
# We use survival rates to reconstruct historical series, then SCALE to
# anchor 2024 to the actual car park total.
# ════════════════════════════════════════════════════════════════════════════
print("[2/8] Processing ITUK (UK actual car park)...")

df_ituk_raw = pd.read_excel(BASE + "UIO.xlsx", sheet_name="ITUK", header=None)
ituk_cols = (['model', 'pre2008'] + [str(y) for y in range(2008, 2025)] + ['total'])
df_ituk = df_ituk_raw.iloc[1:].copy()
df_ituk.columns = ituk_cols[:len(df_ituk.columns)]
df_ituk = df_ituk[df_ituk['model'].notna() &
                  (df_ituk['model'] != 'Grand Total') &
                  (df_ituk['model'] != 'Row Labels')].reset_index(drop=True)
for c in ituk_cols[1:]:
    if c in df_ituk.columns:
        df_ituk[c] = pd.to_numeric(df_ituk[c], errors='coerce').fillna(0)

# Identify N-series vs F-series
df_ituk['series'] = df_ituk['model'].apply(
    lambda m: 'F' if str(m).startswith('F') else 'N')

# Actual 2024 car park (Sum of Total column)
actual_N_2024 = int(df_ituk[df_ituk['series'] == 'N']['total'].sum())
actual_F_2024 = int(df_ituk[df_ituk['series'] == 'F']['total'].sum())
print(f"    UK N-series car park 2024: {actual_N_2024:,}")
print(f"    UK F-series car park 2024: {actual_F_2024:,}")

# Build annual registration approximation from cohort data
# (recent years ≈ 100% survival, so cohort count ≈ original registrations)
def ituk_annual_from_cohorts(series_filter):
    rows = df_ituk[df_ituk['series'] == series_filter]
    annual = {}
    # pre2008 → assign as single lump to year 2007
    annual[2007] = rows['pre2008'].sum()
    for yr in range(2008, 2025):
        annual[yr] = rows[str(yr)].sum()
    for yr in range(1990, 2007):
        annual[yr] = 0
    return annual

n_annual = ituk_annual_from_cohorts('N')
f_annual = ituk_annual_from_cohorts('F')

# Forecast 2025-2030: average of last 3 full years
for src in [n_annual, f_annual]:
    avg = np.mean([src.get(y, 0) for y in range(2022, 2025)])
    for yr in range(2025, 2031):
        src[yr] = avg

# Compute survival-rate UIO
n_uio = calc_uio(n_annual, ALL_YEARS)
f_uio = calc_uio(f_annual, ALL_YEARS)

# Scale to actual 2024 car park
scale_N = actual_N_2024 / n_uio[2024] if n_uio[2024] > 0 else 1.0
scale_F = actual_F_2024 / f_uio[2024] if f_uio[2024] > 0 else 1.0
print(f"    N-series scale factor: {scale_N:.4f}")
print(f"    F-series scale factor: {scale_F:.4f}")

n_uio = {yr: round(v * scale_N) for yr, v in n_uio.items()}
f_uio = {yr: round(v * scale_F) for yr, v in f_uio.items()}

# Apply UK LD (N-series): use IML for 1990-2009, ITUK-scaled for 2010-2030
uk_ld_mask = (df_base['country'] == 'U KING') & (df_base['model_type'] == 'LD')
for yr in range(2010, 2031):
    df_base.loc[uk_ld_mask, str(yr)] = n_uio[yr]

# UK MD → 0 (all N-series = LD per user assumption)
uk_md_mask = (df_base['country'] == 'U KING') & (df_base['model_type'] == 'MD')
for yr in ALL_YEARS:
    df_base.loc[uk_md_mask, str(yr)] = 0

# Add UK F-Series row
f_row = {'ctry_code': '205', 'country': 'U KING', 'cv_lcv': 'CV',
         'model_type': 'F-Series', 'asc_db': 'ISZE'}
for yr in ALL_YEARS:
    f_row[str(yr)] = f_uio[yr]
df_base = pd.concat([df_base, pd.DataFrame([f_row])], ignore_index=True)
print(f"    After ITUK: {len(df_base)} rows")

# ════════════════════════════════════════════════════════════════════════════
# STEP 3 – UTI: ISRAEL
# The UTI sheet in UIO.xlsx contains ANNUAL SALES (registrations), not
# accumulated UIO/fleet figures. IML calculation.xlsx already carries the
# correct accumulated UIO for Israel (survival-rate convolution on all
# historical cohorts), so we use IML directly.
# For 2027-2030, the trend CAGR in Step 6 extrapolates from IML's own trend.
# ════════════════════════════════════════════════════════════════════════════
print("[3/8] Israel: using IML accumulated UIO (UTI sheet = annual sales, not fleet)...")

# ════════════════════════════════════════════════════════════════════════════
# STEP 4 – LCV FORECAST 2025-2030 (growth rates from LCV UIO file)
# ════════════════════════════════════════════════════════════════════════════
print("[4/8] Applying LCV forecast...")

df_lcv_raw = pd.read_excel(
    BASE + "LCV UIO (November 2025)_EU_Study_Imit.xlsx",
    sheet_name="ISZE", header=None)
df_lcv = df_lcv_raw.iloc[25:47, :11].copy()
df_lcv.columns = ['entity', 'CY2019', 'CY2020', 'CY2021', 'CY2022', 'CY2023',
                  'CY2024', 'CY2025E', 'CY2026E', 'CY2027E', 'CY2028E']
df_lcv = df_lcv[df_lcv['entity'].notna()].copy()
for c in df_lcv.columns[1:]:
    df_lcv[c] = pd.to_numeric(df_lcv[c], errors='coerce').fillna(0)

# IBX Belgium = Belgium + Netherlands + Poland (user confirmed)
ENTITY_COUNTRIES = {
    'IUK UK':                        ['U KING'],
    'ISD Germany':                   ['GERMANY'],
    'IBX Belgium':                   ['BELGIUM', 'NETHLDS', 'POLAND'],
    'ISUZU Sweden':                  ['SWEDEN'],
    'RSA Norway':                    ['NORWAY'],
    'IMOTORS Portugal':              ['PORTUGL', 'AZORS'],
    'PETROS Greece':                 ['GREECE'],
    'WAE Kft Hungary':               ['HUNGARY'],
    'LOUTSIOS A & SONS LTD Cyprus':  ['CYPRUS'],
    'ISUZU Ireland':                 ['IRELAND'],
    'ISUZU Rus Russia':              ['RUSSIA'],
    'ISUZU ROM AUTO SRL  Romania':   ['ROMANIA'],
    'ISUZU Finland':                 ['FINLAND'],
    'ISUZU Denmark':                 ['DENMARK'],
    'GASANZAMMIT MOTORS Malta':      ['MALTA'],
    'BL. Ehf. Iceland':              ['ICELAND'],
}

def apply_lcv_forecast(entity_name, countries):
    lr = df_lcv[df_lcv['entity'].astype(str).str.strip() == entity_name.strip()]
    if lr.empty:
        return
    lr = lr.iloc[0]
    base_2024 = lr['CY2024']
    if base_2024 == 0:
        return
    gr = {yr: lr[f'CY{yr}E'] / base_2024 for yr in [2025, 2026, 2027, 2028]}
    ann_2829 = gr[2028] / gr[2027] if gr.get(2027, 0) > 0 else 1.0
    gr[2029] = gr[2028] * ann_2829
    gr[2030] = gr[2029] * ann_2829
    for country in countries:
        mask = (df_base['country'] == country) & (df_base['model_type'] == 'LCV')
        if mask.sum() == 0:
            continue
        iml_2024 = df_base.loc[mask, '2024'].values[0]
        if iml_2024 == 0:
            continue
        for yr in range(2025, 2031):
            df_base.loc[mask, str(yr)] = round(iml_2024 * gr[yr])

for entity, countries in ENTITY_COUNTRIES.items():
    apply_lcv_forecast(entity, countries)

# ════════════════════════════════════════════════════════════════════════════
# STEP 5 – SCRAP-ADJUSTED CAR PARK 2025
# UIO.xlsx → "CV customers with scrap logic" sheet, column O
# Countries: BE, CY, DE, DK, GR, IE, MT, PT
# Methodology: scale survival-rate historical series so 2025 = scrap adj value
# ════════════════════════════════════════════════════════════════════════════
print("[5/8] Applying scrap-adjusted car park corrections...")

df_scrap_raw = pd.read_excel(
    BASE + "UIO.xlsx", sheet_name="CV customers with scrap logic", header=None)

# Parse: row labels in col 0, registration years in cols 1-12 (2014-2024+2025?),
# col 13 = Grand Total, col 14 = Scrap Adj Car Park 2025
SCRAP_COL = 14   # "Scrap Adj Car Park 2025"
REG_YEARS = list(range(2014, 2025))  # cols 1-11 are 2014-2024
CTRY_CODES = {
    'BE': 'BELGIUM', 'CY': 'CYPRUS', 'DE': 'GERMANY',
    'DK': 'DENMARK', 'GR': 'GREECE', 'IE': 'IRELAND',
    'MT': 'MALTA',   'PT': 'PORTUGL'
}
N_SERIES = {'NLR85', 'NLR87', 'NLR88', 'NMR85', 'NMR88',
            'NNR85', 'NNR87', 'NNR88', 'NPR75', 'NPR85'}
F_SERIES = {'FRR90', 'FSR90'}

# Build annual registration data per country per series
scrap_registrations = {}   # {country: {'N': {year: count}, 'F': {year: count}}}
scrap_adj_2025      = {}   # {country: {'N': value, 'F': value}}

current_country = None
for _, row in df_scrap_raw.iterrows():
    label = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
    if label in CTRY_CODES:
        current_country = CTRY_CODES[label]
        if current_country not in scrap_registrations:
            scrap_registrations[current_country] = {
                'N': {yr: 0 for yr in REG_YEARS},
                'F': {yr: 0 for yr in REG_YEARS}
            }
            scrap_adj_2025[current_country] = {'N': 0.0, 'F': 0.0}
    elif current_country and label in N_SERIES | F_SERIES:
        series = 'N' if label in N_SERIES else 'F'
        # Registration counts by year (cols 1 onward = 2014, 2015, ...)
        for i, yr in enumerate(REG_YEARS, start=1):
            val = pd.to_numeric(row.iloc[i], errors='coerce')
            if pd.notna(val):
                scrap_registrations[current_country][series][yr] = \
                    scrap_registrations[current_country][series].get(yr, 0) + val
        # Scrap adj value (col 14)
        adj_val = pd.to_numeric(row.iloc[SCRAP_COL], errors='coerce')
        if pd.notna(adj_val):
            scrap_adj_2025[current_country][series] += adj_val

# Compute survival-rate UIO 2014-2026 from registration data,
# then scale to anchor 2025 = scrap_adj value
SCALE_YEARS = list(range(2014, 2027))
scaled_uio = {}   # {country: {'N': {year: value}, 'F': {year: value}}}

for country, series_data in scrap_registrations.items():
    scaled_uio[country] = {}
    for stype, reg_by_yr in series_data.items():
        target_2025 = scrap_adj_2025[country][stype]
        if target_2025 == 0:
            scaled_uio[country][stype] = {yr: 0.0 for yr in SCALE_YEARS}
            continue
        # Full registration dict for calc_uio (zeros outside 2014-2024)
        full_regs = {yr: reg_by_yr.get(yr, 0) for yr in range(1990, 2031)}
        raw_uio = calc_uio(full_regs, SCALE_YEARS)
        base_2025 = raw_uio.get(2025, 0)
        factor = (target_2025 / base_2025) if base_2025 > 0 else 1.0
        scaled_uio[country][stype] = {
            yr: round(v * factor) for yr, v in raw_uio.items()
        }

# Apply to df_base
SCRAP_COUNTRIES = list(CTRY_CODES.values())

for country in SCRAP_COUNTRIES:
    # LD: replace 2014-2025 with scaled N-series values
    ld_mask = (df_base['country'] == country) & (df_base['model_type'] == 'LD')
    if ld_mask.sum():
        for yr in SCALE_YEARS:
            df_base.loc[ld_mask, str(yr)] = scaled_uio[country]['N'].get(yr, 0)
    # MD: set to 0 (all trucks are N-series = LD per assumption)
    md_mask = (df_base['country'] == country) & (df_base['model_type'] == 'MD')
    for yr in ALL_YEARS:
        df_base.loc[md_mask, str(yr)] = 0

# Add F-Series rows for Ireland and Portugal
F_COUNTRIES = {'IRELAND': '206', 'PORTUGL': '217'}
for country, code in F_COUNTRIES.items():
    existing = df_base[(df_base['country'] == country) &
                       (df_base['model_type'] == 'F-Series')]
    if len(existing) == 0:
        row_data = {'ctry_code': code, 'country': country, 'cv_lcv': 'CV',
                    'model_type': 'F-Series', 'asc_db': 'ISZE'}
        for yr in ALL_YEARS:
            row_data[str(yr)] = scaled_uio[country]['F'].get(yr, 0)
        df_base = pd.concat([df_base, pd.DataFrame([row_data])],
                            ignore_index=True)

print(f"    After scrap corrections: {len(df_base)} rows")

# ════════════════════════════════════════════════════════════════════════════
# STEP 6 – CV FORECAST 2026-2030
# Parse ISZE CV plan → apply UIO roll-forward for 8 countries from 2025 base
# Trend CAGR for all other countries (2027-2030)
# ════════════════════════════════════════════════════════════════════════════
print("[6/8] Applying CV forecast (2026-2030)...")

df_cv_raw = pd.read_excel(
    BASE + "ISZE CV_FY2025-FY2030_mid-term plan & 12RS.xlsx",
    sheet_name="mid-term plan to FY30 (Nov25)", header=None)

CUST_COUNTRY = {
    '3595_PETROS PETROPOULOS':   'GREECE',
    '3594_LOUTSIOS & SONS LTD.': 'CYPRUS',
    '3596_ISUZU BENELUX NV':     'BELGIUM',
    '3597_ISUZU IRELAND':        'IRELAND',
    '3598_IMOTORS LDA':          'PORTUGL',
    '3599_GASANZAMMIT MOTORS':   'MALTA',
    '3600_ISUZU SALES DEUTSCHL': 'GERMANY',
}
FY_TO_CY = {'FY25': 2025, 'FY26': 2026, 'FY27': 2027,
            'FY28': 2028, 'FY29': 2029, 'FY30': 2030}

parsed_cv = {}
current_country = None
for _, row in df_cv_raw.iterrows():
    col1  = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
    model = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ''
    if col1 and col1 != 'nan':
        current_country = CUST_COUNTRY.get(col1, None)
        if current_country and current_country not in parsed_cv:
            parsed_cv[current_country] = {}
    if current_country and model in ['LD', 'MD']:
        vals = {fy: float(pd.to_numeric(row.iloc[3 + fi], errors='coerce') or 0)
                for fi, fy in enumerate(['FY25', 'FY26', 'FY27', 'FY28', 'FY29', 'FY30'])}
        parsed_cv[current_country][model] = vals

# Trend CAGR for all LD/MD/LCV/F-Series (applied first, overridden below)
def trend_cagr(model_type, base_yr=2026):
    for idx, row in df_base[df_base['model_type'] == model_type].iterrows():
        vals = [float(df_base.loc[idx, str(y)] or 0) for y in range(base_yr - 3, base_yr + 1)]
        base = vals[-1]
        if base > 0 and vals[0] > 0:
            cagr = min(0.08, max(-0.08, (vals[-1] / vals[0]) ** (1 / 3) - 1))
        else:
            cagr = 0.0
        for fy in range(2027, 2031):
            df_base.loc[idx, str(fy)] = round(base * (1 + cagr) ** (fy - base_yr))

for mt in ['LD', 'MD', 'LCV', 'F-Series']:
    trend_cagr(mt)

# ISZE CV plan override: 2026-2030 using decay + new sales from 2025 base
for country, type_dict in parsed_cv.items():
    for model_type, fy_sales in type_dict.items():
        mask = (df_base['country'] == country) & (df_base['model_type'] == model_type)
        if mask.sum() == 0:
            continue
        prev_uio = float(df_base.loc[mask, '2025'].values[0])
        for fy, cy in [(f, c) for f, c in FY_TO_CY.items() if c >= 2026]:
            new_s   = fy_sales.get(fy, 0)
            new_uio = round(prev_uio * DECAY + new_s)
            df_base.loc[mask, str(cy)] = new_uio
            prev_uio = new_uio

# Israel 2027-2030: trend CAGR (applied above) extrapolates from IML 2023-2026 trend.
# UTI annual sales are NOT used here (UTI = registrations, not fleet stock).

# Re-apply ITUK F-Series forecast (trend may have overwritten)
uk_fs_mask = (df_base['country'] == 'U KING') & (df_base['model_type'] == 'F-Series')
for yr in range(2027, 2031):
    df_base.loc[uk_fs_mask, str(yr)] = f_uio[yr]

# ════════════════════════════════════════════════════════════════════════════
# STEP 7 – REMOVE RUSSIA + ROUND TO INTEGERS
# ════════════════════════════════════════════════════════════════════════════
print("[7/8] Removing Russia and rounding to integers...")

df_base = df_base[df_base['country'] != 'RUSSIA'].reset_index(drop=True)

yr_str = [str(y) for y in ALL_YEARS]
for y in yr_str:
    df_base[y] = pd.to_numeric(df_base[y], errors='coerce').fillna(0).round(0).astype(int)

print(f"    Final dataset: {len(df_base)} rows × {len(yr_str)} year columns")

# Quick sanity check
for c, mt in [('GERMANY','LD'), ('IRELAND','LD'), ('PORTUGL','LD'),
              ('U KING','LD'), ('U KING','F-Series')]:
    row = df_base[(df_base['country']==c) & (df_base['model_type']==mt)]
    if len(row):
        r = row.iloc[0]
        print(f"    {c:10s} {mt:8s}: 2024={r['2024']:>6,}  2025={r['2025']:>6,}  2026={r['2026']:>6,}")

# ════════════════════════════════════════════════════════════════════════════
# HELPER STYLES (shared by both Excel outputs)
# ════════════════════════════════════════════════════════════════════════════
C_NAVY    = "1F3864"
C_BLUE    = "2E75B6"
C_LGRAY   = "F2F2F2"
C_WHITE   = "FFFFFF"
C_YELLOW  = "FFF2CC"
C_LBLUE   = "EAF3FB"
C_GREEN   = "E2EFDA"
C_ALTROW  = "F0F5FF"
C_BORDER  = "B8CCE4"

def fill(h):    return PatternFill("solid", fgColor=h)
def fnt(bold=False, sz=9, color="000000"):
    return Font(name="Arial", bold=bold, size=sz, color=color)
def bdr():
    s = Side(style='thin', color=C_BORDER)
    return Border(left=s, right=s, top=s, bottom=s)
def aln(h='center', wrap=False):
    return Alignment(horizontal=h, vertical='center', wrap_text=wrap)

# ════════════════════════════════════════════════════════════════════════════
# STEP 8a – BUILD UIO OVERVIEW EXCEL
# ════════════════════════════════════════════════════════════════════════════
print("[8/8] Building Excel files and HTML dashboard...")

MODEL_ORDER = {'LD': 1, 'MD': 2, 'F-Series': 3, 'LCV': 4}
df_base['_ord'] = df_base['model_type'].map(MODEL_ORDER).fillna(9)
df_base['_code_n'] = pd.to_numeric(df_base['ctry_code'], errors='coerce').fillna(999)
df_sorted = df_base.sort_values(['_code_n', '_ord']).reset_index(drop=True)

HIST_FORE = [str(y) for y in range(2025, 2027)]
NEW_FORE  = [str(y) for y in range(2027, 2031)]

wb_uio = Workbook()

# ── Cover sheet ──────────────────────────────────────────────────────────────
ws_cov = wb_uio.active
ws_cov.title = "Cover"
ws_cov.sheet_view.showGridLines = False
ws_cov.row_dimensions[3].height = 40
ws_cov.merge_cells('B3:G3')
t = ws_cov['B3']
t.value = "ISUZU – Units In Operation (UIO) Overview"
t.font  = Font(name="Arial", size=18, bold=True, color="FFFFFF")
t.fill  = fill(C_NAVY)
t.alignment = aln('left')
ws_cov.merge_cells('B4:G4')
s = ws_cov['B4']
s.value = "ISZE + ITUK + Israel  |  Historical 1990–2024  |  Forecast 2025–2030"
s.font  = Font(name="Arial", size=10, color="FFFFFF")
s.fill  = fill(C_BLUE)
s.alignment = aln('left')

info = [
    ("Scope",          "ISZE (Europe), ITUK (UK – actual car park), Israel (UTI)"),
    ("Model Types",    "LD (N-series), MD, F-Series (N-series excl.), LCV | HD + TBR excluded"),
    ("N-series = LD",  "Assumption: all N-prefix model codes → LD; F-prefix → F-Series"),
    ("CV Hist.",       "IML 1990–2026; ITUK actual car park 2010–2024; Scrap Adj 2025 for BE/CY/DE/DK/GR/IE/MT/PT"),
    ("CV Forecast",    "2026–2030: ISZE CV plan (decay + new sales) from 2025 scrap-adj base; trend CAGR elsewhere"),
    ("LCV Forecast",   "2025–2028: LCV UIO file (Nov 2025); 2029–2030: trailing CAGR"),
    ("FY→CY",          "ISZE CV plan uses Japanese FY (Apr–Mar): FY25=CY2025, FY26=CY2026, …"),
    ("Russia",         "Excluded from all calculations"),
    ("Prepared",       "March 2026 | Auto-generated by build_isuzu_uio.py"),
]
for i, (k, v) in enumerate(info, start=7):
    ws_cov.row_dimensions[i].height = 18
    ws_cov.cell(row=i, column=2, value=k).font = fnt(bold=True, sz=10)
    c = ws_cov.cell(row=i, column=3, value=v)
    c.font = fnt(sz=10)
    c.alignment = aln('left', wrap=True)
ws_cov.column_dimensions['B'].width = 22
ws_cov.column_dimensions['C'].width = 80

# ── 1.UIO Overview sheet ─────────────────────────────────────────────────────
ws = wb_uio.create_sheet("1.UIO Overview")
ws.sheet_view.showGridLines = False
ws.freeze_panes = "F7"

ALL_YR_STR = [str(y) for y in ALL_YEARS]
N_META, N_YEARS = 5, len(ALL_YR_STR)

ws.column_dimensions['A'].width = 8
ws.column_dimensions['B'].width = 12
ws.column_dimensions['C'].width = 6
ws.column_dimensions['D'].width = 10
ws.column_dimensions['E'].width = 8
for i in range(N_YEARS):
    ws.column_dimensions[get_column_letter(6 + i)].width = 8

# Row 1: title
ws.row_dimensions[1].height = 26
ws.merge_cells(f'A1:{get_column_letter(N_META + N_YEARS)}1')
r1 = ws['A1']
r1.value = "ISUZU – Units In Operation (UIO)  |  ISZE · ITUK · Israel"
r1.font  = Font(name="Arial", size=13, bold=True, color="FFFFFF")
r1.fill  = fill(C_NAVY)
r1.alignment = aln('left')

# Row 2: Grand Total
total_by_year = {y: int(df_sorted[y].sum()) for y in ALL_YR_STR}
ws.row_dimensions[2].height = 18
ws.merge_cells('A2:E2')
ws['A2'].value = "GRAND TOTAL"
ws['A2'].font  = Font(name="Arial", size=10, bold=True, color="FFFFFF")
ws['A2'].fill  = fill(C_BLUE)
for col in ['B2', 'C2', 'D2', 'E2']:
    ws[col].fill = fill(C_BLUE)
for i, y in enumerate(ALL_YR_STR, start=6):
    c = ws.cell(row=2, column=i)
    c.value        = total_by_year[y] or None
    c.number_format = '#,##0'
    c.font         = Font(name="Arial", size=9, bold=True, color="FFFFFF")
    c.fill         = fill(C_BLUE)
    c.alignment    = aln()

# Row 3: Growth Rate
ws.row_dimensions[3].height = 16
ws.merge_cells('A3:E3')
ws['A3'].value = "Growth Rate Y-o-Y"
ws['A3'].font  = fnt(sz=9)
prev = None
for i, y in enumerate(ALL_YR_STR, start=6):
    c = ws.cell(row=3, column=i)
    if prev and total_by_year.get(prev, 0) > 0:
        gr = (total_by_year[y] - total_by_year[prev]) / total_by_year[prev]
        c.value = round(gr, 4)
        c.number_format = '0.0%'
    c.font = fnt(sz=9)
    c.alignment = aln()
    prev = y

ws.row_dimensions[4].height = 4
ws.row_dimensions[5].height = 4

# Row 6: Column headers
ws.row_dimensions[6].height = 30
for i, lbl in enumerate(['Ctry\nCode','Country','CV/\nLCV','Model\nType','ASC/\nDB'] + ALL_YR_STR, start=1):
    c = ws.cell(row=6, column=i, value=lbl)
    c.font      = Font(name="Arial", size=9, bold=True, color="FFFFFF")
    c.alignment = aln(wrap=True)
    c.border    = bdr()
    yr = str(lbl).strip()
    if yr in NEW_FORE:
        c.fill = fill("2E4057")
    elif yr in HIST_FORE:
        c.fill = fill(C_BLUE)
    else:
        c.fill = fill(C_NAVY)

# Data rows
prev_ctry = None
color_idx = 0
for ridx, row in df_sorted.iterrows():
    er = 7 + ridx
    ws.row_dimensions[er].height = 15
    if row['country'] != prev_ctry:
        color_idx += 1
        prev_ctry = row['country']
    bg = C_WHITE if color_idx % 2 else C_ALTROW
    if row['model_type'] == 'F-Series':
        bg = C_GREEN

    meta_vals = [row['ctry_code'], row['country'], row['cv_lcv'],
                 row['model_type'], row['asc_db']]
    for ci, v in enumerate(meta_vals, start=1):
        c = ws.cell(row=er, column=ci, value=str(v) if pd.notna(v) else '')
        c.font      = fnt(bold=(ci <= 2))
        c.fill      = fill(bg)
        c.border    = bdr()
        c.alignment = aln() if ci in [1, 3, 4, 5] else aln('left')

    for yi, y in enumerate(ALL_YR_STR, start=6):
        val = row[y]
        c = ws.cell(row=er, column=yi)
        c.value        = int(val) if val and val != 0 else None
        c.number_format = '#,##0'
        c.font         = fnt()
        c.border       = bdr()
        c.alignment    = aln()
        if y in NEW_FORE:
            c.fill = fill(C_LBLUE)
        elif y in HIST_FORE:
            c.fill = fill("FFFDE7")
        else:
            c.fill = fill(bg)

# ── Assumptions sheet ────────────────────────────────────────────────────────
ws_asm = wb_uio.create_sheet("Assumptions & Mapping")
ws_asm.sheet_view.showGridLines = False
ws_asm.column_dimensions['A'].width = 30
ws_asm.column_dimensions['B'].width = 55
ws_asm.column_dimensions['C'].width = 35

def sec_hdr(ws, row, title, col_end=3):
    ws.row_dimensions[row].height = 20
    ws.merge_cells(f'A{row}:{get_column_letter(col_end)}{row}')
    c = ws.cell(row=row, column=1, value=title)
    c.font  = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    c.fill  = fill(C_NAVY)
    c.alignment = aln('left')

r = 2
sec_hdr(ws_asm, r, "1.  Model Code Classification")
r += 2
for ci, lbl in enumerate(['Model Code / Series', 'Maps to', 'Notes'], start=1):
    c = ws_asm.cell(row=r, column=ci, value=lbl)
    c.font = fnt(bold=True, color="FFFFFF")
    c.fill = fill(C_BLUE)
ws_asm.row_dimensions[r].height = 16
r += 1

model_rows = [
    ("N-Series (NLR, NMR, NNR, NPR, N35, N50/55, N62/65, N75)", "LD (Light Duty)", "Key assumption: all N-prefix = LD"),
    ("F-Series (FRR90, FSR90, F110/120, F135, F150/180)", "F-Series", "Separate category. UK + IE + PT have F-series."),
    ("HD (Heavy Duty)", "EXCLUDED", "Not in ISZE/ITUK/Israel scope"),
    ("TBR", "EXCLUDED", "Not in scope"),
    ("LCV", "LCV", "Tracked separately with 12-year survival window"),
    ("MD (Medium Duty)", "MD", "IML classification; set to 0 for scrap-adj countries"),
]
for i, (code, maps, note) in enumerate(model_rows):
    bg = C_WHITE if i % 2 == 0 else C_ALTROW
    for ci, val in enumerate([code, maps, note], start=1):
        c = ws_asm.cell(row=r, column=ci, value=val)
        c.font = fnt(bold=(ci == 1), color="CC0000" if val == "EXCLUDED" else "000000")
        c.fill = fill(bg)
        c.border = bdr()
        c.alignment = aln('left', wrap=True)
    r += 1

r += 1
sec_hdr(ws_asm, r, "2.  Survival Rate Curves")
r += 2
for ci, lbl in enumerate(['Vehicle Age (Years)', 'CV Advanced Economy (IML)', 'LCV / IMIT (12-yr)'], start=1):
    c = ws_asm.cell(row=r, column=ci, value=lbl)
    c.font = fnt(bold=True, color="FFFFFF")
    c.fill = fill(C_BLUE)
r += 1
for age in range(1, 17):
    bg = C_WHITE if age % 2 else C_ALTROW
    lcv_v = SURV_LCV.get(age, '—')
    for ci, val in enumerate([f"Year {age}", SURV_CV.get(age, 0.0), lcv_v], start=1):
        c = ws_asm.cell(row=r, column=ci, value=val)
        c.font = fnt()
        c.fill = fill(bg)
        c.border = bdr()
        c.alignment = aln()
        if isinstance(val, float):
            c.number_format = '0%'
    r += 1
ws_asm.cell(row=r, column=1,
    value="Source: IML Calculation.xlsx (5.Survival Rate) + LCV UIO (Nov 2025)").font = fnt(sz=8, color="888888")
r += 2

sec_hdr(ws_asm, r, "3.  Scrap-Adjusted Car Park 2025")
r += 2
scrap_notes = [
    ("Sheet", "UIO.xlsx → 'CV customers with scrap logic', column O = Scrap Adj Car Park 2025"),
    ("Countries", "Belgium, Cyprus, Denmark, Germany, Greece, Ireland, Malta, Portugal"),
    ("Methodology", "~100% survival yrs 1–11, ~47% at yr 12, 0% at yr 13+  (milder than IML CV curve)"),
    ("Usage", "2025 scrap-adj value anchors the historical series; 2014–2025 scaled proportionally"),
    ("Germany 2025", "406 units (IML showed 0)"),
    ("Ireland LD 2025", "1,151 units; F-Series 2025 = 101 units (FRR90)"),
    ("Portugal LD 2025", "2,585 units; F-Series 2025 = 292 units (FRR90 + FSR90)"),
]
for i, (k, v) in enumerate(scrap_notes):
    bg = C_WHITE if i % 2 == 0 else C_ALTROW
    for ci, val in enumerate([k, v], start=1):
        c = ws_asm.cell(row=r, column=ci, value=val)
        c.font = fnt(bold=(ci == 1))
        c.fill = fill(bg)
        c.border = bdr()
        c.alignment = aln('left', wrap=True)
    r += 1

r += 1
sec_hdr(ws_asm, r, "4.  UK (ITUK) Actual Car Park")
r += 2
ituk_notes = [
    ("Source", "UIO.xlsx → sheet 'ITUK': car park snapshot of UK vehicles in service, by registration year cohort"),
    ("N-series 2024", f"Actual car park = {actual_N_2024:,} (N35 + N50/55 + N62/65 + N75 + Unspecified)"),
    ("F-Series 2024", f"Actual car park = {actual_F_2024:,} (F110/120 + F135 + F150/180)"),
    ("Method", "Survival-rate UIO series scaled so 2024 = actual car park. Scale N = {:.4f}, Scale F = {:.4f}".format(scale_N, scale_F)),
    ("UK LCV", "IML historical; IUK UK from LCV UIO file for 2025–2028 forecast"),
]
for i, (k, v) in enumerate(ituk_notes):
    bg = C_WHITE if i % 2 == 0 else C_ALTROW
    for ci, val in enumerate([k, v], start=1):
        c = ws_asm.cell(row=r, column=ci, value=val)
        c.font = fnt(bold=(ci == 1))
        c.fill = fill(bg)
        c.border = bdr()
        c.alignment = aln('left', wrap=True)
    r += 1

r += 1
sec_hdr(ws_asm, r, "5.  FY → Calendar Year Mapping")
r += 2
for ci, lbl in enumerate(['FY Period', 'Date Range', 'CY Used'], start=1):
    c = ws_asm.cell(row=r, column=ci, value=lbl)
    c.font = fnt(bold=True, color="FFFFFF")
    c.fill = fill(C_BLUE)
r += 1
for i, (fy, dr, cy) in enumerate([
    ("FY25", "2025/4/1 – 2026/3/31", "CY2025"),
    ("FY26", "2026/4/1 – 2027/3/31", "CY2026"),
    ("FY27", "2027/4/1 – 2028/3/31", "CY2027"),
    ("FY28", "2028/4/1 – 2029/3/31", "CY2028"),
    ("FY29", "2029/4/1 – 2030/3/31", "CY2029"),
    ("FY30", "2030/4/1 – 2031/3/31", "CY2030"),
]):
    bg = C_WHITE if i % 2 == 0 else C_ALTROW
    for ci, val in enumerate([fy, dr, cy], start=1):
        c = ws_asm.cell(row=r, column=ci, value=val)
        c.font = fnt()
        c.fill = fill(bg)
        c.border = bdr()
        c.alignment = aln('left')
    r += 1

r += 1
sec_hdr(ws_asm, r, "6.  LCV Distributor → Country Mapping")
r += 2
for ci, lbl in enumerate(['LCV File Entity', 'Country / Countries', 'Notes'], start=1):
    c = ws_asm.cell(row=r, column=ci, value=lbl)
    c.font = fnt(bold=True, color="FFFFFF")
    c.fill = fill(C_BLUE)
r += 1
entity_map = [
    ("IUK UK", "United Kingdom", "1-to-1"),
    ("ISD Germany", "Germany", "1-to-1"),
    ("IBX Belgium", "Belgium + Netherlands + Poland", "User-confirmed: IBX covers Benelux + PL"),
    ("ISUZU Sweden", "Sweden", "1-to-1"),
    ("RSA Norway", "Norway", "1-to-1"),
    ("IMOTORS Portugal", "Portugal + Azores", "Astara = IMOTORS LDA (3598)"),
    ("PETROS Greece", "Greece", "1-to-1"),
    ("WAE Kft Hungary", "Hungary", "1-to-1"),
    ("LOUTSIOS Cyprus", "Cyprus", "1-to-1"),
    ("ISUZU Ireland", "Ireland", "1-to-1"),
    ("GASANZAMMIT Malta", "Malta", "1-to-1"),
    ("ISUZU Denmark", "Denmark", "1-to-1"),
    ("ISUZU Finland", "Finland", "1-to-1"),
    ("ISUZU ROM AUTO", "Romania", "1-to-1"),
    ("BL. Ehf. Iceland", "Iceland", "1-to-1"),
]
for i, (e, c_, n) in enumerate(entity_map):
    bg = C_WHITE if i % 2 == 0 else C_ALTROW
    for ci, val in enumerate([e, c_, n], start=1):
        c = ws_asm.cell(row=r, column=ci, value=val)
        c.font = fnt(bold=(ci == 1))
        c.fill = fill(bg)
        c.border = bdr()
        c.alignment = aln('left', wrap=True)
    r += 1

# Save UIO overview
OUT_UIO = BASE + "ISUZU_UIO_Overview_2026.xlsx"
wb_uio.save(OUT_UIO)
print(f"    Saved: {OUT_UIO}")

# ════════════════════════════════════════════════════════════════════════════
# STEP 8b – BUILD DASHBOARD (Excel + HTML)
# ════════════════════════════════════════════════════════════════════════════

# Aggregations
CHART_YRS_STR = [str(y) for y in range(2005, 2031)]
total_by_yr   = {y: int(df_sorted[y].sum()) for y in ALL_YR_STR}
by_model      = {mt: {y: int(df_sorted[df_sorted['model_type']==mt][y].sum())
                       for y in CHART_YRS_STR}
                 for mt in ['LD', 'MD', 'F-Series', 'LCV']}
top_ctry      = df_sorted.groupby('country')['2025'].sum().sort_values(ascending=False).head(15)
key_mkts      = list(top_ctry.head(8).index)
km_yrs_int    = list(range(2015, 2031))
market_trend  = {c: {y: int(df_sorted[df_sorted['country']==c][str(y)].sum())
                     for y in km_yrs_int}
                 for c in key_mkts}

total_2025 = total_by_yr['2025']
total_2030 = total_by_yr['2030']
total_2020 = total_by_yr['2020']
cagr_2530  = (total_2030 / total_2025) ** (1/5) - 1
mix_pct    = {mt: round(by_model[mt]['2025'] / total_2025 * 100, 1)
              for mt in ['LD', 'MD', 'F-Series', 'LCV']}

NAVY  = '#1F3864'
BLUE  = '#2E75B6'
PALMC = ['#1F3864','#2E75B6','#FF6F00','#4CAF50','#9C27B0','#00BCD4','#F44336','#795548']
MODEL_CLR = {'LCV': '#2196F3', 'LD': '#FF6F00', 'MD': '#795548', 'F-Series': '#4CAF50'}

def kfmt(x, pos): return f'{x/1000:,.0f}k' if x >= 1000 else f'{x:,.0f}'
fmt_k = FuncFormatter(kfmt)

def save_chart(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf

# Chart 1 – Grand Total Trend
chart_ints = list(range(2005, 2031))
total_vals = [total_by_yr[str(y)] for y in chart_ints]
fig, ax = plt.subplots(figsize=(12, 4))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F7FAFF')
hist_v = [v if y <= 2024 else None for v, y in zip(total_vals, chart_ints)]
fore_v = [v if y >= 2024 else None for v, y in zip(total_vals, chart_ints)]
ax.plot(chart_ints, hist_v, color=NAVY, lw=2.5, label='Historical')
ax.plot(chart_ints, fore_v, color=BLUE, lw=2.5, ls='--', label='Forecast')
ax.fill_between(chart_ints, [v or 0 for v in hist_v], alpha=0.1, color=NAVY)
ax.fill_between(chart_ints, [v or 0 for v in fore_v], alpha=0.08, color=BLUE)
ax.axvline(2024.5, color='#AAAAAA', lw=1, ls=':')
ax.yaxis.set_major_formatter(fmt_k)
ax.set_xticks(chart_ints[::2])
ax.set_xticklabels([str(y) for y in chart_ints[::2]], rotation=30, fontsize=8)
ax.yaxis.set_tick_params(labelsize=8)
ax.set_title('Total Units In Operation – 2005–2030', fontsize=11, fontweight='bold', color=NAVY)
ax.legend(fontsize=8)
ax.grid(axis='y', alpha=0.3)
ax.spines[['top','right']].set_visible(False)
fig.tight_layout()
c1 = save_chart(fig)

# Chart 2 – Model Mix Stacked Bar
yrs_mix = list(range(2015, 2031))
fig, ax = plt.subplots(figsize=(8, 4))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F7FAFF')
bot = np.zeros(len(yrs_mix))
for mt in ['LCV','LD','MD','F-Series']:
    vals = np.array([by_model[mt][str(y)] for y in yrs_mix])
    ax.bar(yrs_mix, vals, bottom=bot, color=MODEL_CLR[mt], label=mt, alpha=0.9, width=0.75)
    bot += vals
ax.axvline(2024.5, color='#AAAAAA', lw=1, ls=':')
ax.yaxis.set_major_formatter(fmt_k)
ax.set_xticks(yrs_mix[::2])
ax.set_xticklabels([str(y) for y in yrs_mix[::2]], rotation=30, fontsize=8)
ax.yaxis.set_tick_params(labelsize=8)
ax.set_title('UIO by Model Type – 2015–2030', fontsize=11, fontweight='bold', color=NAVY)
ax.legend(fontsize=8, ncol=2)
ax.grid(axis='y', alpha=0.3)
ax.spines[['top','right']].set_visible(False)
fig.tight_layout()
c2 = save_chart(fig)

# Chart 3 – Top 10 Countries horizontal bar
top10_l = list(top_ctry.head(10).index)[::-1]
top10_v = [int(top_ctry[c]) for c in top10_l]
fig, ax = plt.subplots(figsize=(7, 4))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F7FAFF')
bars = ax.barh(top10_l, top10_v, color=NAVY, alpha=0.88, height=0.65)
for bar, val in zip(bars, top10_v):
    ax.text(bar.get_width() + max(top10_v)*0.01, bar.get_y()+bar.get_height()/2,
            f'{val:,}', va='center', fontsize=8)
ax.xaxis.set_major_formatter(fmt_k)
ax.xaxis.set_tick_params(labelsize=8)
ax.yaxis.set_tick_params(labelsize=8)
ax.set_title('Top 10 Countries – UIO 2025', fontsize=11, fontweight='bold', color=NAVY)
ax.spines[['top','right']].set_visible(False)
fig.tight_layout()
c3 = save_chart(fig)

# Chart 4 – Key Markets Trend
fig, ax = plt.subplots(figsize=(12, 4))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F7FAFF')
for i, ctry in enumerate(key_mkts):
    vals = [market_trend[ctry][y] for y in km_yrs_int]
    hist = [v if y <= 2024 else None for v, y in zip(vals, km_yrs_int)]
    fore = [v if y >= 2024 else None for v, y in zip(vals, km_yrs_int)]
    col = PALMC[i % len(PALMC)]
    ax.plot(km_yrs_int, hist, color=col, lw=2, label=ctry)
    ax.plot(km_yrs_int, fore, color=col, lw=2, ls='--')
ax.axvline(2024.5, color='#AAAAAA', lw=1, ls=':')
ax.yaxis.set_major_formatter(fmt_k)
ax.set_xticks(km_yrs_int[::2])
ax.set_xticklabels([str(y) for y in km_yrs_int[::2]], rotation=30, fontsize=8)
ax.yaxis.set_tick_params(labelsize=8)
ax.set_title('Key Markets UIO Trend – 2015–2030', fontsize=11, fontweight='bold', color=NAVY)
ax.legend(fontsize=7, ncol=2)
ax.grid(axis='y', alpha=0.3)
ax.spines[['top','right']].set_visible(False)
fig.tight_layout()
c4 = save_chart(fig)

# ── Dashboard Excel ───────────────────────────────────────────────────────────
wb_dash = load_workbook(OUT_UIO)
ws_d = wb_dash.create_sheet("Dashboard", 0)
ws_d.sheet_view.showGridLines = False

ws_d.row_dimensions[1].height = 38
ws_d.merge_cells('A1:O1')
c = ws_d['A1']
c.value = "ISUZU – UIO Dashboard  |  ISZE · ITUK · Israel  |  2026 Edition"
c.font  = Font(name="Arial", size=15, bold=True, color="FFFFFF")
c.fill  = fill(C_NAVY)
c.alignment = aln('left')

kpis = [
    ("Total UIO 2020",  f"{total_2020:,}",    "2E75B6"),
    ("Total UIO 2025E", f"{total_2025:,}",    "1F3864"),
    ("Total UIO 2030F", f"{total_2030:,}",    "2E4057"),
    ("CAGR 2025–2030",  f"{cagr_2530:.2%}",   "4CAF50"),
    ("LCV Share 2025",  f"{mix_pct['LCV']}%", "FF6F00"),
    ("CV Share 2025",   f"{round(100-mix_pct['LCV'],1)}%", "795548"),
]
ws_d.row_dimensions[2].height = 8
ws_d.row_dimensions[3].height = 22
ws_d.row_dimensions[4].height = 28
ws_d.row_dimensions[5].height = 8
for col in range(1, 14):
    ws_d.column_dimensions[get_column_letter(col)].width = 10

for (lbl, val, bg), col in zip(kpis, [1,3,5,7,9,11]):
    ws_d.merge_cells(start_row=3, start_column=col, end_row=3, end_column=col+1)
    ws_d.merge_cells(start_row=4, start_column=col, end_row=4, end_column=col+1)
    lc = ws_d.cell(row=3, column=col, value=lbl)
    lc.font = Font(name="Arial", size=9, color="FFFFFF")
    lc.fill = fill(bg)
    lc.alignment = aln()
    vc = ws_d.cell(row=4, column=col, value=val)
    vc.font = Font(name="Arial", size=13, bold=True, color="FFFFFF")
    vc.fill = fill(bg)
    vc.alignment = aln()

ws_d.row_dimensions[6].height = 8
for buf, anchor, w, h in [(c1,'A7',680,235),(c4,'I7',680,235),
                           (c2,'A22',460,235),(c3,'H22',400,235)]:
    img = XLImage(buf)
    img.width, img.height = w, h
    ws_d.add_image(img, anchor)

note_row = 38
ws_d.merge_cells(f'A{note_row}:O{note_row}')
nc = ws_d[f'A{note_row}']
nc.value = ("Source: IML calculation.xlsx | UIO.xlsx (ITUK car park + UTI Israel + Scrap Adj 2025) | "
            "LCV UIO Nov-2025 | ISZE CV FY2025–FY2030  —  Auto-generated March 2026")
nc.font = Font(name="Arial", size=8, italic=True, color="888888")
nc.alignment = aln('left')

OUT_DASH = BASE + "ISUZU_UIO_Dashboard_2026.xlsx"
wb_dash.save(OUT_DASH)
print(f"    Saved: {OUT_DASH}")

# ── HTML Dashboard ────────────────────────────────────────────────────────────
km_datasets_js = json.dumps([{
    'label': ctry,
    'data': [market_trend[ctry][y] for y in km_yrs_int],
    'borderColor': PALMC[i % len(PALMC)],
    'backgroundColor': 'transparent',
    'tension': 0.3, 'pointRadius': 2, 'borderWidth': 2,
} for i, ctry in enumerate(key_mkts)])

years_js  = list(range(2005, 2031))
tot_js    = [total_by_yr[str(y)] for y in years_js]
hist_idx  = years_js.index(2024)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ISUZU UIO Dashboard 2026</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:Arial,sans-serif;background:#EEF2F7;color:#1a1a2e}}
  .header{{background:#1F3864;color:#fff;padding:14px 28px;display:flex;align-items:center;justify-content:space-between}}
  .header h1{{font-size:1.2rem}}
  .header .sub{{font-size:0.78rem;opacity:.75;margin-top:3px}}
  .badge{{background:#2E75B6;padding:3px 10px;border-radius:12px;font-size:.72rem}}
  .kpi-strip{{display:flex;gap:10px;padding:12px 28px;background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.07);flex-wrap:wrap}}
  .kpi{{flex:1;min-width:110px;background:#F0F5FF;border-left:4px solid #2E75B6;border-radius:5px;padding:8px 12px}}
  .kpi.a{{border-left-color:#1F3864;background:#E8EDF7}}
  .kpi.g{{border-left-color:#4CAF50;background:#F0F8F0}}
  .kpi.o{{border-left-color:#FF6F00;background:#FFF8F0}}
  .kpi-label{{font-size:.68rem;color:#666;text-transform:uppercase;letter-spacing:.4px}}
  .kpi-value{{font-size:1.2rem;font-weight:700;color:#1F3864;margin-top:2px}}
  .grid{{display:grid;gap:12px;padding:14px 28px;grid-template-columns:1fr 1fr}}
  .card{{background:#fff;border-radius:7px;box-shadow:0 1px 4px rgba(0,0,0,.07);padding:14px 16px}}
  .card.full{{grid-column:1/-1}}
  .card h3{{font-size:.85rem;color:#1F3864;font-weight:700;margin-bottom:10px;border-bottom:2px solid #E8EDF7;padding-bottom:5px}}
  .chart-wrap{{position:relative;height:270px}}
  table{{width:100%;border-collapse:collapse;font-size:.78rem;margin-top:4px}}
  th{{background:#1F3864;color:#fff;padding:5px 8px;text-align:left;font-size:.72rem}}
  tr:nth-child(even){{background:#F0F5FF}}
  td{{padding:4px 8px;border-bottom:1px solid #E8EDF7}}
  td.r{{text-align:right;font-variant-numeric:tabular-nums}}
  .bar-cell{{display:flex;align-items:center;gap:5px}}
  .mini-bar{{height:7px;border-radius:3px;background:#2E75B6;min-width:2px}}
  .footer{{text-align:center;padding:10px;font-size:.68rem;color:#999;background:#fff;margin:0 28px 18px;border-radius:0 0 7px 7px}}
</style>
</head>
<body>
<div class="header">
  <div><h1>ISUZU – Units In Operation (UIO) Overview</h1>
  <div class="sub">ISZE · ITUK (UK) · Israel &nbsp;|&nbsp; Historical 1990–2024 &nbsp;|&nbsp; Forecast 2025–2030</div></div>
  <span class="badge">March 2026</span>
</div>
<div class="kpi-strip">
  <div class="kpi"><div class="kpi-label">Total UIO 2020</div><div class="kpi-value">{total_2020:,}</div></div>
  <div class="kpi a"><div class="kpi-label">Total UIO 2024</div><div class="kpi-value">{total_by_yr['2024']:,}</div></div>
  <div class="kpi a"><div class="kpi-label">Total UIO 2025E</div><div class="kpi-value">{total_2025:,}</div></div>
  <div class="kpi a"><div class="kpi-label">Total UIO 2030F</div><div class="kpi-value">{total_2030:,}</div></div>
  <div class="kpi g"><div class="kpi-label">CAGR 2025–2030</div><div class="kpi-value">{cagr_2530:.2%}</div></div>
  <div class="kpi o"><div class="kpi-label">LCV Share 2025</div><div class="kpi-value">{mix_pct['LCV']}%</div></div>
  <div class="kpi o"><div class="kpi-label">CV Share 2025</div><div class="kpi-value">{round(100-mix_pct['LCV'],1)}%</div></div>
  <div class="kpi"><div class="kpi-label">Countries tracked</div><div class="kpi-value">{df_sorted['country'].nunique()}</div></div>
</div>
<div class="grid">
  <div class="card full"><h3>📈 Total UIO Trend — 2005 to 2030</h3><div class="chart-wrap"><canvas id="c1"></canvas></div></div>
  <div class="card"><h3>🔵 UIO by Model Type — 2015–2030</h3><div class="chart-wrap"><canvas id="c2"></canvas></div></div>
  <div class="card"><h3>🏆 Top 10 Countries — UIO 2025</h3><div class="chart-wrap"><canvas id="c3"></canvas></div></div>
  <div class="card full"><h3>🌍 Key Markets UIO Trend — 2015–2030</h3><div class="chart-wrap"><canvas id="c4"></canvas></div></div>
  <div class="card full">
    <h3>📋 Model Mix — 2025 vs 2030F</h3>
    <table>
      <thead><tr><th>Model Type</th><th>UIO 2025</th><th>Share</th><th>UIO 2030F</th><th>Growth</th><th>Visual</th></tr></thead>
      <tbody>{"".join(f'''<tr><td><b>{mt}</b></td><td class="r">{by_model[mt]["2025"]:,}</td>
        <td class="r">{mix_pct[mt]}%</td>
        <td class="r">{by_model[mt]["2030"]:,}</td>
        <td class="r">{(by_model[mt]["2030"]/by_model[mt]["2025"]-1)*100:.1f}%</td>
        <td><div class="bar-cell"><div class="mini-bar" style="width:{int(mix_pct[mt]*2)}px"></div></div></td></tr>'''
        for mt in ['LD','MD','F-Series','LCV'] if by_model[mt]['2025']>0)}</tbody></table>
    <br>
    <h3>🌐 Top 10 Countries — 2025 vs 2030F</h3>
    <table>
      <thead><tr><th>Country</th><th>2024</th><th>2025E</th><th>2030F</th><th>CAGR 25→30</th><th>Visual 2025</th></tr></thead>
      <tbody>{"".join(f'''<tr><td><b>{c_}</b></td>
        <td class="r">{int(df_sorted[df_sorted["country"]==c_]["2024"].sum()):,}</td>
        <td class="r">{int(top_ctry[c_]):,}</td>
        <td class="r">{int(df_sorted[df_sorted["country"]==c_]["2030"].sum()):,}</td>
        <td class="r">{((df_sorted[df_sorted["country"]==c_]["2030"].sum()/top_ctry[c_])**(1/5)-1)*100:.1f}%</td>
        <td><div class="bar-cell"><div class="mini-bar" style="width:{int(top_ctry[c_]/top_ctry.iloc[0]*120)}px"></div></div></td></tr>'''
        for c_ in list(top_ctry.head(10).index))}</tbody></table>
  </div>
</div>
<div class="footer">Source: IML calculation.xlsx | UIO.xlsx | LCV UIO Nov-2025 | ISZE CV FY2025–FY2030 — Auto-generated March 2026</div>
<script>
const def_ = {{
  plugins:{{legend:{{labels:{{font:{{family:'Arial',size:11}}}}}}}},
  scales:{{x:{{ticks:{{font:{{size:10}}}},grid:{{display:false}}}},
    y:{{ticks:{{font:{{size:10}},callback:v=>v>=1000?(v/1000).toFixed(0)+'k':v}},grid:{{color:'#EEF2F7'}}}}}},
  responsive:true,maintainAspectRatio:false
}};
const yrs={years_js};
const tot={tot_js};
const fi={hist_idx};
new Chart(document.getElementById('c1'),{{type:'line',data:{{labels:yrs,datasets:[
  {{label:'Historical',data:tot.map((v,i)=>i<=fi?v:null),borderColor:'#1F3864',backgroundColor:'rgba(31,56,100,0.08)',fill:true,tension:0.3,pointRadius:2,borderWidth:2.5}},
  {{label:'Forecast',data:tot.map((v,i)=>i>=fi?v:null),borderColor:'#2E75B6',backgroundColor:'rgba(46,117,182,0.07)',fill:true,tension:0.3,pointRadius:2,borderWidth:2.5,borderDash:[5,3]}}
]}},options:def_}});
const ymix={list(range(2015,2031))};
new Chart(document.getElementById('c2'),{{type:'bar',data:{{labels:ymix,datasets:[
  {{label:'LCV',data:{[by_model['LCV'][str(y)] for y in range(2015,2031)]},backgroundColor:'#2196F3',stack:'a'}},
  {{label:'LD',data:{[by_model['LD'][str(y)] for y in range(2015,2031)]},backgroundColor:'#FF6F00',stack:'a'}},
  {{label:'MD',data:{[by_model['MD'][str(y)] for y in range(2015,2031)]},backgroundColor:'#795548',stack:'a'}},
  {{label:'F-Series',data:{[by_model['F-Series'][str(y)] for y in range(2015,2031)]},backgroundColor:'#4CAF50',stack:'a'}}
]}},options:{{...def_,scales:{{x:{{stacked:true,ticks:{{font:{{size:10}}}},grid:{{display:false}}}},y:{{stacked:true,ticks:{{font:{{size:10}},callback:v=>v>=1000?(v/1000).toFixed(0)+'k':v}},grid:{{color:'#EEF2F7'}}}}}}}}}});
new Chart(document.getElementById('c3'),{{type:'bar',data:{{labels:{top10_l[::-1]},datasets:[{{label:'UIO 2025',data:{top10_v[::-1]},backgroundColor:'#1F3864',borderRadius:4}}]}},options:{{...def_,indexAxis:'y',plugins:{{legend:{{display:false}}}},scales:{{x:{{ticks:{{font:{{size:10}},callback:v=>v>=1000?(v/1000).toFixed(0)+'k':v}},grid:{{color:'#EEF2F7'}}}},y:{{ticks:{{font:{{size:10}}}},grid:{{display:false}}}}}}}}}});
const kmd={km_datasets_js};
new Chart(document.getElementById('c4'),{{type:'line',data:{{labels:{km_yrs_int},datasets:kmd}},options:def_}});
</script>
</body></html>"""

OUT_HTML = BASE + "ISUZU_UIO_Dashboard_2026.html"
with open(OUT_HTML, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"    Saved: {OUT_HTML}")

print("\n" + "=" * 60)
print("All done! Output files:")
print(f"  • ISUZU_UIO_Overview_2026.xlsx")
print(f"  • ISUZU_UIO_Dashboard_2026.xlsx  (Dashboard tab + data)")
print(f"  • ISUZU_UIO_Dashboard_2026.html  (open in any browser)")
print("=" * 60)
