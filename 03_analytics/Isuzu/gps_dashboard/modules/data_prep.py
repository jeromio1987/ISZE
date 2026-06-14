"""
Module 1: Data Preparation
ISZE GPS & Spend per Unit Dashboard
Loads, cleans, and maps all input data sources.

Key design:
  - UIO is loaded from V13 Excel (multi-year 2020–2024, CV/LCV split)
  - Each distributor gets its OWN UIO segment:
      ITUK → CV (LD + F-Series) UIO only
      IUK  → LCV UIO only
      UTI  → CV (LD + MD) UIO only   [Universal Trucks Israel]
      UMI  → LCV UIO only            [Universal Motors Israel]
      All others → total UIO (CV + LCV combined)
  - Sales year is matched to UIO year (2022→2022 UIO, 2023→2023 UIO, etc.)
  - Only 2025/2026 use 2024 as proxy (flagged)
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ─── SOLD_TO NAME → DISTRIBUTOR CODE ─────────────────────────────────────────
# Resolves SAP sold_to name variants → internal distributor_code
#
# Israel naming (V13 / CLAUDE.md confirmed):
#   UNIVERSAL MOTORS ISRAEL LTD  → UMI  (LCV, D-Max only)
#   UNIVERSAL TRUCKS ISRAEL LTD  → UTI  (CV, LD + MD trucks)

SOLD_TO_OVERRIDES = {
    # ── UK ───────────────────────────────────────────────────────────────────
    "ISUZU TRUCK (UK) LIMITED":          "ITUK",   # CV trucks (LD + F-Series)
    "ISUZU TRUCK UK LIMITED":            "ITUK",   # variant spelling
    "I.M. PARTS & SERVICE Limited":      "IUK",    # LCV D-Max

    # ── Israel ────────────────────────────────────────────────────────────────
    "UNIVERSAL MOTORS ISRAEL LTD":       "UMI",    # LCV (D-Max)
    "UNIVERSAL TRUCKS ISRAEL LTD":       "UTI",    # CV (trucks LD + MD)

    # ── Portugal ──────────────────────────────────────────────────────────────
    "IMOTORS - Importacao e Comercio":   "PORTUGAL",
    "I Motors":                          "PORTUGAL",

    # ── Ireland ───────────────────────────────────────────────────────────────
    "ISUZU IRELAND":                     "IRELAND",
    "Isuzu Ireland":                     "IRELAND",

    # ── Greece ───────────────────────────────────────────────────────────────
    "PETROS PETROPOULOS S.A. (VEHICLE)": "GREECE",
    "PETROS PETROPOULOS S.A.":           "GREECE",

    # ── Belgium / IBX ────────────────────────────────────────────────────────
    # Master CSV has both BELGIUM and POLAND mapped to "ISUZU BENELUX NV".
    # POLAND entry comes last so overwrites BELGIUM in dict — override here.
    # All Benelux-region sales are invoiced through the Belgian entity (IBX).
    "ISUZU BENELUX NV":                 "BELGIUM",

    # ── Romania (not in master CSV) ───────────────────────────────────────────
    "ISUZU ROM AUTO SRL":                "ROMANIA",

    # ── Germany ──────────────────────────────────────────────────────────────
    "ISUZU SALES DEUTSCHLAND GMBH":      "GERMANY",
    "XXX ISUZU SALES DEUTSCHLAND GMBH":  "GERMANY",   # legacy SAP code
    "Isuzu Motors Germany GmbH":         "GERMANY_SERVICE",  # internal — excluded

    # ── Sweden ───────────────────────────────────────────────────────────────
    "ISUZU MOTORS SWEDEN AB":            "SWEDEN",
    "ISUZU SVERIGE AB":                  "SWEDEN",

    # ── Exclude ───────────────────────────────────────────────────────────────
    "ISUZU MOTORS LIMITED":              "IML_INTERNAL",   # Japan parent
    "JSC ISUZU RUS":                     "RUSSIA_EXCLUDE", # zero sales
    "Forlog NV":                         "FORLOG_EXCLUDE", # micro, not a distributor
}

# Distributor codes to EXCLUDE from all GPS/spend calculations
EXCLUDED_CODES = {
    "GERMANY_SERVICE",  # Internal service dept, not distributor sales
    "MIDI",             # Italy distributor — excluded (no ISZE direct sales; Italy UIO not usable)
    "IML_INTERNAL",     # Japan parent — internal transfers
    "RUSSIA_EXCLUDE",   # Zero sales, no UIO
    "FORLOG_EXCLUDE",   # Micro/noise
    "NETHERLANDS",      # UIO ≈ 1, covered under BELGIUM entity sales
    "LUXEMBOURG",       # UIO = 0
}

# Distributors not in master CSV — metadata added here
EXTRA_DISTRIBUTORS = {
    "ROMANIA":  {"country": "Romania",  "region": "CEE",  "cv_lcv_scope": "TOTAL"},
}

# ─── V13 dist label → distributor_code ───────────────────────────────────────
# Maps the 'Distributor' column in V13 '1.UIO Overview' to internal codes
V13_DIST_TO_CODE = {
    "UTI":                    "UTI",       # Israel CV trucks
    "UMI":                    "UMI",       # Israel LCV
    "BL":                     "ICELAND",
    "RSA":                    "NORWAY",
    "Isuzu Sverige":          "SWEDEN",
    "Isuzu Denmark":          "DENMARK",
    "ITUK":                   "ITUK",      # UK CV trucks
    "IUK":                    "IUK",       # UK LCV
    "Isuzu Ireland":          "IRELAND",
    "IBX":                    "BELGIUM",   # IBX covers BE/NL/PL/LUX — use BELGIUM as primary
    "ISD-Lang":               "GERMANY",
    "Imotors":                "PORTUGAL",
    "GasanZammit":            "MALTA",
    "Nordic Auto.":           "FINLAND",
    "AutoWallis":             "HUNGARY",
    "Petros Petropoulos":     "GREECE",
    "Isuzu Rom Auto":         "ROMANIA",
    "Loutsios & Sons":        "CYPRUS",
}

# Which distributors use ONLY their segment UIO (not combined CV+LCV)
# Everyone else uses the sum of all their rows
SEGMENT_ONLY = {
    "ITUK": "CV",    # CV trucks only
    "IUK":  "LCV",   # LCV only
    "UTI":  "CV",    # Israel CV trucks only
    "UMI":  "LCV",   # Israel LCV only
}

# UIO reference year for proxy (used when year not in V13)
UIO_PROXY_YEAR = 2024
UIO_AVAILABLE_YEARS = [2020, 2021, 2022, 2023, 2024]


def load_distributor_mapping(filepath: str) -> pd.DataFrame:
    """Load and extend the distributor master CSV."""
    df = pd.read_csv(filepath)
    df.columns = [c.strip() for c in df.columns]

    extras = []
    for code, meta in EXTRA_DISTRIBUTORS.items():
        extras.append({"distributor_code": code, "legal_entity": code, **meta,
                        "notes": "Added from sales data"})
    if extras:
        df = pd.concat([df, pd.DataFrame(extras)], ignore_index=True)

    # Add UMI and UTI rows if not already in file
    existing_codes = set(df['distributor_code'].tolist())
    israel_extras = []
    if "UMI" not in existing_codes:
        israel_extras.append({
            "distributor_code": "UMI", "legal_entity": "UNIVERSAL MOTORS ISRAEL LTD",
            "country": "Israel", "region": "MENA", "uio_match": "UMI",
            "segment_lcv": "Yes", "segment_cv": "No",
            "notes": "Israel LCV (D-Max) — UIO from V13 UMI row"
        })
    if "UTI" not in existing_codes and "UTI_CV" in existing_codes:
        # Rename UTI_CV to UTI (UTI = trucks = CV per V13/CLAUDE.md)
        df.loc[df['distributor_code'] == 'UTI_CV', 'distributor_code'] = 'UTI'
        df.loc[df['distributor_code'] == 'UTI', 'uio_match'] = 'UTI'
        # Old UTI row (was pointing at Universal Motors = LCV) → rename to UMI
        df.loc[df['distributor_code'] == 'UTI', 'distributor_code'] = \
            df.loc[df['distributor_code'] == 'UTI', 'distributor_code'].apply(
                lambda x: 'UMI' if x == 'UTI' else x
            )
    if israel_extras:
        df = pd.concat([df, pd.DataFrame(israel_extras)], ignore_index=True)

    return df


def load_uio_from_excel(filepath: str) -> pd.DataFrame:
    """
    Load multi-year UIO from V13 Excel (sheet '1.UIO Overview').

    Returns long-format DataFrame:
        distributor_code | year | uio_units | cv_lcv | model

    For distributors in SEGMENT_ONLY:
        - Only rows matching their segment are kept
        - e.g., ITUK → CV rows only; IUK → LCV rows only

    For all others:
        - CV + LCV rows are summed per year (total addressable fleet)

    UIO available: 2020–2024 (actual). 2025+ = not loaded (proxy logic in calculator).
    """
    import openpyxl
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb['1.UIO Overview']

    # Build year → column index map
    header_row = list(ws.iter_rows(min_row=6, max_row=6, values_only=True))[0]
    year_cols = {}
    for i, h in enumerate(header_row):
        try:
            yr = int(str(h).strip())
            if yr in UIO_AVAILABLE_YEARS:
                year_cols[yr] = i
        except:
            pass

    rows = []
    for row in ws.iter_rows(min_row=7, max_row=500, values_only=True):
        if row[0] is None:
            continue
        dist_v13 = str(row[5]).strip() if row[5] else ''
        if not dist_v13 or dist_v13 == 'None':
            continue
        # Skip MIDI rows
        if 'MIDI' in dist_v13.upper():
            continue

        dist_code = V13_DIST_TO_CODE.get(dist_v13)
        if not dist_code:
            continue  # Unmapped V13 distributor

        cv_lcv = str(row[2]).strip() if row[2] else ''
        model = str(row[3]).strip() if row[3] else ''

        # Segment filter for ITUK/IUK/UTI/UMI
        if dist_code in SEGMENT_ONLY:
            expected_segment = SEGMENT_ONLY[dist_code]
            if cv_lcv != expected_segment:
                continue  # Skip rows not belonging to this distributor's segment

        for yr, col_idx in year_cols.items():
            val = row[col_idx]
            if val is not None:
                rows.append({
                    'distributor_code': dist_code,
                    'year': yr,
                    'uio_units': int(val),
                    'cv_lcv': cv_lcv,
                    'model': model,
                })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Sum across model rows (e.g., ITUK has LD + F-Series → sum both for total ITUK CV UIO)
    df_agg = (
        df.groupby(['distributor_code', 'year'])
        .agg(uio_units=('uio_units', 'sum'))
        .reset_index()
    )

    print(f"[data_prep] UIO loaded: {len(df_agg)} distributor×year combos | "
          f"distributors: {sorted(df_agg['distributor_code'].unique())}")

    return df_agg


def build_uio_lookup(df_uio: pd.DataFrame) -> dict:
    """
    Build fast lookup dict: (distributor_code, year) → uio_units.
    For years not in V13 (2025, 2026), use 2024 as proxy.
    """
    lookup = {}
    proxy = {}  # distributor_code → 2024 UIO (proxy for future years)

    for _, row in df_uio.iterrows():
        lookup[(row['distributor_code'], row['year'])] = row['uio_units']
        if row['year'] == UIO_PROXY_YEAR:
            proxy[row['distributor_code']] = row['uio_units']

    return lookup, proxy


def build_name_to_code_map(df_mapping: pd.DataFrame) -> dict:
    """Build sold_to name → distributor_code lookup."""
    base_map = dict(zip(df_mapping['legal_entity'], df_mapping['distributor_code']))
    base_map.update(SOLD_TO_OVERRIDES)
    return base_map


def load_sales_data(filepath: str, df_mapping: pd.DataFrame) -> pd.DataFrame:
    """
    Load and clean the raw sales TSV/CSV.

    Returns cleaned DataFrame with:
        - distributor_code mapped
        - excluded entities removed
        - billing_date parsed, year/month/quarter/fiscal_year added
        - is_credit_note flag
    """
    # ── 1. Load ────────────────────────────────────────────────────────────
    sep = '\t' if filepath.endswith('.tsv') else ','
    df = pd.read_csv(filepath, sep=sep, low_memory=False)
    df.columns = [c.strip() for c in df.columns]

    # ── 2. Map sold_to → distributor_code ──────────────────────────────────
    name_to_code = build_name_to_code_map(df_mapping)
    df['distributor_code'] = df['sold_to'].map(name_to_code)

    unmapped = df['distributor_code'].isna()
    if unmapped.any():
        names = df.loc[unmapped, 'sold_to'].unique()
        print(f"[data_prep] WARNING: {unmapped.sum():,} rows have unmapped sold_to: {list(names)}")
        df.loc[unmapped, 'distributor_code'] = 'UNMAPPED'

    # ── 3. Filter exclusions ───────────────────────────────────────────────
    before = len(df)
    df = df[~df['distributor_code'].isin(EXCLUDED_CODES)].copy()
    print(f"[data_prep] Excluded {before - len(df):,} rows — MIDI, Germany service, internal")

    # ── 4. Parse dates ─────────────────────────────────────────────────────
    df['billing_date'] = pd.to_datetime(df['billing_date'], dayfirst=True, errors='coerce')
    df['year'] = df['billing_date'].dt.year.fillna(df['year']).astype(int)
    df['month'] = df['billing_date'].dt.month
    df['quarter'] = df['billing_date'].dt.quarter
    df['fiscal_year'] = df.apply(_get_fiscal_year, axis=1)

    # ── 5. Type cleanup ────────────────────────────────────────────────────
    df['net_sales_value'] = pd.to_numeric(df['net_sales_value'], errors='coerce').fillna(0)
    df['billed_qty'] = pd.to_numeric(df['billed_qty'], errors='coerce').fillna(0)
    df['is_credit_note'] = df['net_sales_value'] < 0

    print(f"[data_prep] Loaded {len(df):,} rows | "
          f"{df['distributor_code'].nunique()} distributors | "
          f"Years: {sorted(df['year'].unique())} | "
          f"Credit notes: {df['is_credit_note'].sum():,}")

    return df


def _get_fiscal_year(row) -> int:
    """ISZE Fiscal Year: Apr–Mar. FY2024 = Apr 2024 – Mar 2025."""
    year = row['year']
    month = row.get('month')
    if pd.isna(month):
        return year
    return year if int(month) >= 4 else year - 1


def get_fiscal_year_dates(fiscal_year: int) -> tuple:
    """FY2024 → ('2024-04-01', '2025-03-31')"""
    return f"{fiscal_year}-04-01", f"{fiscal_year + 1}-03-31"


def get_distributor_metadata(df_mapping: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a clean distributor metadata table (one row per code).
    Used to enrich spend/unit results with country, region etc.
    """
    cols = [c for c in ['distributor_code', 'country', 'region', 'segment_lcv', 'segment_cv']
            if c in df_mapping.columns]
    return df_mapping[cols].drop_duplicates('distributor_code')
