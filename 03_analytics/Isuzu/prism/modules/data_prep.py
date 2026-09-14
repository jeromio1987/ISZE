"""
PRISM Data Hierarchy — Supporting Module: Data Preparation
==========================================================
This module is a dependency of both Layer 2A (GPS) and Layer 2B (PMS).
It handles all raw data loading, cleaning, and distributor mapping.

Key responsibilities:
  - Load UIO from V13 Excel (multi-year 2020–2024, CV/LCV split per distributor)
  - Load sales TSV/CSV and map sold_to names → distributor_code
  - Apply exclusions (MIDI, Germany service dept, IML internal, etc.)
  - Parse dates, add fiscal_year, credit note flags
  - Build UIO lookup dict for fast year-matched lookups

CRITICAL — Distributor segmentation:
  ITUK → CV trucks only (LD + F-Series UIO)
  IUK  → LCV D-Max only
  UTI  → CV trucks only (Universal Trucks Israel)
  UMI  → LCV D-Max only (Universal Motors Israel)
  All others → total CV+LCV combined UIO

CRITICAL — UIO proxy rule:
  Actual UIO available: 2020–2024 only (V13 Excel).
  2025/2026 → uses 2024 as proxy. Flagged in outputs as uio_proxy=True.
  Never use total registrations as denominator — use surviving parc.

Part of PRISM — Parts Revenue Intelligence & Sales Monitor
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

# SAP sold-to pt → distributor_code. Wins over the sold_to *name* column.
# CY extracts often put a ship-to / payer short code in `sold_to` (IUK 89,
# ITUK 2194, UTI 1797) while `sold_to_sap` is the real account (2574 / 2575 / 1799).
# UTI 1799 rows commonly carry the UMI legal name — never map those to UMI.
SAP_SOLD_TO_OVERRIDES: dict[int, str] = {
    66: "GREECE",
    76: "IRELAND",
    86: "NORWAY",
    88: "MIDI",
    90: "BELGIUM",
    105: "GERMANY_SERVICE",
    146: "ITUK",
    373: "IML_INTERNAL",
    393: "CYPRUS",
    396: "ROMANIA",
    519: "PORTUGAL",
    537: "HUNGARY",
    601: "GERMANY",
    1576: "ICELAND",
    1759: "MALTA",
    1797: "UMI",
    1799: "UTI",
    2027: "DENMARK",
    2181: "SWEDEN",
    2194: "MIDI",
    2294: "UKRAINE",
    2516: "GERMANY",
    2574: "IUK",
    2575: "ITUK",
    2679: "FINLAND",
    2733: "ARMENIA",
    2734: "KAZAKHSTAN",
    2751: "DENMARK",
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
    "TURKEY",           # Not an ISZE customer — exclude from all analysis
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

# UIO reference year for proxy (used when requested year absent from workbook)
UIO_PROXY_YEAR = 2025
UIO_AVAILABLE_YEARS = list(range(2020, 2027))


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


def load_uio_detail_from_excel(filepath: str) -> pd.DataFrame:
    """
    Load UIO by distributor × year × model row (sheet '1.UIO Overview').

    Supports v17 (header row 6) and v18+ (header row 5, 2025E–2030F columns).

    Columns: distributor_code, year, uio_units, cv_lcv, model
    """
    import re

    import openpyxl

    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb["1.UIO Overview"]
    all_rows = list(ws.iter_rows(values_only=True))
    wb.close()

    header_idx = next(
        i for i, r in enumerate(all_rows) if r[0] is not None and "Ctry" in str(r[0])
    )
    header_row = all_rows[header_idx]
    year_cols: dict[int, int] = {}
    for i, h in enumerate(header_row):
        if h is None:
            continue
        m = re.match(r"^\s*(\d{4})[EF]?\s*$", str(h).strip())
        if m:
            yr = int(m.group(1))
            if yr in UIO_AVAILABLE_YEARS:
                year_cols[yr] = i

    rows = []
    for row in all_rows[header_idx + 1 : header_idx + 500]:
        if row[0] is None:
            continue
        dist_v13 = str(row[5]).strip() if row[5] else ""
        if not dist_v13 or dist_v13 == "None":
            continue
        if "MIDI" in dist_v13.upper():
            continue

        dist_code = V13_DIST_TO_CODE.get(dist_v13)
        if not dist_code:
            continue

        cv_lcv = str(row[2]).strip() if row[2] else ""
        model = str(row[3]).strip() if row[3] else ""

        if dist_code in SEGMENT_ONLY:
            if cv_lcv != SEGMENT_ONLY[dist_code]:
                continue

        for yr, col_idx in year_cols.items():
            val = row[col_idx]
            if val is not None:
                rows.append(
                    {
                        "distributor_code": dist_code,
                        "year": yr,
                        "uio_units": int(val),
                        "cv_lcv": cv_lcv,
                        "model": model,
                    }
                )

    df = pd.DataFrame(rows)
    if not df.empty:
        print(
            f"[data_prep] UIO detail: {len(df):,} rows | "
            f"{df['distributor_code'].nunique()} distributors"
        )
    return df


def load_uio_from_excel(filepath: str) -> pd.DataFrame:
    """
    Load multi-year UIO totals (sum of model rows per distributor × year).

    UIO available: 2020–2024 (actual). 2025+ uses proxy logic in gps_engine.
    """
    df = load_uio_detail_from_excel(filepath)
    if df.empty:
        return df

    df_agg = (
        df.groupby(["distributor_code", "year"])
        .agg(uio_units=("uio_units", "sum"))
        .reset_index()
    )
    print(
        f"[data_prep] UIO loaded: {len(df_agg)} distributor×year combos | "
        f"distributors: {sorted(df_agg['distributor_code'].unique())}"
    )
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
    # Case-insensitive alias keys
    for name, code in list(base_map.items()):
        if isinstance(name, str):
            base_map[name.strip().upper()] = code
    return base_map


def _normalize_sold_to_key(val) -> str:
    if pd.isna(val):
        return ""
    s = str(val).strip()
    if s.endswith(".0") and s[:-2].isdigit():
        s = s[:-2]
    return s


def _is_sap_numeric(val) -> bool:
    s = _normalize_sold_to_key(val)
    return s.isdigit() and len(s) >= 3


def load_sap_sold_to_mapping(filepath: str | None = None) -> pd.DataFrame:
    """Load SAP sold-to pt → name / distributor_code table."""
    from pathlib import Path

    if filepath is None:
        filepath = str(Path(__file__).resolve().parent.parent / "data" / "sap_sold_to_mapping.csv")
    path = Path(filepath)
    if not path.exists():
        return pd.DataFrame(columns=["sap_sold_to_pt", "sold_to_name", "distributor_code"])
    df = pd.read_csv(path)
    df["sap_sold_to_pt"] = pd.to_numeric(df["sap_sold_to_pt"], errors="coerce").astype("Int64")
    return df


def _sap_to_code_lookup() -> dict[int, str]:
    """CSV first, then hardcoded overrides (UTI 1799 / IUK 2574 / ITUK 2575)."""
    sap_to_code: dict[int, str] = {}
    sap_df = load_sap_sold_to_mapping()
    if not sap_df.empty:
        for _, row in sap_df.iterrows():
            sap = row["sap_sold_to_pt"]
            if pd.isna(sap):
                continue
            code = str(row.get("distributor_code") or "").strip()
            if code:
                sap_to_code[int(sap)] = code
    sap_to_code.update(SAP_SOLD_TO_OVERRIDES)
    return sap_to_code


def apply_distributor_codes(df: pd.DataFrame, df_mapping: pd.DataFrame) -> pd.DataFrame:
    """
    Map billing rows → distributor_code.

    Order:
      1. ``sold_to_sap`` (SAP sold-to pt) via sap_sold_to_mapping + overrides
      2. ``sold_to`` legal name
      3. ``sold_to`` as a SAP number **only when sold_to_sap is missing**

    Never treat a ship-to / payer short code in ``sold_to`` as the account when
    ``sold_to_sap`` is present (IUK 89 vs 2574, ITUK 2194 vs 2575, UTI 1797 vs 1799).
    """
    name_to_code = build_name_to_code_map(df_mapping)
    sap_to_code = _sap_to_code_lookup()

    out = df.copy()
    codes = pd.Series(pd.NA, index=out.index, dtype="object")

    sap_num = None
    if "sold_to_sap" in out.columns:
        sap_num = pd.to_numeric(out["sold_to_sap"], errors="coerce")
        sap_ids = sap_num.dropna().astype(int)
        codes.loc[sap_ids.index] = sap_ids.map(sap_to_code)

    sold_keys = (
        out["sold_to"].map(_normalize_sold_to_key)
        if "sold_to" in out.columns
        else pd.Series("", index=out.index)
    )

    def _name_code(key: str):
        if not key or key.lower() in ("nan", "none", "<na>"):
            return None
        return name_to_code.get(key) or name_to_code.get(key.upper())

    need_name = codes.isna()
    if need_name.any():
        codes.loc[need_name] = sold_keys.loc[need_name].map(_name_code)

    # Numeric sold_to as SAP id only if sold_to_sap was blank — otherwise 89/2194/1797
    # would steal IUK / ITUK / UTI rows.
    need_num = codes.isna()
    if sap_num is not None:
        need_num = need_num & sap_num.isna()
    is_num = sold_keys.map(_is_sap_numeric)
    need_num = need_num & is_num
    if need_num.any():
        extra = pd.to_numeric(sold_keys.loc[need_num], errors="coerce").dropna().astype(int)
        codes.loc[extra.index] = extra.map(sap_to_code)

    out["distributor_code"] = codes
    unmapped = out["distributor_code"].isna()
    if unmapped.any():
        sample_sold = out.loc[unmapped, "sold_to"].astype(str).unique()[:8].tolist() if "sold_to" in out.columns else []
        sample_sap = (
            out.loc[unmapped, "sold_to_sap"].dropna().astype(str).unique()[:8].tolist()
            if "sold_to_sap" in out.columns
            else []
        )
        print(
            f"[data_prep] WARNING: {unmapped.sum():,} rows unmapped "
            f"(sold_to sample {sample_sold}; sold_to_sap sample {sample_sap})"
        )
        out.loc[unmapped, "distributor_code"] = "UNMAPPED"
    return out


def ensure_sales_part_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Guarantee part_number + description for GPS/PMS engines.

    CY parquet may expose ``material`` only; legacy TSV uses ``part_number``.
    """
    df = df.copy()
    if "part_number" not in df.columns:
        for src in ("material", "Material"):
            if src in df.columns:
                df["part_number"] = df[src]
                break
    if "part_number" in df.columns:
        pn = df["part_number"]
        num = pd.to_numeric(pn, errors="coerce")

        def _pn_str(i: int) -> str:
            v, raw = num.iloc[i], pn.iloc[i]
            if pd.notna(v):
                try:
                    return str(int(v))
                except (ValueError, OverflowError):
                    pass
            s = str(raw).strip() if pd.notna(raw) else ""
            return "" if s.lower() in ("nan", "none") else s

        df["part_number"] = [_pn_str(i) for i in range(len(df))]
        if "material" not in df.columns:
            df["material"] = df["part_number"]
    if "description" not in df.columns:
        for desc_col in ("Material Number", "Material Description", "Material description"):
            if desc_col in df.columns:
                df["description"] = df[desc_col]
                break
        else:
            df["description"] = ""
    else:
        df["description"] = df["description"].fillna("").astype(str)
    return df


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
    df = apply_distributor_codes(df, df_mapping)

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
    # Flag H: SaTy CR (credit) / RE (return) codes on positive-value lines — see
    # sales_loader._finish_sales_frame for the verified rationale.
    saty_col = df['saty'] if 'saty' in df.columns else pd.Series('', index=df.index)
    is_return_saty = saty_col.astype(str).str.strip().str.upper().isin(['CR', 'RE'])
    df['is_credit_note'] = (df['net_sales_value'] < 0) | is_return_saty

    df = ensure_sales_part_columns(df)

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
