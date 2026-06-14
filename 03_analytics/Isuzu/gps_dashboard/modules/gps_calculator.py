"""
Module 2: GPS & Spend-per-Unit Calculator
ISZE GPS & Spend per Unit Dashboard

Key changes vs V1:
  - UIO is now year-matched (2022 sales → 2022 UIO, 2023 → 2023 UIO, etc.)
  - ITUK/IUK and UTI/UMI correctly split by CV/LCV segment
  - 2025/2026 use 2024 UIO as proxy (flagged in outputs)

Spend/Unit formula:
    Spend/Unit = Net Sales EUR / UIO
    where UIO = year-matched fleet for this distributor's segment
"""

import pandas as pd
import numpy as np
from .data_prep import UIO_PROXY_YEAR, UIO_AVAILABLE_YEARS


def _get_uio_for_year(uio_lookup: dict, uio_proxy: dict, dist_code: str, year: int):
    """
    Return UIO for a given distributor and year.
    Uses actual UIO if year is in V13; falls back to 2024 proxy otherwise.
    Returns (uio_units, is_proxy).
    """
    if (dist_code, year) in uio_lookup:
        return uio_lookup[(dist_code, year)], False
    elif dist_code in uio_proxy:
        return uio_proxy[dist_code], True
    return None, None


def calculate_sales_by_distributor(
    df_sales: pd.DataFrame,
    year: int = None,
    year_type: str = "calendar",
    include_credit_notes: bool = True,
) -> pd.DataFrame:
    """Aggregate net sales by distributor for a given period."""
    df = df_sales.copy()
    if year is not None:
        col = 'fiscal_year' if year_type == "fiscal" else 'year'
        df = df[df[col] == year]
    if not include_credit_notes:
        df = df[~df['is_credit_note']]

    result = (
        df.groupby('distributor_code')
        .agg(
            total_sales_eur=('net_sales_value', 'sum'),
            total_qty=('billed_qty', 'sum'),
            invoice_lines=('net_sales_value', 'count'),
            credit_notes_eur=('net_sales_value', lambda x: x[x < 0].sum()),
        )
        .reset_index()
    )
    result['period'] = (f"FY{year}" if year_type == "fiscal" else str(year)) if year else "ALL"
    result['year_type'] = year_type
    return result.sort_values('total_sales_eur', ascending=False)


def calculate_spend_per_unit(
    df_sales: pd.DataFrame,
    df_uio: pd.DataFrame,
    df_metadata: pd.DataFrame,
    year: int = None,
    year_type: str = "calendar",
    include_credit_notes: bool = True,
) -> pd.DataFrame:
    """
    Calculate spend per unit by distributor.

    UIO matching:
      - Uses year-matched UIO from V13 when available (2020–2024)
      - Uses 2024 UIO as proxy for 2025/2026 (flagged as uio_proxy=True)
      - ITUK/IUK/UTI/UMI each use their own segment UIO (not combined UK/Israel total)

    Returns:
        distributor_code | country | region | total_sales_eur | uio_units |
        spend_per_unit_eur | uio_year | uio_proxy
    """
    from .data_prep import build_uio_lookup
    uio_lookup, uio_proxy = build_uio_lookup(df_uio)

    # ── Sales aggregation ───────────────────────────────────────────────────
    df_agg = calculate_sales_by_distributor(df_sales, year=year, year_type=year_type,
                                             include_credit_notes=include_credit_notes)

    # ── UIO year to use ─────────────────────────────────────────────────────
    # For fiscal year: use the start year's UIO (e.g., FY2024 → Apr 2024 → UIO 2024)
    # For calendar year: use the exact year
    uio_year = year if year is not None else UIO_PROXY_YEAR
    if year_type == "fiscal":
        uio_year = year  # FY2024 → UIO 2024

    # ── Attach UIO and metadata ─────────────────────────────────────────────
    records = []
    for _, row in df_agg.iterrows():
        dist = row['distributor_code']
        uio_val, is_proxy = _get_uio_for_year(uio_lookup, uio_proxy, dist, uio_year)

        # Get metadata
        meta = df_metadata[df_metadata['distributor_code'] == dist]
        country = meta['country'].values[0] if not meta.empty else ''
        region = meta['region'].values[0] if not meta.empty else ''

        spu = row['total_sales_eur'] / uio_val if (uio_val and uio_val > 0) else np.nan

        records.append({
            **row.to_dict(),
            'country': country,
            'region': region,
            'uio_units': uio_val if uio_val else 0,
            'spend_per_unit_eur': spu,
            'uio_year': UIO_PROXY_YEAR if is_proxy else uio_year,
            'uio_proxy': bool(is_proxy),
            'uio_available': uio_val is not None and uio_val > 0,
        })

    return pd.DataFrame(records).sort_values('spend_per_unit_eur', ascending=False, na_position='last')


def calculate_multiyear_trends(
    df_sales: pd.DataFrame,
    df_uio: pd.DataFrame,
    df_metadata: pd.DataFrame,
    year_type: str = "calendar",
) -> pd.DataFrame:
    """
    Year-on-year spend/unit for all distributors.

    For each year in the sales data, uses the matching UIO year.
    2025/2026 use 2024 UIO proxy (flagged).
    """
    col = 'fiscal_year' if year_type == "fiscal" else 'year'
    years = sorted(df_sales[col].dropna().unique().astype(int))

    results = []
    for yr in years:
        df_yr = calculate_spend_per_unit(df_sales, df_uio, df_metadata,
                                          year=int(yr), year_type=year_type)
        df_yr['year_value'] = int(yr)
        results.append(df_yr)

    if not results:
        return pd.DataFrame()

    df_trend = pd.concat(results, ignore_index=True)
    return df_trend[[
        'distributor_code', 'country', 'region', 'year_value', 'period',
        'total_sales_eur', 'uio_units', 'spend_per_unit_eur', 'uio_year', 'uio_proxy'
    ]].sort_values(['distributor_code', 'year_value'])


def calculate_monthly_sales(
    df_sales: pd.DataFrame,
    distributor_codes: list = None,
    year_type: str = "calendar",
) -> pd.DataFrame:
    """Monthly sales aggregation for trend charts."""
    df = df_sales.copy()
    if distributor_codes:
        df = df[df['distributor_code'].isin(distributor_codes)]
    col = 'fiscal_year' if year_type == "fiscal" else 'year'
    result = (
        df.groupby([col, 'month', 'distributor_code'])
        .agg(net_sales_eur=('net_sales_value', 'sum'), qty=('billed_qty', 'sum'))
        .reset_index()
        .rename(columns={col: 'year_value'})
    )
    result['year_month'] = pd.to_datetime(
        result['year_value'].astype(str) + '-' + result['month'].astype(str).str.zfill(2) + '-01'
    )
    return result.sort_values(['distributor_code', 'year_month'])


def get_top_parts(
    df_sales: pd.DataFrame,
    year: int = None,
    year_type: str = "calendar",
    distributor_code: str = None,
    top_n: int = 20,
) -> pd.DataFrame:
    """Top N parts by revenue for a given year/distributor."""
    df = df_sales.copy()
    if year:
        col = 'fiscal_year' if year_type == "fiscal" else 'year'
        df = df[df[col] == year]
    if distributor_code:
        df = df[df['distributor_code'] == distributor_code]
    result = (
        df.groupby(['part_number', 'description'])
        .agg(
            total_sales_eur=('net_sales_value', 'sum'),
            total_qty=('billed_qty', 'sum'),
            n_distributors=('distributor_code', 'nunique'),
        )
        .reset_index()
        .sort_values('total_sales_eur', ascending=False)
        .head(top_n)
    )
    result['rank'] = range(1, len(result) + 1)
    return result


def get_summary_kpis(
    df_spu: pd.DataFrame,
) -> dict:
    """High-level KPIs from an already-calculated spend/unit DataFrame."""
    df_with_uio = df_spu[df_spu['uio_available']] if 'uio_available' in df_spu.columns \
                  else df_spu[df_spu['uio_units'] > 0]
    return {
        "total_sales_eur": df_spu['total_sales_eur'].sum(),
        "n_distributors": df_spu['distributor_code'].nunique(),
        "n_with_uio": len(df_with_uio),
        "avg_spend_per_unit": df_with_uio['spend_per_unit_eur'].mean() if not df_with_uio.empty else 0,
        "max_spend_per_unit": df_with_uio['spend_per_unit_eur'].max() if not df_with_uio.empty else 0,
        "top_dist": df_with_uio.loc[df_with_uio['spend_per_unit_eur'].idxmax(), 'distributor_code']
                    if not df_with_uio.empty else "—",
        "n_proxy": int(df_spu.get('uio_proxy', pd.Series(False)).sum()),
    }
