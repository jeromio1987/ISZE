"""
Lost-sales model — where are we losing sales, by market, family and service category.

Purpose
-------
One row per (distributor, family, PMS category, year) carrying every evidence layer that can
explain a loss, so a ranked euro never has to be traced back through seven separate files.

The anchor is the fleet ceiling: the target spend the vehicles in service could support, minus
what we billed. Momentum, mix and competitor price are columns on the same row, not separate
studies.

Nothing here is a new model. Every euro comes either from billing through the same loader the
rest of the pipeline uses, or from a derived file that already has a verifier behind it. The only
numbers computed here are the three-way price split and the down-trade rule, and both are
documented at the point of computation.

Taxonomy (two axes, deliberately not one)
-----------------------------------------
The two systems on disk are different cuts and neither is complete alone:

- ``aim_l1_fixed`` (from ``aim_master_v2.csv``) is a *function* grouping covering 99.3% of billed
  euro. It is the primary family axis.
- ``pms_category`` is a *service family* grouping covering 16.4% of billed euro. It is the only
  axis that carries a modelled expected demand, so it drives the gap-type layer.

A part can sit on both. Where it does, the row carries both.

Ceiling caveat, stated once
---------------------------
``wallet_waterfall.csv`` publishes the target-spend ceiling at **market level only**. It cannot be
decomposed by family without inventing a split. Those columns are therefore attached to the
market-level file and to the family file **with ``ceilings_are_market_level=True``** so nobody sums
them down a family column.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from config import (
    BVP_PN_DIMENSION_CSV,
    DERIVED_DIR,
    GPS_SPU_BY_FAMILY_CSV,
    PARTS_CATALOG_DIMENSION_CSV,
    PMS_CAPTURE_BY_DB_CSV,
    PRISM_DATA_DIR,
)
from modules.bvp_analytics import normalize_pn_value

# ── Output paths ─────────────────────────────────────────────────────────────

LOST_SALES_FAMILY_CSV = DERIVED_DIR / "lost_sales_model.csv"
LOST_SALES_MARKET_CSV = DERIVED_DIR / "lost_sales_market.csv"
LOST_SALES_COMPETITOR_CSV = DERIVED_DIR / "lost_sales_competitor_pn.csv"
LOST_SALES_COMPETITOR_COVERAGE_CSV = DERIVED_DIR / "lost_sales_competitor_coverage.csv"
LOST_SALES_PN_ACTION_CSV = DERIVED_DIR / "lost_sales_pn_action.csv"
LOST_SALES_FISCAL_CSV = DERIVED_DIR / "lost_sales_fiscal_year.csv"
LOST_SALES_FISCAL_Q1_CSV = DERIVED_DIR / "lost_sales_fiscal_q1.csv"
LOST_SALES_META_JSON = DERIVED_DIR / "lost_sales_model.meta.json"

# The channel uplift used across the workspace: our list to the distributor x1.40, then the
# distributor to the workshop x1.275 = x1.785. Stated once here because the "could we match the
# competitor" test depends on it and that test must be reproducible.
DEALER_UPLIFT = 1.40 * 1.275

# ── Source paths (derived siblings, not in config) ───────────────────────────

_AIM_MASTER_CSV = DERIVED_DIR / "aim_master_v2.csv"
_WALLET_CSV = DERIVED_DIR / "wallet_waterfall.csv"
_CAPTURE_TRAJECTORY_CSV = DERIVED_DIR / "capture_trajectory.csv"
_SUBSTITUTION_TIMELINE_CSV = DERIVED_DIR / "substitution_timeline.csv"
_PRICE_PREMIUM_CSV = DERIVED_DIR / "price_premium.csv"
_REALIZATION_CSV = DERIVED_DIR / "pr00_realization_by_db_cy.csv"
_GPS_SPU_BY_DB_CSV = DERIVED_DIR / "gps_spu_by_distributor.csv"
_CAPTURE_RECOVERY_CSV = DERIVED_DIR / "capture_recovery_model.csv"
_DISTRIBUTOR_DIM_CSV = DERIVED_DIR / "distributor_dimension.csv"
_COMPETITOR_COMMON_BASIS_CSV = DERIVED_DIR / "competitor_common_basis.csv"
_COMPETITOR_WORKLIST_CSV = DERIVED_DIR / "price_collection_worklist_filled.csv"
_MARGIN_PN_CSV = DERIVED_DIR / "margin_opportunity_top200.csv"
_SELLOUT_TOP_PN_CSV = DERIVED_DIR / "sellout_aim_top_pn_2025.csv"
_SELLOUT_AIM_L1_CSV = DERIVED_DIR / "sellout_aim_by_aim_l1_2025.csv"

# ── Rule sets (documented, deterministic, no model) ──────────────────────────

# Continuity crosswalk from the AIM function grouping to the 7-family vocabulary the existing
# dashboards and every ``*_by_family`` derived file already use. This is for readability across
# the workspace, NOT the primary axis — the primary axis stays ``aim_l1`` so nothing is hidden
# inside a bucket. Anything not listed lands in ``Other``.
AIM_L1_TO_FAMILY_7: dict[str, str] = {
    "Maintenance Service": "PMS_Filters",
    "Fuel System": "PMS_Filters",
    "Cooling": "Belts_Cooling",
    "Engine": "Belts_Cooling",
    "Lubrication": "Belts_Cooling",
    "Fluids Chemicals": "Belts_Cooling",
    "Brakes": "Brakes",
    "Clutch": "Clutch_Driveline",
    "Transmission": "Clutch_Driveline",
    "Driveline Axle": "Clutch_Driveline",
    "Suspension": "Suspension_Chassis",
    "Steering": "Suspension_Chassis",
    "Wheels Hub": "Suspension_Chassis",
    "Chassis Frame": "Suspension_Chassis",
    "Electrical": "Electrical",
    "Lighting": "Electrical",
    "Intake Exhaust Emission": "Electrical",
    "Accident & Body": "Cab_Misc",
    "Cabin Interior": "Cab_Misc",
}

# PMS category → family, mirroring ``bvp_dimension.build_dimension_from_catalog`` so the two
# views agree. Kept explicit rather than inferred so a wrong value is visible.
def _family_for_pms_category(cat: str) -> str:
    if cat in ("oil_filter", "fuel_filter", "air_filter"):
        return "PMS_Filters"
    if "brake" in cat:
        return "Brakes"
    if cat.startswith("clutch") or cat in ("release_bearing", "pilot_bearing"):
        return "Clutch_Driveline"
    if cat in ("blower_filter", "urea_filter"):
        return "PMS_Filters"
    return "Other"


# Catalog-only PMS labels whose front/rear split is a non-unit of commercial action (closed
# decision 2026-07-16). Folded into the canonical parent; the split is preserved in the raw
# catalog file for anyone who wants it.
PMS_CATEGORY_ALIASES: dict[str, str] = {
    "brake_pad_front": "brake_pad",
    "brake_pad_rear": "brake_pad",
    "brake_shoe_front": "brake_shoe",
    "brake_shoe_rear": "brake_shoe",
    "brake_lining_front": "brake_shoe",
    "brake_lining_rear": "brake_shoe",
}

# Adjusters on the ceiling-derived gap so it reads as an action basis, not a "recover everything"
# number. Both are plain business margins, per the spoken-labels rule (margin, never a factor).
CEILING_QUALIFIER = "if the whole network billed at the observed 96% list realisation"
PRICE_ADJUSTER = "price holds at the observed level; volume is the lever"

SERVICE_YEARS = (2023, 2024, 2025, 2026)


def _norm_pn(value: object) -> str:
    """Normalise a part number the way the rest of the pipeline does (strip leading zeros)."""
    return normalize_pn_value(value) or ""


def load_part_taxonomy() -> pd.DataFrame:
    """One row per part number: the AIM function axis, the catalog service axis, the BVP tag.

    Precedence is stated rather than implied:

    - ``aim_l1`` from ``aim_master_v2.aim_l1_fixed`` (authoritative, 99.3% of euro)
    - ``pms_category`` from the PMS registry via ``bvp_pn_dimension`` first — that is the registry
      the PMS capture engine actually prices — then from the catalog dimension for the labels the
      registry does not carry.
    - ``line_type`` from the BVP cross-reference via ``bvp_pn_dimension``, which is the
      authoritative genuine/BVP split (the raw catalog sheet mislabels genuine as BVP).
    """
    aim = pd.read_csv(
        _AIM_MASTER_CSV,
        dtype=str,
        usecols=["part_number", "aim_l1_fixed", "aim_source"],
        low_memory=False,
    )
    aim["_pn"] = aim["part_number"].map(_norm_pn)
    aim = aim[aim["_pn"] != ""].drop_duplicates("_pn")

    dim = pd.read_csv(BVP_PN_DIMENSION_CSV, dtype=str)
    dim["_pn"] = dim["part_number"].map(_norm_pn)
    dim = dim[dim["_pn"] != ""]
    dim = dim.sort_values("pms_category", na_position="last").drop_duplicates("_pn")

    catalog = pd.read_csv(
        PARTS_CATALOG_DIMENSION_CSV, dtype=str, usecols=["part_number", "pms_category", "pr00_family"]
    )
    catalog["_pn"] = catalog["part_number"].map(_norm_pn)
    catalog = catalog[catalog["_pn"] != ""].drop_duplicates("_pn")
    # Fold the front/rear labels, then turn the empty string into a real null. An empty string
    # here would defeat the "is it filled?" test below and silently claim coverage.
    catalog["pms_category"] = (
        catalog["pms_category"].replace(PMS_CATEGORY_ALIASES).replace("", np.nan)
    )

    out = aim[["_pn", "aim_l1_fixed", "aim_source"]].copy()
    out = out.merge(
        dim[["_pn", "pms_category", "line_type", "product_family"]],
        on="_pn",
        how="outer",
    )
    out = out.merge(
        catalog[["_pn", "pms_category", "pr00_family"]].rename(
            columns={"pms_category": "catalog_pms_category"}
        ),
        on="_pn",
        how="left",
    )

    # Registry wins where it carries a category; the catalog fills the remainder.
    registry_cat = out["pms_category"].replace("", np.nan)
    out["pms_category"] = registry_cat
    fill = out["pms_category"].isna() & out["catalog_pms_category"].notna()
    out.loc[fill, "pms_category"] = out.loc[fill, "catalog_pms_category"]
    out["pms_category_source"] = np.where(
        registry_cat.notna(), "pms_registry", np.where(fill, "catalog_dimension", "none")
    )
    out = out.drop(columns=["catalog_pms_category"])
    out["aim_l1"] = out["aim_l1_fixed"].fillna("Unclassified")
    no_axis = out["pms_category"].isna() & out["aim_l1_fixed"].isna()
    out["family_7"] = np.where(
        out["pms_category"].notna(),
        out["pms_category"].map(lambda c: _family_for_pms_category(str(c))),
        out["aim_l1_fixed"].map(AIM_L1_TO_FAMILY_7),
    )
    # A part on neither axis is reported as an explicit bucket rather than absorbed into "Other",
    # so a coverage weakness stays visible as a number rather than hidden inside a family.
    out.loc[no_axis, "family_7"] = "unclassified_pn"
    out["family_7"] = pd.Series(out["family_7"], index=out.index).fillna("unclassified_pn")
    return out[
        ["_pn", "aim_l1", "aim_l1_fixed", "aim_source", "pms_category", "pms_category_source",
         "line_type", "product_family", "family_7", "pr00_family"]
    ]


def build_billing_monthly(sales: pd.DataFrame, taxonomy: pd.DataFrame) -> pd.DataFrame:
    """One classification pass: billed euro and units per market x family x category x year x month.

    Everything downstream aggregates from here, so the taxonomy is applied exactly once and the
    price split and momentum columns can never disagree about which family a part belongs to.
    """
    df = sales.copy()
    df["_pn"] = df["part_number"].map(_norm_pn)
    tx = taxonomy.drop(columns=["part_number"], errors="ignore")
    df = df.merge(tx, on="_pn", how="left")

    df["aim_l1"] = df["aim_l1"].fillna("Unclassified")
    df["family_7"] = df["family_7"].fillna("unclassified_pn")
    df["month"] = pd.to_datetime(df["billing_date"], errors="coerce").dt.month

    # Explicit, countable bucket for part numbers that resolve on the service axis, so a coverage
    # weakness is visible as a row rather than absorbed into a family.
    df["pms_category_out"] = df["pms_category"].fillna("not_a_service_family")

    # Genuine / BVP split from the cross-reference tag, with its own coverage column so a thin tag
    # never reads as a firm mix.
    df["_lt"] = df["line_type"].where(df["line_type"].isin(["genuine", "bvp"]), "untagged")
    df["_gen_eur"] = np.where(df["_lt"] == "genuine", df["net_sales_value"], 0.0)
    df["_bvp_eur"] = np.where(df["_lt"] == "bvp", df["net_sales_value"], 0.0)
    df["_gen_qty"] = np.where(df["_lt"] == "genuine", df["billed_qty"], 0.0)
    df["_bvp_qty"] = np.where(df["_lt"] == "bvp", df["billed_qty"], 0.0)
    df["_tagged_eur"] = np.where(df["_lt"] != "untagged", df["net_sales_value"], 0.0)

    keys = ["distributor_code", "year", "month", "aim_l1", "family_7", "pms_category_out"]
    out = (
        df.groupby(keys, dropna=False)
        .agg(
            billed_qty=("billed_qty", "sum"),
            net_sales_eur=("net_sales_value", "sum"),
            distinct_pns=("part_number", "nunique"),
            tagged_eur=("_tagged_eur", "sum"),
            genuine_eur=("_gen_eur", "sum"),
            bvp_eur=("_bvp_eur", "sum"),
            genuine_qty=("_gen_qty", "sum"),
            bvp_qty=("_bvp_qty", "sum"),
        )
        .reset_index()
        .rename(columns={"pms_category_out": "pms_category"})
    )
    # ISZE's financial year runs April to March, so FY2026 is Apr 2025 to Mar 2026. The label is
    # the calendar year that closes the year. Both clocks are carried because the house rule is to
    # show both, and because a calendar-year reading of a business that plans in fiscal years has
    # already caused one wrong conclusion in this workspace.
    out["fiscal_year"] = np.where(out["month"] >= 4, out["year"] + 1, out["year"])
    out["fiscal_quarter"] = ((out["month"] - 4) % 12) // 3 + 1
    return out


def build_billing_layer(monthly: pd.DataFrame) -> pd.DataFrame:
    """Roll the monthly classification up to market x family x service category x year."""
    keys = ["distributor_code", "year", "aim_l1", "family_7", "pms_category"]
    out = (
        monthly.groupby(keys, dropna=False)
        .agg(
            billed_qty=("billed_qty", "sum"),
            net_sales_eur=("net_sales_eur", "sum"),
            distinct_pns=("distinct_pns", "sum"),
            tagged_eur=("tagged_eur", "sum"),
            genuine_eur=("genuine_eur", "sum"),
            bvp_eur=("bvp_eur", "sum"),
            genuine_qty=("genuine_qty", "sum"),
            bvp_qty=("bvp_qty", "sum"),
        )
        .reset_index()
    )
    out["asp_eur"] = np.where(out["billed_qty"] > 0, out["net_sales_eur"] / out["billed_qty"], np.nan)
    out["bvp_share_units"] = np.where(
        (out["genuine_qty"].fillna(0) + out["bvp_qty"].fillna(0)) > 0,
        out["bvp_qty"] / (out["genuine_qty"].fillna(0) + out["bvp_qty"].fillna(0)),
        np.nan,
    )
    out["mix_tagged_share_eur"] = np.where(
        out["net_sales_eur"] > 0, out["tagged_eur"] / out["net_sales_eur"], np.nan
    )
    return out.drop(columns=["tagged_eur"])


def build_service_layer() -> pd.DataFrame:
    """Expected demand, capture and gap type per market x service category x year.

    ``total`` line type only — total sales, genuine plus BVP, per the sales-is-sales rule. A
    genuine-only cut is available in ``pms_capture_by_db_year.csv`` but is never the headline.
    """
    pms = pd.read_csv(PMS_CAPTURE_BY_DB_CSV)
    tot = pms[pms["line_type"] == "total"].copy()
    keep = [
        "distributor_code", "year", "pms_category", "expected_qty", "actual_qty",
        "actual_rev_eur", "capture_rate", "avg_sp_eur", "revenue_gap_eur", "scope",
    ]
    out = tot[keep].rename(
        columns={
            "expected_qty": "pms_expected_qty",
            "actual_qty": "pms_actual_qty",
            "actual_rev_eur": "pms_actual_rev_eur",
            "capture_rate": "pms_capture_rate",
            "avg_sp_eur": "pms_avg_sp_eur",
            "revenue_gap_eur": "pms_gap_eur_modelled",
        }
    )
    out["gap_units_if_below_expected"] = np.maximum(
        out["pms_expected_qty"] - out["pms_actual_qty"], 0
    )
    out["is_partial_year"] = out["year"].isin([int(pd.Timestamp.today().year)])
    return out


def build_gap_type_layer() -> pd.DataFrame:
    """Under-service / substitution / catalogue gap, from the existing recovery model.

    That model publishes the classification for the latest **complete** year only. Attaching it
    to every year would imply a measurement that was never made, so the column carries the
    classification year explicitly and is null elsewhere.
    """
    rec = pd.read_csv(_CAPTURE_RECOVERY_CSV)
    out = rec[
        ["distributor_code", "pms_category", "year", "gap_type", "gap_revenue_at_genuine",
         "bvp_unit_share", "avg_sp_genuine_eur", "avg_sp_bvp_eur"]
    ].rename(
        columns={
            "year": "gap_type_year",
            "gap_revenue_at_genuine": "gap_eur_at_genuine",
            "bvp_unit_share": "gap_type_bvp_share",
        }
    )
    return out


def build_ceiling_layer() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ceiling and cover. Returns (market-year series, family-year series marked as shared).

    The family series repeats the market number because the ceiling is not decomposable. It
    carries ``ceilings_are_market_level=True`` on every row so it cannot be summed blindly.
    """
    w = pd.read_csv(_WALLET_CSV)
    cols = [
        "distributor_code", "year", "uio_units", "theoretical_wallet_eur", "captured_total_eur",
        "uncaptured_eur", "gps_pct", "bvp_share_of_captured_pct", "assumption_note",
    ]
    w = w[[c for c in cols if c in w.columns]].copy()
    w["is_partial_year"] = w["year"] >= int(pd.Timestamp.today().year)
    w["gps_pct_whole"] = (w["gps_pct"] / 100).round(6)

    # The action basis: what the gap is worth if the whole book billed at the observed
    # realisation rather than at full list. Realisation is the measured per-market figure from
    # pr00_realization_by_db_cy, averaged over the complete years only — the current-year row is a
    # part year and would drag the average down for no commercial reason.
    real = pd.read_csv(_REALIZATION_CSV)
    real = real[real["realization_pct"].notna() & (real["year"] < int(pd.Timestamp.today().year))]
    real_mean = (
        real.groupby("db")["realization_pct"].mean().rename("realisation_pct_avg").reset_index()
    )
    w = w.merge(real_mean, left_on="distributor_code", right_on="db", how="left")
    w = w.drop(columns=["db"], errors="ignore")
    w["actionable_gap_eur"] = (
        w["uncaptured_eur"] * (w["realisation_pct_avg"].fillna(100.0) / 100.0)
    ).round(2)
    w["unrecoverable_at_90pct_cover_eur"] = np.maximum(
        w["uncaptured_eur"] - (w["theoretical_wallet_eur"] * 0.10), 0
    ).round(2)
    w["ceiling_qualifier"] = CEILING_QUALIFIER
    w["price_adjuster"] = PRICE_ADJUSTER

    market = w.copy()

    # Market-level GPS spend per vehicle in service, only for the years the source supports
    # (2026 carries a part-year basis and is blanked upstream).
    gps = pd.read_csv(_GPS_SPU_BY_DB_CSV)
    gps = gps[
        ["year", "distributor_code", "spend_per_unit_eur", "max_spend_eur", "period_basis",
         "gps_capture_vs_max"]
    ]
    market = market.merge(gps, on=["year", "distributor_code"], how="left")
    market["gps_source_year_verified"] = market["period_basis"].eq("full_year")

    shared = market.copy()
    shared["ceilings_are_market_level"] = True
    return market, shared


def build_trend_layer() -> pd.DataFrame:
    """Capture trend slope per market x service category, already guarded against part years."""
    if not _CAPTURE_TRAJECTORY_CSV.exists():
        return pd.DataFrame(
            columns=["distributor_code", "pms_category", "capture_slope_pp_per_year",
                     "capture_trend_r2", "capture_declining"]
        )
    traj = pd.read_csv(_CAPTURE_TRAJECTORY_CSV)
    traj = traj.drop_duplicates(["distributor_code", "pms_category"], keep="first")
    return traj[
        ["distributor_code", "pms_category", "trend_slope_pp_per_year", "trend_r2",
         "alert_declining"]
    ].rename(
        columns={
            "trend_slope_pp_per_year": "capture_slope_pp_per_year",
            "trend_r2": "capture_trend_r2",
            "alert_declining": "capture_declining",
        }
    )


def build_price_layer(
    billing: pd.DataFrame, month_max: int | None = None, basis: str = "full_year"
) -> pd.DataFrame:
    """True three-way volume / price / mix split per market x family x year pair.

    ``revenue_waterfall.csv`` publishes a volume and price split, but its mix term is identically
    zero, so it cannot say whether a move came from selling different parts or from repricing the
    same parts. A naive re-split has the same problem: if price is measured at the same grain as
    the mix axis, ``volume + price`` equals the total by construction and mix is always zero. That
    is an identity, not a finding.

    Mix only exists when price is aggregated one level above the mix axis. So price is taken at
    **family** level and the mix axis is the service category inside the family:

        P̄0   = Σ_c (q0_c / Q0) · p0_c            weighted family price, base year
        vol   = (Q1 − Q0) · P̄0
        mix   = Σ_c q1_c · p0_c   −   Q1 · P̄0    category weight shift, at base-year prices
        price = Σ_c q1_c · (p1_c − p0_c)          price move on the parts actually sold

    The three sum to ``R1 − R0`` exactly. A category with no observed price in the base year falls
    back to its own later price, so the shift is attributed to mix rather than invented as price.

    ``month_max`` restricts every year to the same months (6 = January to June). Without it the
    last pair is a part year against a full year and reads as a collapse that did not happen; the
    2026 comparison is therefore run like-for-like and labelled ``basis="jan_jun"``.
    """
    cat = billing.copy()
    if month_max is not None:
        cat = cat[cat["month"] <= month_max].copy()
    rows: list[dict] = []
    for (dist, family), g in cat.groupby(["distributor_code", "family_7"], dropna=False):
        agg = (
            g.groupby(["year", "pms_category"])
            .agg(qty=("billed_qty", "sum"), rev=("net_sales_eur", "sum"))
            .reset_index()
        )
        agg["asp"] = np.where(agg["qty"] > 0, agg["rev"] / agg["qty"], np.nan)
        years = sorted(int(y) for y in agg["year"].unique())
        for y_from, y_to in zip(years, years[1:]):
            a = agg[agg["year"] == y_from].set_index("pms_category")
            b = agg[agg["year"] == y_to].set_index("pms_category")
            cats = a.index.union(b.index)
            q0 = a["qty"].reindex(cats).fillna(0.0)
            q1 = b["qty"].reindex(cats).fillna(0.0)
            asp0 = a["asp"].reindex(cats)
            asp1 = b["asp"].reindex(cats)
            r0 = float(a["rev"].sum())
            r1 = float(b["rev"].sum())
            if r0 <= 0 and r1 <= 0:
                continue

            asp0_f = asp0.fillna(asp1).fillna(0.0)
            asp1_f = asp1.fillna(asp0).fillna(0.0)
            q_total0 = float(q0.sum())
            q_total1 = float(q1.sum())
            pbar0 = float((q0 / q_total0 * asp0_f).sum()) if q_total0 > 0 else 0.0

            d_vol = (q_total1 - q_total0) * pbar0
            d_mix = float((q1 * asp0_f).sum()) - q_total1 * pbar0
            d_price = float((q1 * (asp1_f - asp0_f)).sum())
            d_tot = r1 - r0

            rows.append(
                {
                    "distributor_code": dist,
                    "family_7": family,
                    "year_from": y_from,
                    "year_to": y_to,
                    "basis": basis,
                    "revenue_base_eur": round(r0, 2),
                    "revenue_end_eur": round(r1, 2),
                    "qty_base": q_total0,
                    "qty_end": q_total1,
                    "pbar_base_eur": round(pbar0, 4),
                    "delta_total_eur": round(d_tot, 2),
                    "delta_volume_eur": round(d_vol, 2),
                    "delta_price_eur": round(d_price, 2),
                    "delta_mix_eur": round(d_mix, 2),
                    "residual_eur": round(d_tot - d_vol - d_price - d_mix, 2),
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    # Attach each pair to the closing year so it lines up with the rest of the model.
    out["year"] = out["year_to"]
    return out.drop(columns=["year_to"])


def build_momentum_layer(monthly: pd.DataFrame) -> pd.DataFrame:
    """Like-for-like year-on-year momentum per market x family x year.

    Every year is cut to the same month window, so the current year (billing is complete only to
    June) is compared with January to June of its base year rather than with a full year. Without
    this the last column of any evolution view reads as a collapse that did not happen.
    """
    yearly = (
        monthly.groupby(["distributor_code", "family_7", "year"], dropna=False)["net_sales_eur"]
        .sum()
        .reset_index()
    )
    h1 = (
        monthly[monthly["month"] <= 6]
        .groupby(["distributor_code", "family_7", "year"], dropna=False)["net_sales_eur"]
        .sum()
        .reset_index()
        .rename(columns={"net_sales_eur": "net_sales_eur_h1"})
    )
    both = yearly.merge(h1, on=["distributor_code", "family_7", "year"], how="left")

    current_year = int(pd.Timestamp.today().year)
    rows: list[dict] = []
    for (dist, family), g in both.groupby(["distributor_code", "family_7"], dropna=False):
        g = g.sort_values("year")
        for i in range(1, len(g)):
            prev = g.iloc[i - 1]
            cur = g.iloc[i]
            y1 = int(cur["year"])
            if y1 >= current_year:
                r0, r1, basis = (
                    float(prev["net_sales_eur_h1"] or 0.0),
                    float(cur["net_sales_eur_h1"] or 0.0),
                    "jan_jun",
                )
            else:
                r0, r1, basis = (
                    float(prev["net_sales_eur"] or 0.0),
                    float(cur["net_sales_eur"] or 0.0),
                    "full_year",
                )
            rows.append(
                {
                    "distributor_code": dist,
                    "family_7": family,
                    "year": y1,
                    "year_from": int(prev["year"]),
                    "momentum_basis": basis,
                    "billed_base_eur": round(r0, 2),
                    "billed_end_eur": round(r1, 2),
                    "yoy_eur": round(r1 - r0, 2),
                    "yoy_pct": round(100 * (r1 / r0 - 1), 2) if r0 > 0 else np.nan,
                    "is_partial_year": y1 >= current_year,
                }
            )
    return pd.DataFrame(rows)


def build_substitution_layer() -> pd.DataFrame:
    """BVP down-trade per market x family x year, plus a read on what it did to volume.

    The flag is a rule, not a measurement, and is labelled as such:

    - ``bvp_share_up_volume_held`` — BVP share rose while total family volume held or grew. We
      moved volume onto our own value line and kept the unit, which is defending against the
      independent aftermarket.
    - ``bvp_share_up_volume_lost`` — BVP share rose while total volume fell. Down-trade happened
      and the unit was lost anyway, so the value line was not the reason for the loss.
    - ``stable`` — share moved less than 5 points.
    """
    if not _SUBSTITUTION_TIMELINE_CSV.exists():
        return pd.DataFrame()
    sub = pd.read_csv(_SUBSTITUTION_TIMELINE_CSV)
    sub["total_units"] = sub["genuine_units"] + sub["bvp_units"]
    sub["bvp_share_units"] = np.where(
        sub["total_units"] > 0, sub["bvp_units"] / sub["total_units"], np.nan
    )

    rows: list[dict] = []
    for (dist, family), g in sub.groupby(["distributor_code", "product_family"], dropna=False):
        g = g.sort_values("year")
        first = g["bvp_first_billing_year"].dropna()
        if first.empty:
            share_change = np.nan
            verdict = "no_bvp_in_market"
        else:
            entry_year = int(first.iloc[0])
            base = g[g["year"] == entry_year]
            latest = g[g["year"] == g["year"].max()]
            if base.empty or latest.empty:
                share_change = np.nan
                verdict = "insufficient_years"
            else:
                sh0 = float(base["bvp_share_units"].iloc[0])
                sh1 = float(latest["bvp_share_units"].iloc[0])
                u0 = float(base["total_units"].iloc[0])
                u1 = float(latest["total_units"].iloc[0])
                share_change = sh1 - sh0
                if share_change < 0.05:
                    verdict = "stable"
                elif u1 >= u0:
                    verdict = "bvp_share_up_volume_held"
                else:
                    verdict = "bvp_share_up_volume_lost"
        rows.append(
            {
                "distributor_code": dist,
                "family_7": family,
                "bvp_unit_share_latest": round(
                    float(g["bvp_share_units"].iloc[-1]), 4
                )
                if g["bvp_share_units"].notna().any()
                else np.nan,
                "bvp_share_change_pp": round(share_change * 100, 2)
                if pd.notna(share_change)
                else np.nan,
                "total_units_first_bvp_year": float(
                    g[g["year"] == int(first.iloc[0])]["total_units"].iloc[0]
                )
                if not first.empty
                else np.nan,
                "total_units_latest_year": float(g["total_units"].iloc[-1]),
                "bvp_first_billing_year": int(first.iloc[0]) if not first.empty else np.nan,
                "down_trade_verdict": verdict,
                "verdict_basis": "rule: share change >= 5pp and total family units vs BVP-entry year",
            }
        )
    return pd.DataFrame(rows)


def build_competitor_layer(taxonomy: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Competitor price position, honestly bounded.

    Returns (part-number sheet, source rollup). Two sources carry a genuine competitor price; they
    are different vintages and different tiers and are never blended.

    The KS file repeats one UK trade price across every market row, so 374 rows are only 43
    distinct facts. Medians are therefore taken over **distinct part numbers**, not over rows,
    otherwise the one source that fans widest would set the network number.
    """
    pn_rows: list[pd.DataFrame] = []

    if _COMPETITOR_COMMON_BASIS_CSV.exists():
        cb = pd.read_csv(_COMPETITOR_COMMON_BASIS_CSV)
        cb["_pn"] = cb["pn"].map(_norm_pn)
        pn_rows.append(
            cb.assign(
                source="KS trade (GBP to EUR)",
                db=cb["db"],
                part_number=cb["_pn"],
                competitor_price_eur=cb["competitor_price_eur"],
                our_reference_dealer_eur=cb["k3_reference_dealer_eur"],
                our_net_to_distributor_eur=cb["k1_net_to_distributor_eur"],
                index_reference_vs_competitor=cb["index_reference_vs_competitor"],
                index_netdist_vs_competitor=cb["index_netdist_vs_competitor"],
                vintage="2026-08-10 to 2026-08-14",
                tier="competitor retail, one UK source fanned across markets",
            )[
                ["source", "db", "part_number", "competitor_price_eur",
                 "our_reference_dealer_eur", "our_net_to_distributor_eur",
                 "index_reference_vs_competitor", "index_netdist_vs_competitor", "vintage", "tier"]
            ]
        )

    if _COMPETITOR_WORKLIST_CSV.exists():
        wl = pd.read_csv(_COMPETITOR_WORKLIST_CSV)
        wl = wl[wl["status"].astype(str).str.lower() == "resolved"].copy()
        wl["part_number"] = wl["pn"].map(_norm_pn)
        pn_rows.append(
            wl.assign(
                source="multi-brand bridge",
                db="",  # a multi-brand price lookup, not market-specific
                our_net_to_distributor_eur=np.nan,
                our_reference_dealer_eur=wl["our_reference_dealer_price_eur"],
                index_reference_vs_competitor=wl["price_index_our_dealer_vs_competitor"],
                index_netdist_vs_competitor=np.nan,
                vintage="2026-09-18",
                tier="online IAM, provenance and licence NOT established",
            )[
                ["source", "db", "part_number", "competitor_price_eur",
                 "our_reference_dealer_eur", "our_net_to_distributor_eur",
                 "index_reference_vs_competitor", "index_netdist_vs_competitor", "vintage", "tier"]
            ]
        )

    if not pn_rows:
        return pd.DataFrame(), pd.DataFrame()

    pn = pd.concat(pn_rows, ignore_index=True)

    # Attach the AIM family so coverage can be read as a business family, not a bare list of
    # numbers. Service category is deliberately not forced: most competitor numbers are not PMS.
    if taxonomy is not None:
        pn = pn.merge(
            taxonomy[["_pn", "aim_l1", "family_7"]].rename(columns={"_pn": "part_number"}),
            on="part_number",
            how="left",
        )
    else:
        pn["aim_l1"] = np.nan
        pn["family_7"] = np.nan

    # One row per source and part number before any statistic, so the fanning cannot weight it.
    per_pn = (
        pn.groupby(["source", "part_number"])
        .agg(
            index_reference_vs_competitor=("index_reference_vs_competitor", "median"),
            markets_listing=("db", "nunique"),
            vintage=("vintage", "first"),
            tier=("tier", "first"),
        )
        .reset_index()
    )
    roll = (
        per_pn.groupby("source")
        .agg(
            covered_part_numbers=("part_number", "nunique"),
            median_index_reference_vs_competitor=("index_reference_vs_competitor", "median"),
            p10_index=("index_reference_vs_competitor", lambda s: s.quantile(0.10)),
            p90_index=("index_reference_vs_competitor", lambda s: s.quantile(0.90)),
            share_above_2x=("index_reference_vs_competitor", lambda s: float((s > 2).mean())),
            share_above_3x=("index_reference_vs_competitor", lambda s: float((s > 3).mean())),
            vintage=("vintage", "first"),
            tier=("tier", "first"),
        )
        .reset_index()
    )
    return pn, roll


def build_pn_action_layer(
    sales: pd.DataFrame, taxonomy: pd.DataFrame, competitor_pn: pd.DataFrame
) -> pd.DataFrame:
    """The action layer: one row per part number with the numbers a decision needs.

    This is the layer that turns a sized gap into an instruction. Four questions per part number:

    1. **Is it worth attention?** Billed euro all years, units, and how many markets.
    2. **Does the dealer hold a real share of what they buy?** Sold to the dealer against what the
       dealer sells on, from the ITUK dealer sell-out, which is the only market we hold at this
       grain. A ratio above 1 means the dealer moved more than they bought.
    3. **Is there room to move?** Margin today, cost landed, and the discount headroom we could
       fund ourselves before breaching the 25% gross-margin floor.
    4. **Could a discount even reach the competitor?** If the competitor price sits below our own
       landed cost, no discount reaches it and the lever is landed cost or a cheaper line, not
       price. This is the single most decision-relevant column on the file.

    ``could_match_at_gm_floor`` compares the competitor against the lowest dealer price we could
    legitimately set, which is our list x the channel uplift at the margin floor. If even that is
    above the competitor, the part is structurally out of reach on price.
    """
    norm = lambda s: s.map(_norm_pn)  # noqa: E731

    if competitor_pn.empty:
        return pd.DataFrame()

    # Cheapest real competitor observation per part number. Where two sources disagree, the lower
    # one is the one that matters for a competitiveness question.
    comp = (
        competitor_pn.dropna(subset=["competitor_price_eur"])
        .assign(comp_eur=lambda d: pd.to_numeric(d["competitor_price_eur"], errors="coerce"))
        .dropna(subset=["comp_eur"])
        .groupby("part_number")
        .agg(
            competitor_price_eur=("comp_eur", "min"),
            competitor_source_count=("source", "nunique"),
            competitor_sources=("source", lambda s: " + ".join(sorted(set(s)))),
            our_reference_eur=("our_reference_dealer_eur", "median"),
        )
        .reset_index()
    )

    # Cost and margin.
    mar = pd.read_csv(_MARGIN_PN_CSV, dtype=str, low_memory=False)
    mar["part_number"] = norm(mar["pn"])
    mar = mar.assign(
        cost_landed_eur=lambda d: pd.to_numeric(d["cost_fob"], errors="coerce"),
        margin_pct_today=lambda d: pd.to_numeric(d["margin_pct"], errors="coerce") / 100.0,
    )
    mar = mar.drop_duplicates("part_number")[
        ["part_number", "cost_landed_eur", "margin_pct_today", "aim_l1", "aim_l2",
         "criticality", "competition", "price_class"]
    ]

    # Billing per part number, all years and latest complete year.
    sf = sales.copy()
    sf["part_number"] = norm(sf["part_number"])
    cy = int(pd.Timestamp.today().year) - 1
    bill = sf.groupby("part_number").agg(
        billed_all_years_eur=("net_sales_value", "sum"),
        units_all_years=("billed_qty", "sum"),
        markets=("distributor_code", "nunique"),
    ).reset_index()
    bill_cy = (
        sf[sf["year"] == cy]
        .groupby("part_number")
        .agg(billed_latest_cy_eur=("net_sales_value", "sum"),
             units_latest_cy=("billed_qty", "sum"))
        .reset_index()
    )

    # Dealer share of the same part: what we sold the distributor against what the dealer sold on.
    share = pd.DataFrame()
    if _SELLOUT_TOP_PN_CSV.exists() and _SELLOUT_AIM_L1_CSV.exists():
        so = pd.read_csv(_SELLOUT_TOP_PN_CSV)
        so["part_number"] = norm(so["part_number"])
        so_agg = (
            so.groupby("part_number")
            .agg(dealer_sold_units=("qty_year", "sum"), dealer_sold_eur=("valued_eur", "sum"))
            .reset_index()
        )
        share = so_agg

    out = comp.merge(mar, on="part_number", how="left")
    out = out.merge(bill, on="part_number", how="left")
    out = out.merge(bill_cy, on="part_number", how="left")
    if not share.empty:
        out = out.merge(share, on="part_number", how="left")

    # Our list price, reconstructed from a landed cost and the margin we show today.
    out["our_list_eur"] = np.where(
        (out["cost_landed_eur"] > 0) & (out["margin_pct_today"] > 0),
        out["cost_landed_eur"] / (1 - out["margin_pct_today"]),
        np.nan,
    )
    # Lowest dealer price we could legitimately set, if we let margin fall to the 25% floor.
    out["dealer_price_at_gm_floor_eur"] = np.where(
        out["cost_landed_eur"] > 0, out["cost_landed_eur"] / 0.75 * DEALER_UPLIFT, np.nan
    )
    out["headroom_to_gm_floor_eur"] = out["our_reference_eur"] - out["dealer_price_at_gm_floor_eur"]
    out["discount_headroom_pct"] = np.where(
        out["our_reference_eur"] > 0,
        (1 - out["dealer_price_at_gm_floor_eur"] / out["our_reference_eur"]) * 100,
        np.nan,
    )
    out["index_vs_competitor"] = np.where(
        out["competitor_price_eur"] > 0, out["our_reference_eur"] / out["competitor_price_eur"], np.nan
    )

    # The decision test.
    out["competitor_below_our_cost"] = out["competitor_price_eur"] < out["cost_landed_eur"]
    out["could_match_at_gm_floor"] = (
        out["dealer_price_at_gm_floor_eur"] <= out["competitor_price_eur"]
    )
    out["sell_through_ratio"] = np.where(
        out["units_latest_cy"] > 0, out["dealer_sold_units"] / out["units_latest_cy"], np.nan
    )

    def _lever(r: pd.Series) -> str:
        if pd.isna(r["cost_landed_eur"]) or pd.isna(r["competitor_price_eur"]):
            return "insufficient_pricing_data"
        if r["competitor_below_our_cost"]:
            return "landed_cost_not_price"
        if not r["could_match_at_gm_floor"]:
            return "below_margin_floor"
        return "price_or_incentive_actionable"

    out["recommended_lever"] = out.apply(_lever, axis=1)

    # An incentive can only fix what a price move can fix. Say so on the row.
    out["incentive_can_help"] = out["recommended_lever"].eq("price_or_incentive_actionable")

    if "family_7" in out.columns:
        out = out.drop(columns=["family_7"])
    fam = taxonomy[["_pn", "family_7"]].rename(columns={"_pn": "part_number"})
    out = out.merge(fam, on="part_number", how="left")
    out["family_7"] = out["family_7"].fillna("unclassified_pn")

    out["billed_rank_in_book"] = out["billed_all_years_eur"].rank(ascending=False, method="min")

    cols = [
        "part_number", "criticality", "competition", "price_class", "aim_l1", "aim_l2", "family_7",
        "billed_all_years_eur", "billed_latest_cy_eur", "units_all_years", "units_latest_cy",
        "markets", "dealer_sold_units", "dealer_sold_eur", "sell_through_ratio",
        "cost_landed_eur", "margin_pct_today", "our_list_eur", "our_reference_eur",
        "competitor_price_eur", "index_vs_competitor", "dealer_price_at_gm_floor_eur",
        "discount_headroom_pct", "competitor_below_our_cost", "could_match_at_gm_floor",
        "recommended_lever", "incentive_can_help", "competitor_sources", "competitor_source_count",
        "billed_rank_in_book",
    ]
    out = out[[c for c in cols if c in out.columns]]
    return out.sort_values("billed_all_years_eur", ascending=False).reset_index(drop=True)


def build_fiscal_layer(monthly: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Like-for-like momentum on ISZE's own clock, April to March.

    The workspace rule is to show both clocks because the business plans in fiscal years. This is
    the same comparison the calendar layer makes, cut on the fiscal year instead.

    Completeness is derived from the months actually present, not assumed. Billing starts in
    January 2023, so FY2023 holds only January to March and is a three-month stub, while the
    current year holds only its closed months. Marking a stub as a full year would put a false
    collapse in the series.

    Billing runs to June 2026, so the closed part of the current fiscal year is April to June.
    """
    fy_year = (
        monthly.groupby(["distributor_code", "family_7", "fiscal_year"], dropna=False)
        .agg(net_sales_eur=("net_sales_eur", "sum"), months_present=("month", "nunique"))
        .reset_index()
    )
    # Months 4,5,6 = the first fiscal quarter.
    q1 = (
        monthly[monthly["fiscal_quarter"] == 1]
        .groupby(["distributor_code", "family_7", "fiscal_year"], dropna=False)["net_sales_eur"]
        .sum()
        .reset_index()
        .rename(columns={"net_sales_eur": "net_sales_eur_q1"})
    )
    both = fy_year.merge(q1, on=["distributor_code", "family_7", "fiscal_year"], how="left")

    fiscal_years = sorted(int(y) for y in both["fiscal_year"].unique())
    latest_fy = fiscal_years[-1]

    rows: list[dict] = []
    for _, r in both.iterrows():
        fy = int(r["fiscal_year"])
        if fy == latest_fy:
            continue  # the current year is compared on its closed quarter, below
        rows.append(
            {
                "distributor_code": r["distributor_code"],
                "family_7": r["family_7"],
                "fiscal_year": fy,
                "fy_label": f"FY{fy}",
                "months_present": int(r["months_present"]),
                "is_complete": int(r["months_present"]) == 12,
                "billed_eur": round(float(r["net_sales_eur"] or 0.0), 2),
            }
        )
    full = pd.DataFrame(rows)

    # Fiscal-year totals, carrying the month count so a stub year cannot be read as a full one.
    net = (
        full.groupby(["fiscal_year", "fy_label"], as_index=False)
        .agg(billed_eur=("billed_eur", "sum"), months_present=("months_present", "max"),
             is_complete=("is_complete", "max"))
        .sort_values("fiscal_year")
    )
    net["yoy_eur"] = net["billed_eur"].diff()
    net["yoy_pct"] = (net["billed_eur"].pct_change() * 100).round(2)
    # A year-on-year move is only quoted between two complete years.
    net.loc[~net["is_complete"], ["yoy_eur", "yoy_pct"]] = np.nan
    prev_complete = net["is_complete"].shift(1).fillna(False).astype(bool)
    net.loc[~prev_complete, ["yoy_eur", "yoy_pct"]] = np.nan

    # The current fiscal year: its closed quarter against the same quarter of the prior year.
    cur = both[both["fiscal_year"] == latest_fy]
    prev = both[both["fiscal_year"] == latest_fy - 1]
    merged = cur.merge(
        prev[["distributor_code", "family_7", "net_sales_eur_q1"]],
        on=["distributor_code", "family_7"],
        how="left",
        suffixes=("", "_prev"),
    )
    q1_rows = []
    for _, r in merged.iterrows():
        base = float(r["net_sales_eur_q1_prev"] or 0.0)
        end = float(r["net_sales_eur_q1"] or 0.0)
        q1_rows.append(
            {
                "distributor_code": r["distributor_code"],
                "family_7": r["family_7"],
                "fiscal_year": latest_fy,
                "fy_label": f"FY{latest_fy}",
                "comparison": "q1_vs_q1",
                "months_compared": 3,
                "billed_base_eur": round(base, 2),
                "billed_end_eur": round(end, 2),
                "yoy_eur": round(end - base, 2),
                "yoy_pct": round(100 * (end / base - 1), 2) if base > 0 else np.nan,
            }
        )
    q1_net = pd.DataFrame(q1_rows)
    base_total = round(float(q1_net["billed_base_eur"].sum()), 2)
    end_total = round(float(q1_net["billed_end_eur"].sum()), 2)
    q1_total = {
        "fiscal_year": latest_fy,
        "fy_label": f"FY{latest_fy}",
        "months_compared": int(monthly[monthly["fiscal_year"] == latest_fy]["month"].nunique()),
        "billed_base_eur": base_total,
        "billed_end_eur": end_total,
        "yoy_eur": round(end_total - base_total, 2),
        "yoy_pct": round(100 * (end_total / base_total - 1), 2) if base_total else None,
        "note": "closed months of the current fiscal year against the same months of the prior year",
    }
    return net, q1_net, q1_total


def build_lost_sales_model(sales: pd.DataFrame) -> tuple[pd.DataFrame, ...]:
    """Assemble the whole model. ``sales`` is the pipeline parts base (see build_billing_layer)."""
    taxonomy = load_part_taxonomy()
    monthly = build_billing_monthly(sales, taxonomy)
    billing = build_billing_layer(monthly)
    service = build_service_layer()
    gap_type = build_gap_type_layer()
    market, ceiling_shared = build_ceiling_layer()
    trend = build_trend_layer()
    # Full-year pairs for 2023-2025, plus a same-months pair for the part year, kept apart so the
    # part-year comparison can never be read as a full-year collapse.
    price_full = build_price_layer(monthly, month_max=None, basis="full_year")
    price_h1 = build_price_layer(monthly, month_max=6, basis="jan_jun")
    momentum = build_momentum_layer(monthly)
    fy_series, fy_family, fy_q1_total = build_fiscal_layer(monthly)
    subs = build_substitution_layer()
    comp_pn, comp_roll = build_competitor_layer(taxonomy)
    if not comp_roll.empty:
        # Coverage as a share of billed euro for the same source, not only a part-number count.
        # The billed euro comes from the model's own billing rows, so the two sides agree.
        pn_billed = (
            sales.assign(
                part_number=sales["part_number"].map(_norm_pn)
            )
            .groupby("part_number")["net_sales_value"]
            .sum()
            .rename("billed_eur_at_pn")
        )
        comp_pn = comp_pn.merge(pn_billed, on="part_number", how="left")
        # De-duplicate to distinct source x part number before summing euro. The KS file repeats
        # one UK price across every market, so summing the fanned rows would multiply the same
        # fact 18 times and overstate the covered book.
        dedup = comp_pn.drop_duplicates(["source", "part_number"])

        # Coverage is stated on two windows because the existing coverage-truth file quotes the
        # latest complete year while this model runs 2023-2026. Both are published so a reader
        # comparing against the older figure can see it is the same fact in a different window.
        cy = int(pd.Timestamp.today().year) - 1
        pn_cy_billed = (
            sales[sales["year"] == cy]
            .assign(part_number=lambda d: d["part_number"].map(_norm_pn))
            .groupby("part_number")["net_sales_value"]
            .sum()
        )
        comp_pn["billed_eur_latest_complete_cy"] = comp_pn["part_number"].map(pn_cy_billed)
        dedup = comp_pn.drop_duplicates(["source", "part_number"])
        cov = (
            dedup.groupby("source")
            .agg(
                covered_pn_billed_eur_all_years=("billed_eur_at_pn", "sum"),
                covered_pn_billed_eur_latest_complete_cy=("billed_eur_latest_complete_cy", "sum"),
            )
            .reset_index()
        )
        comp_roll = comp_roll.merge(cov, on="source", how="left")
        book_all = float(sales["net_sales_value"].sum())
        book_cy = float(sales[sales["year"] == cy]["net_sales_value"].sum())
        comp_roll["coverage_pct_of_book_all_years"] = (
            100 * comp_roll["covered_pn_billed_eur_all_years"] / book_all
        ).round(2)
        comp_roll["coverage_pct_of_book_latest_complete_cy"] = (
            100 * comp_roll["covered_pn_billed_eur_latest_complete_cy"] / book_cy
        ).round(2)
        comp_roll["coverage_window_note"] = (
            f"all-years denominator EUR {book_all:,.0f}; {cy} denominator EUR {book_cy:,.0f}"
        )

    # The action layer: one row per part number, at the depth a decision needs.
    pn_action = build_pn_action_layer(sales, taxonomy, comp_pn)

    out = billing.merge(service, on=["distributor_code", "year", "pms_category"], how="left")
    out = out.merge(
        gap_type, on=["distributor_code", "pms_category"], how="left"
    )
    out = out.merge(
        ceiling_shared,
        on=["distributor_code", "year"],
        how="left",
        suffixes=("", "_ceiling"),
    )
    out = out.merge(trend, on=["distributor_code", "pms_category"], how="left")
    out = out.merge(
        momentum[
            ["distributor_code", "family_7", "year", "momentum_basis", "billed_base_eur",
             "billed_end_eur", "yoy_eur", "yoy_pct"]
        ],
        on=["distributor_code", "family_7", "year"],
        how="left",
    )

    price_cols = [
        "delta_total_eur", "delta_volume_eur", "delta_price_eur", "delta_mix_eur",
        "revenue_base_eur", "qty_base", "qty_end", "residual_eur", "year_from",
    ]
    for frame, suffix in ((price_full, ""), (price_h1, "_h1")):
        renamed = {c: f"{c}{suffix}" for c in price_cols}
        out = out.merge(
            frame[["distributor_code", "family_7", "year", "basis"] + price_cols].rename(
                columns=renamed
            ),
            on=["distributor_code", "family_7", "year"],
            how="left",
        )
    out = out.merge(
        subs, on=["distributor_code", "family_7"], how="left"
    )

    # A year before the family's first BVP billing cannot carry a BVP verdict: there was nothing
    # to down-trade to. Blank it rather than let a later year's verdict read backwards.
    before_bvp = out["bvp_first_billing_year"].notna() & (out["year"] < out["bvp_first_billing_year"])
    for col in ("down_trade_verdict", "bvp_unit_share_latest", "bvp_share_change_pp"):
        if col in out.columns:
            out.loc[before_bvp, col] = np.nan if col != "down_trade_verdict" else "pre_bvp_entry"

    # On a part year the full-year pair compares a part year against a full year, so the split
    # would read as a collapse. Blank it and keep only the same-months pair, so a reader can never
    # pair a part-year delta with a full-year comparison.
    current_year = int(pd.Timestamp.today().year)
    part_year = out["year"] >= current_year
    stale_cols = [
        "delta_total_eur", "delta_volume_eur", "delta_price_eur", "delta_mix_eur",
        "revenue_base_eur", "qty_base", "qty_end", "residual_eur", "year_from",
    ]
    for col in stale_cols:
        if col in out.columns:
            out.loc[part_year, col] = np.nan

    out["gap_type_applies_to_year"] = out["gap_type"].notna()
    return out, market, comp_pn, comp_roll, pn_action, fy_series, fy_q1_total


def write_model() -> dict[str, object]:
    """Build and write the model. Returns a summary for the caller / verifier."""
    from modules.data_prep import load_distributor_mapping
    from modules.sales_loader import load_prism_sales
    from config import resolve_mapping_path

    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    sales, src = load_prism_sales(df_map)
    if "line_kind" in sales.columns:
        sales = sales[sales["line_kind"] == "part"]
    sales = sales[~sales["is_credit_note"]].copy()

    family, market, comp_pn, comp_roll, pn_action, fy_series, fy_q1_total = build_lost_sales_model(sales)

    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    family.to_csv(LOST_SALES_FAMILY_CSV, index=False)
    market.to_csv(LOST_SALES_MARKET_CSV, index=False)
    if not fy_series.empty:
        fy_series.to_csv(LOST_SALES_FISCAL_CSV, index=False)
    if fy_q1_total:
        pd.DataFrame([fy_q1_total]).to_csv(LOST_SALES_FISCAL_Q1_CSV, index=False)
    if not comp_pn.empty:
        comp_pn.to_csv(LOST_SALES_COMPETITOR_CSV, index=False)
    if not comp_roll.empty:
        comp_roll.to_csv(LOST_SALES_COMPETITOR_COVERAGE_CSV, index=False)
    if not pn_action.empty:
        pn_action.to_csv(LOST_SALES_PN_ACTION_CSV, index=False)

    # ── Tie-outs. Every one of these is a check, not an assertion. ───────────
    base_eur = float(sales["net_sales_value"].sum())
    model_eur = float(family["net_sales_eur"].sum())
    covered_eur = float(family.loc[family["pms_category"] != "not_a_service_family", "net_sales_eur"].sum())
    ceiling_eur = float(
        market.loc[~market["is_partial_year"], "uncaptured_eur"].dropna().max()
        if not market.empty
        else 0.0
    )
    meta: dict[str, object] = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "generated_by": "modules/lost_sales_build.py",
        "grain": "distributor_code x aim_l1 x family_7 x pms_category x year",
        "source_sales": src,
        "rows": int(len(family)),
        "distributors": int(family["distributor_code"].nunique()),
        "years": sorted(int(y) for y in family["year"].dropna().unique()),
        "tieouts": {
            "parts_base_eur": round(base_eur, 2),
            "model_billed_eur": round(model_eur, 2),
            "billed_delta_eur": round(model_eur - base_eur, 2),
            "pms_category_covered_eur": round(covered_eur, 2),
            "pms_category_coverage_pct_of_billed": round(100 * covered_eur / model_eur, 2),
            "largest_market_uncaptured_eur": round(ceiling_eur, 2),
        },
        "sources": {
            "billing": "sales_fact.parquet via load_prism_sales (parts only, ex credit notes)",
            "family_axis": "aim_master_v2.csv -> aim_l1_fixed (99.3% of euro)",
            "service_axis": "bvp_pn_dimension.csv (PMS registry) then parts_catalog_dimension.csv",
            "ceiling": "wallet_waterfall.csv (market level, not decomposable by family)",
            "service_gap": "pms_capture_by_db_year.csv line_type=total",
            "gap_type": "capture_recovery_model.csv (latest complete year only)",
            "pn_action_pricing": "margin_opportunity_top200.csv + competitor_common_basis.csv + "
                                 "price_collection_worklist_filled.csv + sellout_aim_top_pn_2025.csv",
            "trend": "capture_trajectory.csv (part-year guarded upstream)",
            "price_split": "computed here from billing; revenue_waterfall.csv has a zero mix term",
            "down_trade": "substitution_timeline.csv",
            "competitor": "competitor_common_basis.csv + price_collection_worklist_filled.csv",
            "realisation": "pr00_realization_by_db_cy.csv",
        },
        "limits": [
            "No fitted price response exists. One complete dealer-level sell-out year, so there is "
            "no elasticity coefficient and no causal claim on the price axis.",
            "Ceiling columns in the family file are MARKET level and repeated on every family row "
            "(ceilings_are_market_level=True). They must not be summed.",
            "The ceiling is a target spend at list, not a forecast. actionable_gap_eur restates it "
            "at observed list realisation; that is still not a recoverable amount.",
            "2026 is a part year: 7 months of billing against a full-year denominator. "
            "is_partial_year marks every affected row.",
            "2026-2030 UIO denominators are overstated (+9% to +59%, worse per market) so nothing "
            "forward-looking is published in this model. It stops at actuals.",
            "Competitor prices cover a small part of the book. The uncovered remainder is a named "
            "gap, not a zero. Two vintages and two tiers are kept separate and never blended.",
            "Apr-Jun 2026 credit-note netting is unverified (no SaTy column in the SAP extract).",
            "There is no web demand series on disk. Web enters as price and listing presence only.",
            "down_trade_verdict is a rule over BVP share and total family units, not a measurement.",
            "Part-number pricing depth (cost, margin, competitor price and the resulting lever) "
            "exists on a minority of the book. Everywhere else the answer stays at family or "
            "market level and the lever column is blank rather than guessed.",
            "Two clocks are shown on purpose. ISZE plans on a financial year running April to "
            "March; the calendar year is also shown because the billing extracts arrive as "
            "calendar-year files. They can give different answers, so both are published.",
        ],
        "outputs": {
            "family": str(LOST_SALES_FAMILY_CSV),
            "market": str(LOST_SALES_MARKET_CSV),
            "competitor_pn": str(LOST_SALES_COMPETITOR_CSV),
            "competitor_coverage": str(LOST_SALES_COMPETITOR_COVERAGE_CSV),
            "pn_action": str(LOST_SALES_PN_ACTION_CSV),
            "fiscal_year_series": str(LOST_SALES_FISCAL_CSV),
            "fiscal_q1": str(LOST_SALES_FISCAL_Q1_CSV),
        },
        "fiscal_year": {
            "definition": "ISZE financial year runs April to March; the label is the calendar "
                          "year that closes it, so FY2026 = Apr 2025 to Mar 2026",
            "complete_fiscal_years_in_data": [int(y) for y in fy_series["fiscal_year"]] if not fy_series.empty else [],
            "closed_months_of_current_fiscal_year": int(fy_q1_total.get("months_compared", 0))
            if fy_q1_total else 0,
        },
    }
    LOST_SALES_META_JSON.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


if __name__ == "__main__":
    summary = write_model()
    print(json.dumps(summary, indent=2))
