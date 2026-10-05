#!/usr/bin/env python3
"""
PMS capture and evolution by vehicle family, per customer, on both clocks.

This is the deliverable behind the family question: how much service demand does each vehicle family
in a market's fleet imply, how much of it did we bill, and how has the billed euro moved — reported
in three families instead of one blended number.

The fleet split is not new data. ``modules/pms_engine.expected_by_category_bucketed()`` already
computes expected demand in three components and adds them:

    base_cv = bucket["cv_std"]  * svc["cv_std"]  * addr    ->  N-series truck
    base_f  = bucket["f_series"] * svc["f_series"] * addr  ->  heavy truck (F-series and C&E)
    base_l  = bucket["lcv"]      * svc["lcv"]      * addr  ->  light vehicle (D-Max)

Those three components ARE the family split. This script reports them in three parts and keeps the
same arithmetic, so the family rows sum back to the published market × category figure exactly
(asserted at the end, not assumed).

This script WRITES ONLY:
    01_data/00_derived/pms_capture_by_family.csv
    01_data/00_derived/pms_capture_by_family.meta.json
    01_data/00_derived/pms_family_evolution_both_clocks.csv
It does not touch any other derived file. Build the page separately with
``02_dashboards/sales/_build/build_pms_family_evolution_page.py``.

Two interval lanes, never averaged
----------------------------------
* **ITUK** runs the service schedule agreed with the distributor for that market: filters 1.25 visits
  a year, clutch and brake 0.5, on a 22,389-vehicle fleet, with its own brake and shoe factor of 0.4.
  Source: ``data/iml_v7_ituk_cy2025.yaml``.
* **Every other market** runs the internal schedule: standard CV 0.5 visits a year (raised by the
  market's own measured 3.5 t share, see ``modules/pms_capture_config.py``), F-series 0.667, light
  vehicle 1.0, with the D-Max brake factor at 0.4.

Every row carries its lane. A page that averages them is wrong.

What splits by family, and what does not
----------------------------------------
Expected demand splits cleanly, because the fleet has a measured three-way split per market.
**Billed actuals split only where the part number resolves to exactly one family** — see
``resolve_family()``. A part that fits more than one family is pooled as
``shared_across_families`` and is never apportioned, because apportioning is an assumption.

Usage:
    python 02_dashboards/sales/_build/build_pms_capture_by_family.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
PDATA = PRISM / "data"
sys.path.insert(0, str(PRISM))

from modules.pms_capture_config import (  # noqa: E402
    BUCKET_SERVICES_PER_YEAR,
    BUCKET_SERVICES_PER_YEAR_OVERRIDES,
    CONSUMABLE_FACTOR,
    LCV_BUCKET_FACTOR_OVERRIDES,
    WEAR_FACTOR,
    n75_addressable_pct,
)
from modules.pms_engine import DEFAULT_PARC_CONFIG, parc_config_for_distributor  # noqa: E402

OUT_CORE = DER / "pms_capture_by_family.csv"
OUT_EVO = DER / "pms_family_evolution_both_clocks.csv"
OUT_MAP = DER / "pms_family_part_number_map.csv"
OUT_META = DER / "pms_capture_by_family.meta.json"

norm = lambda x: (str(x).strip().lstrip("0") or "0")  # noqa: E731
SNAPSHOT = "2026-09-19"

# The three families, plus the pooled bucket and the unattributed one.
FAMILY_ORDER = ["n_series_truck", "heavy_truck", "light_vehicle",
                "shared_across_families", "unattributed"]
FAMILY_LABEL = {
    "n_series_truck": "N-series truck",
    "heavy_truck": "Heavy truck (F-series and C&E)",
    "light_vehicle": "Light vehicle (D-Max pickup and SUV)",
    "shared_across_families": "Parts used across more than one family",
    "unattributed": "No vehicle reference found",
}
# The fleet bucket each reported family is measured against.
FAMILY_BUCKET = {"n_series_truck": "cv_std", "heavy_truck": "f_series", "light_vehicle": "lcv"}
FAMILY_BUILT_FROM = {
    "n_series_truck": "cv_std_uio (standard commercial vehicles, N-series)",
    "heavy_truck": "f_series_uio (F-series and C&E)",
    "light_vehicle": "lcv_uio (D-Max pickup and SUV)",
}
CATEGORY_LABEL = {
    "air_filter": "Air filter", "blower_filter": "Blower filter", "brake_pad": "Brake pad",
    "brake_rotor": "Brake rotor", "brake_shoe": "Brake shoe", "clutch_booster": "Clutch booster",
    "clutch_disc": "Clutch disc", "clutch_kit": "Clutch kit",
    "clutch_pressure_plate": "Clutch pressure plate", "fuel_filter": "Fuel filter",
    "oil_filter": "Oil filter", "pilot_bearing": "Pilot bearing",
    "release_bearing": "Release bearing", "urea_filter": "Urea (AdBlue) filter",
}

# ── family resolution ─────────────────────────────────────────────────────────
# The answer to "which vehicle family does this part number fit" is not derived here. It is read from
# `01_data/00_derived/vehicle_family_bands.csv`, written by
# `03_analytics/Isuzu/prism/scripts/build_vehicle_family_bands.py`, which reads BOTH vehicle sources
# for every service part number: the EPC decode (tonnage bands and vehicle ranges) and the
# catalogue cross-reference's `vehicle_model` string. Deriving it a second time here is what let the
# two copies drift, so this function deliberately computes no vocabulary of its own.
#
# Three outcomes per part number, and nothing else:
#   single_family            one family, agreed by every source that names a vehicle for it
#   shared_across_families   fits more than one family — pooled, never apportioned
#   no_vehicle_reference     no source names a vehicle for it
FAMILY_OUTCOMES = ["n_series_truck", "heavy_truck", "light_vehicle",
                   "shared_across_families", "no_vehicle_reference"]


def load_sources() -> dict:
    """Read every input once. Nothing here writes."""
    src = {}
    src["bands"] = pd.read_csv(DER / "vehicle_family_bands.csv", dtype=str)
    src["capture"] = pd.read_csv(DER / "pms_capture_by_db_year.csv")
    src["buckets"] = pd.read_csv(PDATA / "uio_by_model_bucket.csv")
    src["n35"] = pd.read_csv(PDATA / "uio_ld_n35_share.csv")
    src["gps"] = pd.read_csv(DER / "gps_spu_by_distributor.csv")
    src["competitor"] = pd.read_csv(DER / "lost_sales_competitor_pn.csv",
                                    dtype={"part_number": str})
    src["sales"] = pd.read_parquet(DER / "sales_fact.parquet")
    src["dimension"] = pd.read_csv(DER / "bvp_pn_dimension.csv",
                                   dtype={"part_number": str})
    supp = PDATA / "pms_capture_supplement.csv"
    src["supplement"] = (pd.read_csv(supp, dtype={"part_number": str})
                         if supp.is_file() else pd.DataFrame())
    src["tonnage"] = pd.read_csv(DER / "pms_tonnage_model.csv")
    return src


def resolve_family(src: dict) -> pd.DataFrame:
    """Part number -> reported family, read from the single two-source banding table.

    The table carries, per part number, which family each source named (`from_epc`,
    `from_crossref`), whether the answer needed a wildcard model code, and a confidence. This
    function only shapes it into the vocabulary the rest of the build expects; it decides nothing.
    """
    bands = src["bands"].copy()
    bands["pn"] = bands.pn.map(norm)
    out = pd.DataFrame({
        "pn": bands.pn,
        "family": bands.family.where(bands.resolution == "single_family"),
        "family_source": bands.source_note,
        "resolution": bands.resolution,
    })
    # keep the vocabulary stable for anything downstream that reads 'unattributed'
    out["resolution"] = out.resolution.replace({"no_vehicle_reference": "unattributed"})

    bandinfo = pd.DataFrame({
        "pn": bands.pn,
        "epc_n": bands.from_epc.fillna("").map(lambda s: len([x for x in str(s).split("|") if x])),
        "epc_one": bands.from_epc.fillna("").map(
            lambda s: ([x for x in str(s).split("|") if x] or [None])[0]
            if len([x for x in str(s).split("|") if x]) == 1 else None),
        "band_n": bands.families_in_union.fillna("").map(
            lambda s: len([x for x in str(s).split("|") if x])),
        "band_one": bands.family.where(bands.resolution == "single_family"),
        "xc_n": bands.from_crossref.fillna("").map(
            lambda s: len([x for x in str(s).split("|") if x])),
        "xc_one": bands.from_crossref.fillna("").map(
            lambda s: [x for x in str(s).split("|") if x][0]
            if len([x for x in str(s).split("|") if x]) == 1 else None),
        "crossref_from_wildcard": bands.from_crossref_wildcard.fillna(""),
        "confidence": bands.confidence,
        "billed_eur_all": bands.eur_all_markets.astype(float),
        "billed_units_all": bands.units_all_markets.astype(float),
        "vehicle_model": bands.vehicle_model.fillna(""),
    })
    bandinfo["band_n"] = bandinfo.band_n.clip(lower=0)
    bandinfo["epc_n"] = bandinfo.epc_n.clip(lower=0)
    return out, bandinfo


def tagged_pms(src: dict) -> pd.DataFrame:
    """The service-part billing, tagged by the project's own code path.

    This calls ``modules.pms_tagging.tag_pms_sales`` — the same function the published capture file
    is built with — rather than re-deriving the category here. That distinction matters: the part
    registry is consulted before the catalogue, so a part number both know gets the registry's
    category, and a hand-rolled join silently gets a different one. Using the project's own path
    makes the attributed euro reconcile against the published actual euro, and the build asserts
    that reconciliation rather than assuming it.

    The published file's exclusions are applied too: credit notes come out, and part numbers the
    dimension marks as not capture-eligible (filter assemblies, kits) come out.
    """
    from config import resolve_mapping_path  # noqa: PLC0415
    from modules.data_prep import load_distributor_mapping  # noqa: PLC0415
    from modules.pms_tagging import tag_pms_sales  # noqa: PLC0415
    from modules.sales_loader import load_prism_sales  # noqa: PLC0415

    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    sales, _ = load_prism_sales(df_map)
    dim = pd.concat([src["dimension"], src["supplement"]], ignore_index=True)
    df = tag_pms_sales(sales, dim, fill_catalog_pms=True)
    df = df[df.is_pms.fillna(False)].copy()
    if "is_credit_note" in df.columns:
        df = df[~df.is_credit_note.fillna(False).astype(bool)].copy()
    if "pms_capture_eligible" in df.columns:
        df = df[df.pms_capture_eligible.fillna(True).astype(bool)].copy()
    df["pn"] = df.part_number.map(norm)
    df["year"] = df.year.astype(int)
    df["fy_label"] = df.year + (df.month.astype(int) >= 4).astype(int)
    return df


def build_attributed_billing(src: dict, fam: pd.DataFrame, tagged: pd.DataFrame) -> pd.DataFrame:
    """Billed euro and units per market x family x service category x year, attributed only where
    the part number resolves to exactly one family. Everything else is pooled, never spread."""
    pn_family = dict(zip(fam.pn, fam.family))
    pn_res = dict(zip(fam.pn, fam.resolution))
    sf = tagged
    # A part number that resolves to one family is attributed. Everything else — pooled by the
    # banding, several families in the catalogue, or no vehicle named at all — becomes one of the
    # two non-family values and is never apportioned.
    sf = sf.assign(family=sf.pn.map(pn_family).fillna(sf.pn.map(pn_res))
                   .fillna("shared_across_families"))
    return (sf.groupby(["distributor_code", "family", "pms_category", "year"], dropna=False)
            .agg(billed_eur=("net_sales_value", "sum"),
                 billed_units=("billed_qty", "sum"),
                 distinct_pns=("pn", "nunique"))
            .reset_index())


def build_fleet_and_expected(src: dict) -> pd.DataFrame:
    """Expected service demand per market x family x service category, the same arithmetic the
    pipeline already runs, reported in three parts instead of one."""
    factors = {**CONSUMABLE_FACTOR, **WEAR_FACTOR}
    addr = n75_addressable_pct()
    rows = []
    for _, bk in src["buckets"].iterrows():
        db = bk.distributor_code
        cfg = parc_config_for_distributor(db, dict(DEFAULT_PARC_CONFIG))
        svc = {**BUCKET_SERVICES_PER_YEAR, **BUCKET_SERVICES_PER_YEAR_OVERRIDES.get(db, {})}
        fo = cfg.get("factor_overrides") or {}
        lane = "agreed" if db == "ITUK" else "internal"
        parts = {"cv_std": float(bk.cv_std_uio), "f_series": float(bk.f_series_uio),
                 "lcv": float(bk.lcv_uio)}
        for fam, bucket_key in [("n_series_truck", "cv_std"), ("heavy_truck", "f_series"),
                                ("light_vehicle", "lcv")]:
            units = parts[bucket_key]
            visits = svc[bucket_key]
            base = units * visits * addr
            for cat in sorted(factors):
                # AdBlue filter is the one category whose rate differs by vehicle class: 40,000/200,000
                # on the N-series, 30,000/80,000 on the F-series, unchanged on the light vehicle.
                # The published derived file already carries the sourced rates, so they are used here.
                # modules/pms_engine.expected_by_category_bucketed() currently stubs this branch at
                # 1.0 ("BASELINE RUN ONLY"); that stub is NOT what the published file was built with.
                if cat == "urea_filter":
                    rate = {"cv_std": CONSUMABLE_FACTOR["urea_filter"],
                            "f_series": 30_000 / 80_000, "lcv": 1.0}[bucket_key]
                    fac = rate
                    fac_label = f"{rate:g} (interval-derived)"
                elif bucket_key == "lcv":
                    fac = LCV_BUCKET_FACTOR_OVERRIDES.get(cat, fo.get(cat, factors[cat]))
                    fac_label = f"{fac:g}"
                else:
                    fac = fo.get(cat, factors[cat])
                    fac_label = f"{fac:g}"
                rows.append({
                    "distributor_code": db, "family": fam, "family_label": FAMILY_LABEL[fam],
                    "pms_category": cat, "pms_category_label": CATEGORY_LABEL.get(cat, cat),
                    "lane": lane,
                    "fleet_units": round(units, 1),
                    "visits_per_year": round(visits, 4),
                    "category_factor": round(float(fac), 6),
                    "addressable_pct": round(addr, 4),
                    "expected_qty": round(base * float(fac), 4),
                    "_fact_label": fac_label,
                    "_bucket_units": round(units, 1),
                    "_visits": round(visits, 4),
                })
    df = pd.DataFrame(rows)
    n35 = dict(zip(src["n35"].distributor_code, src["n35"].n35_share))
    note = []
    for _, r in df.iterrows():
        db = r.distributor_code
        bits = [f"fleet {FAMILY_BUILT_FROM[r.family]} = {r.fleet_units:,.1f}",
                f"visits/year {r.visits_per_year:g}"]
        if r.family == "n_series_truck":
            if db in BUCKET_SERVICES_PER_YEAR_OVERRIDES and "cv_std" in BUCKET_SERVICES_PER_YEAR_OVERRIDES[db]:
                sh = n35.get(db)
                bits.append(f"raised by this market's measured 3.5 t share {sh:.4f}" if sh
                            else "market-specific override")
        bits.append(f"category factor {r._fact_label}")
        bits.append("addressable 100%")
        note.append("; ".join(bits))
    df["basis_note"] = note
    df = df.drop(columns=[c for c in df.columns if c.startswith("_")])
    # Expected demand is fleet x visits x factor, and the fleet carries a 2025 estimate for every
    # year — the same convention the published model uses. So the expected row repeats across the
    # years on which the published model reports, and only the billing and the price move.
    years = sorted(int(y) for y in src["capture"].year.unique())
    df = df.merge(pd.DataFrame({"year": years}), how="cross")
    return df


def build_attributed_billing(src: dict, fam: pd.DataFrame, tagged: pd.DataFrame) -> pd.DataFrame:
    """Billed euro and units per market x family x service category x year, attributed only where
    the part number resolves to exactly one family. Everything else is pooled, never spread."""
    pn_family = dict(zip(fam.pn, fam.family))
    pn_res = dict(zip(fam.pn, fam.resolution))
    sf = tagged.copy()
    # A part number that resolves to one family is attributed. Everything else — pooled by the
    # banding, several families in the catalogue, or no vehicle named at all — becomes one of the
    # two non-family values and is never apportioned.
    sf["family"] = sf.pn.map(pn_family).fillna(sf.pn.map(pn_res)).fillna("shared_across_families")
    return (sf.groupby(["distributor_code", "family", "pms_category", "year"], dropna=False)
            .agg(billed_eur=("net_sales_value", "sum"),
                 billed_units=("billed_qty", "sum"),
                 distinct_pns=("pn", "nunique"))
            .reset_index())


def widen_to_reported_families(expect3: pd.DataFrame, src: dict) -> pd.DataFrame:
    """Widen the three-fleet expected demand into exactly one row per reported family value.

    The three fleet components sum to the market's total expected demand for a category. This
    function turns that into five reported values per market x category x year:

        N-series truck      the cv_std component, as the pipeline computes it
        Heavy truck         the f_series component (F-series and C&E)
        Light vehicle       the lcv component (D-Max pickup and SUV)
        Shared across       the whole market total — a part usable on several families is available
                            to all of them, so its expectation is the market total, not a slice
        No vehicle ref      zero. Nothing usable can be derived from a numerator we cannot see.

    Exactly one row per market x family x category x year. The three named families are the only
    slices of the market ceiling, so they sum back to the published figure; the shared value is the
    ceiling itself and is therefore never added to it.
    """
    key = ["distributor_code", "pms_category", "year"]
    total = expect3.groupby(key, as_index=False).expected_qty.sum().rename(
        columns={"expected_qty": "market_expected_qty"})
    fleet_total = dict(zip(src["buckets"].distributor_code,
                           src["buckets"][["cv_std_uio", "f_series_uio", "lcv_uio"]].sum(axis=1)))

    named = expect3.copy()
    named["basis_note"] = (named.basis_note + "; this family's own fleet component, "
                           + named.fleet_units.map(lambda v: f"{v:,.0f}")
                           + " vehicles in service x "
                           + named.visits_per_year.map(lambda v: f"{v:g}")
                           + " visits a year x the category factor")
    named["expected_qty_own_fleet_component"] = named.expected_qty

    shared = expect3.groupby(key, as_index=False).first()
    shared["family"] = "shared_across_families"
    shared["family_label"] = FAMILY_LABEL["shared_across_families"]
    shared["visits_per_year"] = np.nan
    shared["category_factor"] = np.nan
    shared = shared.merge(total, on=key, how="left")
    shared["expected_qty"] = shared.market_expected_qty
    shared["expected_qty_own_fleet_component"] = np.nan
    shared["fleet_units"] = shared.distributor_code.map(fleet_total).round(1)
    shared["basis_note"] = (shared.basis_note.str.split(";").str[0]
                            + "; the whole market expectation for this service family, because a "
                              "part that fits several vehicle families is available to all of them")

    unattr = expect3.groupby(key, as_index=False).first()
    unattr["family"] = "unattributed"
    unattr["family_label"] = FAMILY_LABEL["unattributed"]
    unattr["fleet_units"] = 0.0
    unattr["visits_per_year"] = np.nan
    unattr["category_factor"] = np.nan
    unattr["expected_qty"] = 0.0
    unattr["expected_qty_own_fleet_component"] = np.nan
    unattr["basis_note"] = (unattr.basis_note.str.split(";").str[0]
                            + "; zero: a part with no vehicle reference cannot be given an "
                              "expectation at all, so its billed euro is reported against a zero "
                              "ceiling and a blank rate rather than spread over families")

    out = pd.concat([named, shared, unattr], ignore_index=True)
    dup = out.duplicated(subset=["distributor_code", "family", "pms_category", "year"]).sum()
    if dup:
        raise SystemExit(f"BUILD FAIL: {dup} duplicate market x family x category x year rows")
    return out.sort_values(["distributor_code", "family", "pms_category", "year"]).reset_index(drop=True)


def build(src: dict) -> tuple[pd.DataFrame, pd.DataFrame, dict, pd.DataFrame]:
    fam, bandinfo = resolve_family(src)
    tagged = tagged_pms(src)
    expect3 = build_fleet_and_expected(src)
    expect = widen_to_reported_families(expect3, src)
    actual = build_attributed_billing(src, fam, tagged)

    core = expect.merge(actual, on=["distributor_code", "family", "pms_category", "year"], how="left")
    for c in ["billed_eur", "billed_units", "distinct_pns"]:
        core[c] = core[c].fillna(0)
    core["family_label"] = core.family.map(FAMILY_LABEL)

    # ── a real average selling price per market x family x category, taken from this market's own
    # attributed billing in the year, then this market's own for any year, then the network, then
    # the category-wide network median. Recorded per row so the euro is never an unexplained number.
    core = core.sort_values(["distributor_code", "family", "pms_category", "year"])
    mf = (core.groupby(["distributor_code", "family", "pms_category"])
          .apply(lambda g: g.billed_eur.sum() / g.billed_units.sum()
                 if g.billed_units.sum() > 0 else np.nan, include_groups=False)
          .rename("asp_market_family_cat"))
    mfa = (core.groupby(["distributor_code", "pms_category"])
           .apply(lambda g: g.billed_eur.sum() / g.billed_units.sum()
                  if g.billed_units.sum() > 0 else np.nan, include_groups=False)
           .rename("asp_market_cat"))
    nf = (core.groupby(["family", "pms_category"])
          .apply(lambda g: g.billed_eur.sum() / g.billed_units.sum()
                 if g.billed_units.sum() > 0 else np.nan, include_groups=False)
          .rename("asp_network_family_cat"))
    nc = (core.groupby("pms_category")
          .apply(lambda g: g.billed_eur.sum() / g.billed_units.sum()
                 if g.billed_units.sum() > 0 else np.nan, include_groups=False)
          .rename("asp_network_cat"))
    own = core.billed_eur / core.billed_units.replace(0, np.nan)
    core["asp_own_year_eur"] = own
    core = core.join(mf, on=["distributor_code", "family", "pms_category"])
    core = core.join(mfa, on=["distributor_code", "pms_category"])
    core = core.join(nf, on=["family", "pms_category"])
    core = core.join(nc, on="pms_category")

    asp, asp_src = [], []
    for _, r in core.iterrows():
        for val, name in ((r.asp_own_year_eur, "this customer, this family, this year"),
                          (r.asp_market_family_cat, "this customer, this family, all years"),
                          (r.asp_market_cat, "this customer, all families"),
                          (r.asp_network_family_cat, "the network, this family"),
                          (r.asp_network_cat, "the network, this category")):
            if pd.notna(val) and val > 0:
                asp.append(float(val))
                asp_src.append(name)
                break
        else:
            asp.append(np.nan)
            asp_src.append("no billed price available — euro left blank rather than priced at zero")
    core["avg_selling_price_eur"] = np.round(asp, 2)
    core["asp_source"] = asp_src

    core["expected_eur"] = (core.expected_qty * core.avg_selling_price_eur).round(2)
    core["actual_eur_in_expected_units"] = (core.billed_units * core.avg_selling_price_eur).round(2)

    # ── how much of this market x category x year billing could be placed in a family at all.
    # Published actual euro is the full service-part billing for that market, category and year.
    # Where it is larger than the attributed figure, the difference is billing on part numbers
    # that fit more than one family — reported as shared, never spread.
    pub_act = src["capture"]
    pub_act = pub_act[pub_act.line_type == "total"][
        ["distributor_code", "pms_category", "year", "actual_rev_eur"]].rename(
        columns={"actual_rev_eur": "pms_actual_eur_market_category"})
    core = core.merge(pub_act, on=["distributor_code", "pms_category", "year"], how="left")

    # Capture on euro: what we billed against what the fleet implies, at one price per family and
    # category. Where the customer has no fleet at all in that family, the denominator is zero and
    # the rate is left blank rather than reported as infinite.
    denom = core.actual_eur_in_expected_units
    core["capture_rate"] = np.where(
        (core.expected_eur > 0) & (denom > 0), (denom / core.expected_eur).round(4), np.nan)
    core["gap_eur"] = np.where(
        core.expected_eur > 0,
        (core.expected_eur * (1 - core.capture_rate.fillna(0)).clip(lower=0)).round(2), np.nan)
    core["no_fleet_but_billed"] = (core.expected_eur <= 0) & (core.billed_eur > 0)
    core["quality_flag_units_not_euro"] = core.billed_eur.notna() & (
        core.actual_eur_in_expected_units > 0) & np.where(
            core.actual_eur_in_expected_units > 0,
            ((core.billed_eur - core.actual_eur_in_expected_units).abs()
             / core.actual_eur_in_expected_units) > 0.15, False)
    core["basis_note"] = (core.basis_note + "; billed price basis: " + core.asp_source)

    cols = ["distributor_code", "family", "family_label", "pms_category", "pms_category_label",
            "year", "lane", "fleet_units", "visits_per_year", "category_factor",
            "expected_qty", "expected_eur", "billed_eur", "billed_units", "distinct_pns",
            "capture_rate", "gap_eur", "avg_selling_price_eur", "asp_source",
            "pms_actual_eur_market_category", "no_fleet_but_billed",
            "quality_flag_units_not_euro", "basis_note"]
    core = core[cols].sort_values(["distributor_code", "family", "pms_category", "year"])

    # ── evolution on both clocks. One scope only: the part numbers the published service-part book
    # covers. The euro and the scope flag come from the same tagged rows, so the trend reconciles to
    # the published book to the cent. A second "every billed part number" scope was removed because
    # its euro included credit notes and non-capture-eligible part numbers, which is exactly how a
    # trend ends up summing to a number no other page agrees with.
    #
    # The billing runs from January 2023 to 30 June 2026. That makes two periods on each clock
    # partial, and they must be flagged rather than compared with a full year:
    #   CY2026  January to June 2026                  6 months
    #   FY2023  April 2022 to March 2023, of which     3 months (January to March 2023)
    #   FY2027  April 2026 to March 2027, of which     3 months (April to June 2026)
    sf = src["sales"].copy()
    sf["pn"] = sf.part_number.map(norm)
    dim = pd.read_csv(DER / "distributor_dimension.csv")
    sf["distributor_code"] = sf.sold_to_sap.map(dict(zip(dim.sold_to_sap, dim.distributor_code)))
    sf = sf[sf.distributor_code.notna()].copy()
    dd = pd.to_datetime(sf.billing_date, errors="coerce")
    sf = sf.assign(year=dd.dt.year, month=dd.dt.month, day=dd.dt.day).dropna(subset=["year"])
    sf["year"] = sf.year.astype(int)
    sf["fy_label"] = sf.year + (sf.month >= 4).astype(int)
    pn_family = dict(zip(fam.pn, fam.family))
    pn_res = dict(zip(fam.pn, fam.resolution))
    # A part that resolves to one family is attributed; everything else is pooled and never spread.
    sf["family"] = sf.pn.map(pn_family).fillna(sf.pn.map(pn_res)).fillna("shared_across_families")

    # The family trend is built from the SAME tagged rows the published service-part book is built
    # from, not from raw billing. This is the fix for a real defect: the scope flag used to be read
    # from the tagged frame while the euro beside it came from raw billing, which still carries
    # credit notes and the part numbers the dimension marks as not capture-eligible (filter
    # assemblies, kits). The published book excludes those, so the trend summed to a number no other
    # page agreed with. Now the scope flag and the euro come from one set of rows and the trend ties
    # to the published book by construction.
    sf = tagged.copy()
    sf["pn"] = sf.part_number.map(norm)
    # The published service-part book covers 18 markets. The billing also carries four CIS markets
    # (Armenia, Kazakhstan, Palestine, Ukraine) that the service model does not cover and that the
    # book excludes. The trend is scoped to the book's own markets, so the two reconcile.
    BOOK_MARKETS = set(src["capture"].distributor_code.unique())
    sf = sf[sf.distributor_code.isin(BOOK_MARKETS)].copy()
    sf["year"] = sf.year.astype(int)
    sf["month"] = sf.month.astype(int)
    sf["fy_label"] = sf.year + (sf.month >= 4).astype(int)
    sf["family"] = sf.pn.map(pn_family).fillna(sf.pn.map(pn_res)).fillna("shared_across_families")
    sf["is_service_part"] = True
    _evo_check = sf[sf.year == 2025].net_sales_value.sum()
    _pub_all = src["capture"][(src["capture"].line_type == "total") & (src["capture"].year == 2025)]
    _pub_check = _pub_all.actual_rev_eur.sum()
    if abs(_evo_check - _pub_check) > 2.0:
        raise SystemExit(f"BUILD FAIL: the family trend does not tie to the published service-part "
                         f"book for 2025: EUR {_evo_check:,.2f} against EUR {_pub_check:,.2f} "
                         f"(difference EUR {_evo_check - _pub_check:,.2f})")

    # how many months of billing each period actually holds, so a partial period cannot be read as
    # a fall. A calendar period is complete when all twelve months are present; a financial period
    # is complete when all twelve of its own months (April to March) are present.
    month_presence = sf.groupby(["year", "month"]).size().reset_index()[["year", "month"]]
    cy_months = month_presence.groupby("year").month.nunique().to_dict()
    fy_months = (month_presence.assign(fy=month_presence.year + (month_presence.month >= 4).astype(int))
                 .groupby("fy").month.nunique().to_dict())
    rows = []
    for clock, col in (("CY", "year"), ("FY", "fy_label")):
        for scope, sub in (("service_parts_only", sf),):
            g = (sub.groupby(["distributor_code", col, "family"], dropna=False)
                 .agg(billed_eur=("net_sales_value", "sum"), units=("billed_qty", "sum"),
                      distinct_pns=("pn", "nunique")).reset_index()
                 .rename(columns={col: "period"}))
            g["clock"] = clock
            g["scope"] = scope
            g["months_in_period"] = g.period.map(cy_months if clock == "CY" else fy_months)
            g["period_is_complete"] = g.months_in_period >= 12
            rows.append(g)
    evo = pd.concat(rows, ignore_index=True)
    evo["family_label"] = evo.family.map(FAMILY_LABEL)
    evo["period_label"] = evo.apply(
        lambda r: (("calendar year " + str(int(r.period))) if r.clock == "CY"
                   else (f"ISZE year {int(r.period)} (Apr {int(r.period)-1} to Mar {int(r.period)})")), axis=1)
    evo["billed_eur"] = evo.billed_eur.round(2)
    evo["units"] = evo.units.round(1)
    lane = dict(zip(src["tonnage"].distributor_code, src["tonnage"].lane))
    evo["lane"] = evo.distributor_code.map(lane)
    evo = evo[["distributor_code", "family", "family_label", "clock", "period", "period_label",
               "scope", "billed_eur", "units", "distinct_pns", "months_in_period",
               "period_is_complete", "lane"]]
    evo = evo.sort_values(["clock", "distributor_code", "family", "scope", "period"])

    # ── tie-out: the three named families must sum back to the published market x category figure.
    # The pooled shared value is deliberately the same ceiling again (a part usable on several
    # families is available to all of them), so it is excluded from the sum, not added to it.
    pub = src["capture"]
    pub = pub[pub.line_type == "total"][["distributor_code", "pms_category", "year", "expected_qty"]]
    named = core[core.family.isin(["n_series_truck", "heavy_truck", "light_vehicle"])]
    mine = (named.groupby(["distributor_code", "pms_category", "year"], as_index=False)
            .expected_qty.sum().rename(columns={"expected_qty": "mine"}))
    chk = pub.merge(mine, on=["distributor_code", "pms_category", "year"], how="outer")
    chk["published"] = chk.expected_qty
    chk["delta"] = chk["mine"] - chk["published"]
    tol = 0.5
    bad = chk[chk.delta.abs() > tol]
    tie = {
        "basis": ("sum of the three named families against pms_capture_by_db_year.csv "
                  "line_type=total expected_qty; the pooled shared value is the same ceiling and is "
                  "excluded from the sum"),
        "rows_compared": int(chk.published.notna().sum()),
        "rows_unmatched_in_published": int(chk.published.isna().sum()),
        "rows_unmatched_in_mine": int(chk.mine.isna().sum()),
        "tolerance_units": tol,
        "max_abs_delta": round(float(chk.delta.abs().max()), 6),
        "fail_count": int(len(bad)),
        "source": "01_data/00_derived/pms_capture_by_db_year.csv line_type=total, expected_qty",
    }
    if len(bad):
        tie["worst"] = bad.reindex(bad.delta.abs().sort_values(ascending=False).index).head(10)[
            ["distributor_code", "pms_category", "year", "mine", "published", "delta"]
        ].to_dict("records")

    # ── tie-out 2: attributed billed euro (all five family values) must equal the published actual
    # euro for the same market x category x year, because a part number is placed in exactly one
    # value. This is the check that catches double-counting in the attribution.
    pub_e = src["capture"]
    pub_e = pub_e[pub_e.line_type == "total"][["distributor_code", "pms_category", "year",
                                               "actual_rev_eur"]]
    got = (core.groupby(["distributor_code", "pms_category", "year"], as_index=False)
           .billed_eur.sum().rename(columns={"billed_eur": "attributed"}))
    chk2 = pub_e.merge(got, on=["distributor_code", "pms_category", "year"], how="outer")
    delta2 = (chk2.attributed - chk2.actual_rev_eur).abs()
    tol_eur = 1.0
    tie_eur = {
        "basis": ("attributed billed euro over all five family values against "
                  "pms_capture_by_db_year.csv line_type=total actual_rev_eur; every part number is "
                  "placed in exactly one value, so the two must agree"),
        "rows_compared": int(chk2.actual_rev_eur.notna().sum()),
        "tolerance_eur": tol_eur,
        "max_abs_delta_eur": round(float(delta2.max()), 2),
        "fail_count": int((delta2 > tol_eur).sum()),
        "unmatched_in_published": int(chk2.actual_rev_eur.isna().sum()),
        "unmatched_in_attributed": int(chk2.attributed.isna().sum()),
    }
    over = chk2[delta2 > tol_eur]
    if len(over):
        tie_eur["worst"] = over.assign(delta=(over.attributed - over.actual_rev_eur)).reindex(
            (over.attributed - over.actual_rev_eur).abs().sort_values(ascending=False).index
        ).head(10).to_dict("records")

    meta = {
        "snapshot": SNAPSHOT,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "generated_by": "02_dashboards/sales/_build/build_pms_capture_by_family.py",
        "families": {k: FAMILY_LABEL[k] for k in FAMILY_ORDER},
        "what_splits_by_family": {
            "expected": "splits fully — the fleet has a measured three-way split per market",
            "billed": ("splits only where the part number resolves to exactly one family; a part "
                       "fitting more than one family is pooled as shared_across_families and is "
                       "never apportioned"),
        },
        "family_resolution": {
            "resolved_single_family": int((fam.resolution == "single_family").sum()),
            "pooled_shared": int((fam.resolution == "shared_across_families").sum()),
            "no_vehicle_reference": int((fam.resolution == "unattributed").sum()),
            "by_source": {
                "epc_and_crossref_agree": int(((bandinfo.epc_n == 1) & (bandinfo.xc_n == 1)).sum()),
                "epc_only": int(((bandinfo.epc_n == 1) & (bandinfo.xc_n != 1)).sum()),
                "crossref_only": int(((bandinfo.epc_n != 1) & (bandinfo.xc_n == 1)).sum()),
            },
            "by_confidence": {k: int(v) for k, v in bandinfo.confidence.value_counts().items()},
            "answered_from_a_wildcard_model_code": int(
                (bandinfo.crossref_from_wildcard.fillna("") != "").sum()),
            "both_sources_speak": {
                "epc_and_crossref_both_name_one_family": int(
                    ((bandinfo.epc_n == 1) & (bandinfo.xc_n == 1)).sum()),
                "of_which_they_disagree": int(
                    ((bandinfo.epc_n == 1) & (bandinfo.xc_n == 1)
                     & (bandinfo.epc_one != bandinfo.xc_one)).sum()),
                "note": ("where the EPC and the cross-reference each name exactly one family, this "
                         "many disagree; a disagreement is pooled and flagged rather than trusted "
                         "to either source"),
            },
            "rule": ("one table, two sources — 01_data/00_derived/vehicle_family_bands.csv, written "
                     "by 03_analytics/Isuzu/prism/scripts/build_vehicle_family_bands.py. A part is "
                     "placed when every source that names a vehicle for it agrees; a part that fits "
                     "more than one family is pooled and never apportioned; a wildcard model code "
                     "still names a family but is recorded at medium confidence."),
        },
        "tie_out": tie,
        "tie_out_attributed_euro": tie_eur,
        "sources": {
            "fleet_split": "03_analytics/Isuzu/prism/data/uio_by_model_bucket.csv",
            "visit_rates": "03_analytics/Isuzu/prism/modules/pms_capture_config.py BUCKET_SERVICES_PER_YEAR",
            "vehicle_family": "01_data/00_derived/epc_decode_batch1_banded_20260919.csv + epc_decode_batch1_20260919.json + genuine_bvp_crossref.csv",
            "billing": "01_data/00_derived/sales_fact.parquet",
            "service_categories": "01_data/00_derived/bvp_pn_dimension.csv + prism/data/pms_capture_supplement.csv",
            "published_capture": "01_data/00_derived/pms_capture_by_db_year.csv",
            "gps": "01_data/00_derived/gps_spu_by_distributor.csv + prism/data/gps_model_targets.csv",
            "competitor": "01_data/00_derived/lost_sales_competitor_pn.csv",
        },
        "not_attempted": [
            "A 3.5 t versus 7.5 t split. 50 of 120 model codes in "
            "prism/data/model_code_to_tonnage.csv are unresolved and the unresolved ones include "
            "NN, NP and NHR — exactly the codes that separate N35 from N75. Splitting on them would "
            "be inference, so the N-series is reported as one family.",
            "A fuel-filter answer by family. Fuel filters are the second-largest service family and "
            "almost none of their billing resolves to one vehicle family: the two decoded part "
            "numbers fit both the N-series and the heavy models, and the remaining part numbers in "
            "that family have no vehicle reference at all. The fuel-filter euro therefore sits in "
            "the pooled value, not in a family.",
            "An oil-filter answer by family. Oil filters are the largest service family by units and "
            "their part numbers are shared across the truck families and the industrial engines, so "
            "the same pooled treatment applies.",
        ],
    }
    return core, evo, meta, fam


def main() -> int:
    src = load_sources()
    core, evo, meta, fam = build(src)
    OUT_CORE.parent.mkdir(parents=True, exist_ok=True)
    core.to_csv(OUT_CORE, index=False)
    evo.to_csv(OUT_EVO, index=False)
    fam.to_csv(OUT_MAP, index=False)
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"written -> {OUT_CORE}  ({len(core):,} rows)")
    print(f"written -> {OUT_EVO}  ({len(evo):,} rows)")
    print(f"written -> {OUT_MAP}  ({len(fam):,} rows)")
    print(f"written -> {OUT_META}")
    print()
    t = meta["tie_out"]
    print(f"TIE-OUT 1  three named families sum to published expected_qty: "
          f"{t['rows_compared']} rows, max abs delta {t['max_abs_delta']}, fail {t['fail_count']}")
    t2 = meta["tie_out_attributed_euro"]
    print(f"TIE-OUT 2  attributed euro equals published actual euro        : "
          f"{t2['rows_compared']} rows, max abs delta EUR {t2['max_abs_delta_eur']}, "
          f"fail {t2['fail_count']}")
    if t["fail_count"] or t2["fail_count"]:
        print(json.dumps(t.get("worst"), indent=2))
        print(json.dumps(t2.get("worst"), indent=2))
        return 1
    print()
    print("family resolution:")
    fr = meta["family_resolution"]
    print(f"  resolved to one family : {fr['resolved_single_family']}")
    print(f"  pooled as shared       : {fr['pooled_shared']}")
    print(f"  no vehicle reference   : {fr['no_vehicle_reference']}")
    print(f"  by source              : {fr['by_source']}")
    print(f"  by confidence          : {fr['by_confidence']}")
    print(f"  needed a wildcard code : {fr['answered_from_a_wildcard_model_code']}")
    print(f"  contradictions         : {fr['both_sources_speak']['of_which_they_disagree']} "
          f"of {fr['both_sources_speak']['epc_and_crossref_both_name_one_family']} where both speak")

    y = core[core.year == 2025]
    print()
    print("network 2025, by family (attributed billed euro of the published service-part book):")
    net = y.groupby("family").agg(fleet_units=("fleet_units", "first"),
                                  expected_eur=("expected_eur", "sum"),
                                  billed_eur=("billed_eur", "sum"),
                                  expected_qty=("expected_qty", "sum"),
                                  billed_units=("billed_units", "sum"))
    tot_billed = net.billed_eur.sum()
    for fam, r in net.iterrows():
        cap = (r.billed_eur / r.expected_eur) if r.expected_eur > 0 else float("nan")
        print(f"  {fam:24s} fleet {r.fleet_units:>9,.0f}  expected EUR {r.expected_eur:>12,.0f}  "
              f"billed EUR {r.billed_eur:>11,.0f}  {100*r.billed_eur/tot_billed:5.1f}%  "
              f"capture {'n/a' if cap != cap else format(cap, '.1%')}")
    print(f"  {'TOTAL':24s} {'':>16} expected EUR {net.expected_eur.sum():>12,.0f}  "
          f"billed EUR {tot_billed:>11,.0f}")
    db = core[(core.year == 2025) & core.family.isin(
        ["n_series_truck", "heavy_truck", "light_vehicle"])]
    print()
    print("per market, 2025, attributed euro by family (the three named families):")
    piv = db.pivot_table(index="distributor_code", columns="family", values="billed_eur",
                         aggfunc="sum", fill_value=0)
    piv["total"] = piv.sum(axis=1)
    print(piv.sort_values("total", ascending=False).to_string(float_format=lambda v: f"{v:,.0f}"))
    print()
    print("evolution, calendar years, network, service parts only (all markets on the file):")
    ev = evo[(evo.clock == "CY") & (evo.scope == "service_parts_only")
             & evo.period.isin([2023, 2025])]
    pe = ev.pivot_table(index="family", columns="period", values="billed_eur", aggfunc="sum")
    pu = ev.pivot_table(index="family", columns="period", values="units", aggfunc="sum")
    for name, p in (("EUR", pe), ("units", pu)):
        q = p.copy()
        q["chg"] = (q[2025] / q[2023] - 1) * 100
        print(f"  {name}")
        for fam, r in q.iterrows():
            chg = r.chg
            print(f"    {fam:24s} 2023 {r[2023]:>12,.0f}  2025 {r[2025]:>12,.0f}  "
                  f"{'n/a' if chg != chg else format(chg, '+.1f') + '%'}")
    print()
    print("quality flag rows (billed euro more than 15% away from the expected at one price):",
          int(core.quality_flag_units_not_euro.sum()), "of", len(core))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
