"""
PRISM Data Hierarchy — Layer 2A: GPS (Genuine Parts Share / Spend per Unit)
============================================================================
GPS answers: "How much of the available parts wallet are we capturing per truck?"

Formula:   Net Sales EUR / UIO = EUR per truck per year (Spend per Unit)
Depends on: UIO (Layer 1) as denominator — GPS is meaningless without accurate UIO
Granularity: Distributor x year (macro view across all parts)

Thresholds:
  >EUR 150 / year / truck  — healthy capture
  EUR 50-150               — at risk
  <EUR 50                  — critical underperformance

Source: ISZE net sales data (ERP/SAP export, monthly refresh)
Refinements (May 2026): warranty exclusion, segment split, age weighting, PDI flag
"""

# Module: GPS Engine
# PRISM — Parts Revenue Intelligence & Sales Monitor
#
# GPS = Genuine Parts Share / Spend per Unit
# Core calculation: Net Sales EUR / UIO (Units in Operation)
#
# Migrated from gps_dashboard/modules/gps_calculator.py.
# Dependencies on data_prep.build_uio_lookup have been inlined here
# so this module has no dependency on the old gps_dashboard package.

import pandas as pd
import numpy as np

# Strategic spend/unit target (traffic-light mid threshold = 100% GPS)
GPS_TARGET_EUR_PER_UNIT = 150.0
GPS_AMBER_EUR_PER_UNIT = 50.0

# Year used as UIO proxy when actual data is unavailable (sync with data_prep)
from modules.data_prep import UIO_PROXY_YEAR  # noqa: E402


def build_uio_lookup(df_uio: pd.DataFrame) -> tuple[dict, dict]:
    """
    Build two lookup structures from a UIO DataFrame.

    Expected columns (after normalisation by uio_loader):
        distributor_code, year, uio_units
        (additional columns are ignored)

    Returns
    -------
    uio_lookup : dict
        {(distributor_code, year): uio_units}
    uio_proxy : dict
        {distributor_code: uio_units} — UIO_PROXY_YEAR values for fallback
    """
    uio_lookup: dict = {}
    uio_proxy: dict = {}

    if df_uio.empty:
        return uio_lookup, uio_proxy

    required = {"distributor_code", "year", "uio_units"}
    missing = required - set(df_uio.columns)
    if missing:
        import warnings
        warnings.warn(
            f"UIO DataFrame is missing columns: {missing}. "
            "Returning empty lookups.",
            stacklevel=2,
        )
        return uio_lookup, uio_proxy

    for _, row in df_uio.iterrows():
        dist = str(row["distributor_code"]).strip()
        try:
            year = int(row["year"])
            units = float(row["uio_units"])
        except (ValueError, TypeError):
            continue
        uio_lookup[(dist, year)] = units
        if year == UIO_PROXY_YEAR:
            uio_proxy[dist] = units

    return uio_lookup, uio_proxy


def _get_uio_for_year(
    uio_lookup: dict,
    uio_proxy: dict,
    dist_code: str,
    year: int,
) -> tuple:
    """
    Return (uio_units, is_proxy) for a distributor/year combination.
    Falls back to UIO_PROXY_YEAR when the requested year is absent.
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
    exclude_warranty: bool = False,
) -> pd.DataFrame:
    """Aggregate net sales by distributor for a given period.

    Parameters
    ----------
    exclude_warranty : bool, default False
        When True, filters out warranty credit notes before aggregation.
        Warranty rows are identified by:
          - net_sales_value < 0 AND billed_qty <= 0, OR
          - description column contains "WARRANTY" or "WARRANT" (case-insensitive)
        A ``warranty_credits_eur`` column is added showing the sum of the
        excluded warranty rows per distributor.
    """
    df = df_sales.copy()
    # Flag A: drop freight / rebate / finance / adjustment lines — not parts revenue.
    if "line_kind" in df.columns:
        df = df[df["line_kind"] == "part"]
    if year is not None:
        col = "fiscal_year" if year_type == "fiscal" else "year"
        df = df[df[col] == year]
    if not include_credit_notes:
        df = df[~df["is_credit_note"]]

    # --- warranty exclusion ------------------------------------------------
    warranty_mask = pd.Series(False, index=df.index)
    if exclude_warranty:
        qty_col = "billed_qty" if "billed_qty" in df.columns else None
        if qty_col:
            warranty_mask |= (df["net_sales_value"] < 0) & (df[qty_col] <= 0)
        if "description" in df.columns:
            desc_upper = df["description"].fillna("").str.upper()
            warranty_mask |= desc_upper.str.contains("WARRANT", na=False)

    df_warranty = df[warranty_mask]
    df = df[~warranty_mask]
    # -----------------------------------------------------------------------

    result = (
        df.groupby("distributor_code")
        .agg(
            total_sales_eur=("net_sales_value", "sum"),
            total_qty=("billed_qty", "sum"),
            invoice_lines=("net_sales_value", "count"),
            credit_notes_eur=("net_sales_value", lambda x: x[x < 0].sum()),
        )
        .reset_index()
    )

    if exclude_warranty and not df_warranty.empty:
        warranty_agg = (
            df_warranty.groupby("distributor_code")["net_sales_value"]
            .sum()
            .reset_index()
            .rename(columns={"net_sales_value": "warranty_credits_eur"})
        )
        result = result.merge(warranty_agg, on="distributor_code", how="left")
        result["warranty_credits_eur"] = result["warranty_credits_eur"].fillna(0.0)
    else:
        result["warranty_credits_eur"] = 0.0

    result["period"] = (
        (f"FY{year}" if year_type == "fiscal" else str(year)) if year else "ALL"
    )
    result["year_type"] = year_type
    return result.sort_values("total_sales_eur", ascending=False)


def calculate_spend_per_unit(
    df_sales: pd.DataFrame,
    df_uio: pd.DataFrame,
    df_metadata: pd.DataFrame,
    year: int = None,
    year_type: str = "calendar",
    include_credit_notes: bool = True,
    exclude_warranty: bool = False,
) -> pd.DataFrame:
    """
    Calculate spend per unit (GPS metric) by distributor.

    UIO matching:
      - Uses year-matched UIO when available
      - Falls back to UIO_PROXY_YEAR (2024) for later years
      - Each distributor uses its own segment UIO (not a combined total)

    Parameters
    ----------
    exclude_warranty : bool, default False
        Passed through to calculate_sales_by_distributor. When True, warranty
        credit notes are excluded from net_sales_eur and a ``warranty_credits_eur``
        column is carried through to the output.

    Returns
    -------
    DataFrame with columns:
        distributor_code | country | region | total_sales_eur | uio_units |
        spend_per_unit_eur | uio_year | uio_proxy
        (+ warranty_credits_eur when exclude_warranty=True)
    """
    uio_lookup, uio_proxy = build_uio_lookup(df_uio)

    df_agg = calculate_sales_by_distributor(
        df_sales, year=year, year_type=year_type,
        include_credit_notes=include_credit_notes,
        exclude_warranty=exclude_warranty,
    )

    uio_year = year if year is not None else UIO_PROXY_YEAR
    if year_type == "fiscal":
        uio_year = year  # FY2024 → UIO 2024

    records = []
    for _, row in df_agg.iterrows():
        dist = row["distributor_code"]
        uio_val, is_proxy = _get_uio_for_year(uio_lookup, uio_proxy, dist, uio_year)

        meta = df_metadata[df_metadata["distributor_code"] == dist]
        country = meta["country"].values[0] if not meta.empty else ""
        region = meta["region"].values[0] if not meta.empty else ""

        spu = row["total_sales_eur"] / uio_val if (uio_val and uio_val > 0) else np.nan

        records.append({
            **row.to_dict(),
            "country": country,
            "region": region,
            "uio_units": uio_val if uio_val else 0,
            "spend_per_unit_eur": spu,
            "uio_year": UIO_PROXY_YEAR if is_proxy else uio_year,
            "uio_proxy": bool(is_proxy),
            "uio_available": uio_val is not None and uio_val > 0,
        })

    return pd.DataFrame(records).sort_values(
        "spend_per_unit_eur", ascending=False, na_position="last"
    )


def _uio_detail_for_year(
    df_uio_detail: pd.DataFrame,
    distributor_code: str,
    uio_year: int,
) -> tuple[pd.DataFrame, bool]:
    """Return model-level UIO rows for a year; proxy from UIO_PROXY_YEAR when missing."""
    dist = distributor_code
    actual = df_uio_detail[
        (df_uio_detail["distributor_code"] == dist)
        & (df_uio_detail["year"] == uio_year)
    ]
    if not actual.empty:
        return actual.copy(), False
    proxy = df_uio_detail[
        (df_uio_detail["distributor_code"] == dist)
        & (df_uio_detail["year"] == UIO_PROXY_YEAR)
    ]
    if proxy.empty:
        return pd.DataFrame(), True
    out = proxy.copy()
    out["year"] = uio_year
    return out, True


def calculate_model_weighted_gps(
    df_sales: pd.DataFrame,
    df_uio_detail: pd.DataFrame,
    df_metadata: pd.DataFrame,
    year: int,
    year_type: str = "calendar",
    targets: dict[str, float] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    GPS % using per-model €/vehicle targets weighted by UIO mix.

    GPS % = total_sales / sum(uio_model × target_model) × 100

    Returns (summary_by_distributor, model_breakdown_rows).
    """
    from modules.gps_model_targets import map_uio_row_to_model_group, targets_by_group

    if targets is None:
        targets = targets_by_group()

    uio_year = year if year_type != "fiscal" else year
    df_agg = calculate_sales_by_distributor(
        df_sales, year=year, year_type=year_type, include_credit_notes=True
    )

    summary_rows = []
    breakdown_rows = []

    for _, row in df_agg.iterrows():
        dist = row["distributor_code"]
        sales = float(row["total_sales_eur"])
        uio_rows, is_proxy = _uio_detail_for_year(df_uio_detail, dist, uio_year)

        meta = df_metadata[df_metadata["distributor_code"] == dist]
        country = meta["country"].values[0] if not meta.empty else ""
        region = meta["region"].values[0] if not meta.empty else ""

        if uio_rows.empty:
            summary_rows.append(
                {
                    **row.to_dict(),
                    "country": country,
                    "region": region,
                    "uio_units": 0,
                    "target_wallet_eur": np.nan,
                    "weighted_target_spu": np.nan,
                    "spend_per_unit_eur": np.nan,
                    "gps_pct": np.nan,
                    "uio_year": uio_year,
                    "uio_proxy": is_proxy,
                }
            )
            continue

        uio_rows = uio_rows.copy()
        uio_rows["model_group"] = uio_rows.apply(
            lambda r: map_uio_row_to_model_group(r["model"], r["cv_lcv"]), axis=1
        )
        def _target_for_group(group: str, seg: str) -> float:
            if group in targets:
                return float(targets[group])
            seg_u = str(seg).strip().upper()
            if group == "Other_LCV" or seg_u == "LCV":
                return float(targets.get("LCV_D_Max", 250))
            # Was hardcoded 1120 — the same wrong figure the docstring carried. Now uses the
            # loaded rate so the fallback cannot disagree with the CSV.
            return float(targets.get("N75_N50_N62", 739))

        uio_rows["target_eur"] = uio_rows.apply(
            lambda r: _target_for_group(r["model_group"], r["cv_lcv"]), axis=1
        )
        uio_rows["target_wallet_eur"] = uio_rows["uio_units"] * uio_rows["target_eur"]

        target_wallet = float(uio_rows["target_wallet_eur"].sum())
        uio_total = int(uio_rows["uio_units"].sum())
        weighted_spu = target_wallet / uio_total if uio_total > 0 else np.nan
        actual_spu = sales / uio_total if uio_total > 0 else np.nan
        # ITUK Parts Sales Target Study row 38: Actual ÷ TTL target wallet × 100
        gps_pct = (sales / target_wallet * 100) if target_wallet > 0 else np.nan

        mix = (
            uio_rows.groupby("model_group")["target_wallet_eur"]
            .sum()
            .div(target_wallet)
            .mul(100)
            if target_wallet > 0
            else pd.Series(dtype=float)
        )

        for _, urow in uio_rows.iterrows():
            alloc = (
                sales * (int(urow["uio_units"]) / uio_total) if uio_total > 0 else 0.0
            )
            tw = float(urow["target_wallet_eur"])
            breakdown_rows.append(
                {
                    "distributor_code": dist,
                    "year": year,
                    "model": urow["model"],
                    "cv_lcv": urow["cv_lcv"],
                    "model_group": urow["model_group"],
                    "uio_units": int(urow["uio_units"]),
                    "target_eur_per_vehicle": float(urow["target_eur"]),
                    "target_wallet_eur": tw,
                    "allocated_sales_eur": alloc,
                    "gps_pct_model": (alloc / tw * 100) if tw > 0 else np.nan,
                    "uio_proxy": is_proxy,
                }
            )

        summary_rows.append(
            {
                **row.to_dict(),
                "country": country,
                "region": region,
                "uio_units": uio_total,
                "target_wallet_eur": target_wallet,
                "weighted_target_spu": weighted_spu,
                "spend_per_unit_eur": actual_spu,
                "gps_pct": gps_pct,
                "wallet_mix_n75_pct": float(mix.get("N75_N50_N62", 0) or 0),
                "wallet_mix_f_pct": float(mix.get("F_Series_MD", 0) or 0),
                "wallet_mix_lcv_pct": float(mix.get("LCV_D_Max", 0) or 0),
                "uio_year": UIO_PROXY_YEAR if is_proxy else uio_year,
                "uio_proxy": is_proxy,
            }
        )

    df_summary = pd.DataFrame(summary_rows)
    df_breakdown = pd.DataFrame(breakdown_rows)
    return df_summary, df_breakdown


def calculate_model_weighted_multiyear_trends(
    df_sales: pd.DataFrame,
    df_uio_detail: pd.DataFrame,
    df_metadata: pd.DataFrame,
    year_type: str = "calendar",
    targets: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Year-on-year model-weighted GPS % for all distributors."""
    col = "fiscal_year" if year_type == "fiscal" else "year"
    years = sorted(df_sales[col].dropna().unique().astype(int))
    frames = []
    for yr in years:
        df_yr, _ = calculate_model_weighted_gps(
            df_sales,
            df_uio_detail,
            df_metadata,
            year=int(yr),
            year_type=year_type,
            targets=targets,
        )
        if df_yr.empty:
            continue
        df_yr["year_value"] = int(yr)
        frames.append(df_yr)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).sort_values(
        ["distributor_code", "year_value"]
    )


def add_gps_pct_of_target(
    df: pd.DataFrame,
    target_eur: float = GPS_TARGET_EUR_PER_UNIT,
) -> pd.DataFrame:
    """
    GPS % vs flat €/vehicle target (legacy traffic-light benchmark).

    Prefer calculate_model_weighted_gps when per-model targets apply.
    """
    out = df.copy()
    has_uio = out["uio_units"] > 0 if "uio_units" in out.columns else False
    out["gps_pct"] = np.where(
        out["spend_per_unit_eur"].notna() & has_uio,
        (out["spend_per_unit_eur"] / target_eur) * 100,
        np.nan,
    )
    return out


def calculate_multiyear_trends(
    df_sales: pd.DataFrame,
    df_uio: pd.DataFrame,
    df_metadata: pd.DataFrame,
    year_type: str = "calendar",
) -> pd.DataFrame:
    """
    Year-on-year spend/unit for all distributors.

    For each year in the sales data, uses the matching UIO year.
    Years beyond UIO data range use the proxy year (flagged).
    """
    col = "fiscal_year" if year_type == "fiscal" else "year"
    years = sorted(df_sales[col].dropna().unique().astype(int))

    results = []
    for yr in years:
        df_yr = calculate_spend_per_unit(
            df_sales, df_uio, df_metadata,
            year=int(yr), year_type=year_type,
        )
        df_yr["year_value"] = int(yr)
        results.append(df_yr)

    if not results:
        return pd.DataFrame()

    df_trend = pd.concat(results, ignore_index=True)
    df_trend = df_trend[[
        "distributor_code", "country", "region", "year_value", "period",
        "total_sales_eur", "uio_units", "spend_per_unit_eur", "uio_year", "uio_proxy",
    ]].sort_values(["distributor_code", "year_value"])
    return add_gps_pct_of_target(df_trend)


def calculate_monthly_sales(
    df_sales: pd.DataFrame,
    distributor_codes: list = None,
    year_type: str = "calendar",
) -> pd.DataFrame:
    """Monthly sales aggregation for trend charts."""
    df = df_sales.copy()
    if distributor_codes:
        df = df[df["distributor_code"].isin(distributor_codes)]
    col = "fiscal_year" if year_type == "fiscal" else "year"
    result = (
        df.groupby([col, "month", "distributor_code"])
        .agg(net_sales_eur=("net_sales_value", "sum"), qty=("billed_qty", "sum"))
        .reset_index()
        .rename(columns={col: "year_value"})
    )
    result["year_month"] = pd.to_datetime(
        result["year_value"].astype(str)
        + "-"
        + result["month"].astype(str).str.zfill(2)
        + "-01"
    )
    return result.sort_values(["distributor_code", "year_month"])


def get_top_parts(
    df_sales: pd.DataFrame,
    year: int = None,
    year_type: str = "calendar",
    distributor_code: str = None,
    top_n: int = 20,
) -> pd.DataFrame:
    """Top N parts by revenue for a given year/distributor."""
    df = df_sales.copy()
    # Flag A: exclude freight / rebate / finance lines from the parts ranking.
    if "line_kind" in df.columns:
        df = df[df["line_kind"] == "part"]
    if year:
        col = "fiscal_year" if year_type == "fiscal" else "year"
        df = df[df[col] == year]
    if distributor_code:
        df = df[df["distributor_code"] == distributor_code]
    result = (
        df.groupby(["part_number", "description"])
        .agg(
            total_sales_eur=("net_sales_value", "sum"),
            total_qty=("billed_qty", "sum"),
            n_distributors=("distributor_code", "nunique"),
        )
        .reset_index()
        .sort_values("total_sales_eur", ascending=False)
        .head(top_n)
    )
    result["rank"] = range(1, len(result) + 1)
    return result


def calculate_spend_per_unit_by_segment(
    df_sales: pd.DataFrame,
    df_uio: pd.DataFrame,
    df_metadata: pd.DataFrame,
    year: int = None,
    year_type: str = "calendar",
) -> pd.DataFrame:
    """
    Spend-per-unit broken down by segment (CV / LCV) and parent market.

    Calls ``calculate_spend_per_unit`` then enriches the result with
    ``segment`` and ``parent_market`` columns derived from df_metadata.

    Expected metadata columns: distributor_code, segment_cv, segment_lcv
    (boolean or truthy/falsy).  Distributors that belong to a shared country
    group are assigned the same ``parent_market`` label (e.g. "UK" for ITUK
    and IUK).

    Returns
    -------
    Same columns as calculate_spend_per_unit plus:
        segment       — "CV", "LCV", or "TOTAL" (when no segment split exists)
        parent_market — country-level grouping label; equals ``country`` when
                        there is only one distributor for that country.
    """
    df_spu = calculate_spend_per_unit(
        df_sales, df_uio, df_metadata, year=year, year_type=year_type,
    )

    # Determine segment for each distributor from metadata
    def _resolve_segment(dist_code: str) -> str:
        meta = df_metadata[df_metadata["distributor_code"] == dist_code]
        if meta.empty:
            return "TOTAL"
        row = meta.iloc[0]
        has_cv = bool(row.get("segment_cv", False))
        has_lcv = bool(row.get("segment_lcv", False))
        if has_cv and not has_lcv:
            return "CV"
        if has_lcv and not has_cv:
            return "LCV"
        return "TOTAL"

    df_spu["segment"] = df_spu["distributor_code"].apply(_resolve_segment)

    # Build parent_market: group distributors that share the same country
    # and have distinct segments (i.e. a CV+LCV split exists for that country)
    country_dist_counts = df_spu.groupby("country")["distributor_code"].transform("nunique")
    country_segment_counts = df_spu.groupby("country")["segment"].transform("nunique")

    # A "split" market is one with >=2 distributors AND >=2 distinct segments
    is_split = (country_dist_counts >= 2) & (country_segment_counts >= 2)
    df_spu["parent_market"] = df_spu["country"]
    # For split markets, parent_market stays as the country (already set above);
    # the two rows for that country naturally represent CV and LCV sub-markets.

    _ = is_split  # used implicitly via the country column; kept for clarity

    return df_spu.sort_values(
        ["parent_market", "segment", "spend_per_unit_eur"],
        ascending=[True, True, False],
        na_position="last",
    )


def weight_uio_by_age(
    df_uio: pd.DataFrame,
    reference_year: int,
    peak_age_years: int = 5,
    decay_factor: float = 0.85,
) -> pd.DataFrame:
    """
    Apply age-based weighting to UIO units.

    Reflects that service-parts demand peaks in years 1-5, decays through
    years 6-10, and falls to a low-capture floor beyond 10 years.

    Parameters
    ----------
    df_uio : pd.DataFrame
        Must contain columns: distributor_code, year (registration year),
        uio_units.
    reference_year : int
        The year from which vehicle age is measured (typically current year).
    peak_age_years : int, default 5
        Age up to which weight = 1.0 (full capture).
    decay_factor : float, default 0.85
        Geometric decay rate applied per year beyond peak_age_years.
        e.g. age 6 → 0.85^1, age 7 → 0.85^2, …

    Returns
    -------
    Input DataFrame with an additional ``age_weighted_uio`` column.
    Rows where ``year`` is missing or non-numeric are assigned weight 1.0.

    Notes
    -----
    This is a pure utility helper and does NOT modify the main SPU calculation.
    """
    df = df_uio.copy()

    def _weight(reg_year) -> float:
        try:
            age = int(reference_year) - int(reg_year)
        except (ValueError, TypeError):
            return 1.0
        if age <= peak_age_years:
            return 1.0
        if age <= 10:
            return decay_factor ** (age - peak_age_years)
        return 0.5

    df["age_weighted_uio"] = df.apply(
        lambda row: row["uio_units"] * _weight(row["year"]), axis=1
    )
    return df


def flag_pdi_parts(df_sales: pd.DataFrame) -> pd.DataFrame:
    """
    Add a boolean ``is_pdi`` column identifying Pre-Delivery Inspection parts.

    PDI parts are flagged when any of the following is true:
      - ``description`` contains "PDI", "PRE DELIVERY", "PREDELIVERY", or
        "ACCESSORY" (case-insensitive), OR
      - ``part_number`` starts with "PDI" (case-insensitive) after stripping
        leading zeros.

    PDI parts inflate GPS because they are one-time charges at vehicle
    delivery, not recurring service revenue.  Callers can use this flag to
    optionally exclude them before calling calculate_spend_per_unit.

    Returns
    -------
    Input DataFrame with ``is_pdi`` (bool) added.  Existing columns are
    unchanged.
    """
    df = df_sales.copy()

    pdi_desc_terms = ["PDI", "PRE DELIVERY", "PREDELIVERY", "ACCESSORY"]

    is_pdi = pd.Series(False, index=df.index)

    if "description" in df.columns:
        desc_upper = df["description"].fillna("").str.upper()
        for term in pdi_desc_terms:
            is_pdi |= desc_upper.str.contains(term, na=False)

    if "part_number" in df.columns:
        pn_stripped = (
            df["part_number"]
            .fillna("")
            .astype(str)
            .str.lstrip("0")
            .str.upper()
        )
        is_pdi |= pn_stripped.str.startswith("PDI")

    df["is_pdi"] = is_pdi
    return df


def get_summary_kpis(df_spu: pd.DataFrame) -> dict:
    """High-level KPIs from an already-calculated spend/unit DataFrame."""
    df_with_uio = (
        df_spu[df_spu["uio_available"]]
        if "uio_available" in df_spu.columns
        else df_spu[df_spu["uio_units"] > 0]
    )
    return {
        "total_sales_eur": df_spu["total_sales_eur"].sum(),
        "n_distributors": df_spu["distributor_code"].nunique(),
        "n_with_uio": len(df_with_uio),
        "avg_spend_per_unit": (
            df_with_uio["spend_per_unit_eur"].mean() if not df_with_uio.empty else 0
        ),
        "max_spend_per_unit": (
            df_with_uio["spend_per_unit_eur"].max() if not df_with_uio.empty else 0
        ),
        "top_dist": (
            df_with_uio.loc[
                df_with_uio["spend_per_unit_eur"].idxmax(), "distributor_code"
            ]
            if not df_with_uio.empty
            else "—"
        ),
        "n_proxy": int(df_spu.get("uio_proxy", pd.Series(False)).sum()),
    }
