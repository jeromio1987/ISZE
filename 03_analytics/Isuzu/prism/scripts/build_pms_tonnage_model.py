#!/usr/bin/env python3
"""
PMS by tonnage band x AIM level, per customer, on both clocks.

Answers: for each market, how does the service demand split by vehicle weight band, what is the
capture, and how has it moved over the years — on the calendar year and on ISZE's April-March
financial year, at AIM level 1 and level 2 as well as by PMS service category.

Two interval lanes, never blended
--------------------------------
* **ITUK** runs the IML v7 schedule: filters 1.25 visits a year (40,000 km visit ÷ 50,000 km/yr),
  clutch and brake 0.5, on the 22,389-vehicle DVLA fleet. It also carries its own brake factor of
  0.4 on top. Source: ``iml_v7_ituk_cy2025.yaml``.
* **Every other market** runs the PRISM lane: 0.5 visits a year for standard CV, 0.667 for
  F-series, 1.0 for LCV, with D-Max brake at 0.4.

A row therefore always carries its lane, and the two are never summed into one capture figure.

What splits by band, and what does not
--------------------------------------
Expected demand splits cleanly: it is fleet × visits per year × category factor, and the fleet has
a measured band split per market. **Actual billed units do not split by band**, because the
billing carries no vehicle. So each row carries the band's expected demand beside the *market's*
actual and capture, with ``actual_is_market_level = True``. Anyone summing actuals down the band
column would double-count; the flag and a verifier check prevent it.

The fleet vintage is 2025E for every year, so expected demand is flat over time by construction.
What moves over time is the billing and the capture. That is stated, not hidden.

Usage:
    python 03_analytics/Isuzu/prism/scripts/build_pms_tonnage_model.py
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DERIVED_DIR, PRISM_DATA_DIR  # noqa: E402

BANDS_CSV = DERIVED_DIR / "pms_tonnage_model.csv"
AIM_CSV = DERIVED_DIR / "aim_evolution_model.csv"
META_JSON = DERIVED_DIR / "pms_tonnage_model.meta.json"

norm = lambda x: (str(x).strip().lstrip("0") or "0")  # noqa: E731

# Band definitions. The three N-series rungs plus LCV and F-series, which are vehicle classes.
# The 5.5 t rung was added 2026-09-23 after the NMR ruling (NMR = the European N55, 5.5 t); before
# that the model had no 5.5 t band and NMR trucks sat inside the 7.5 t band.
BAND_ORDER = ["LCV_D-Max", "3.5t_N35", "5.5t_N50_N55", "7.5t_N50_N62_N75", "F_series_MD_heavy"]
BAND_LABEL = {
    "LCV_D-Max": "LCV / D-Max",
    "3.5t_N35": "3.5 t (N35 Grafter)",
    "5.5t_N50_N55": "5.5 t (N50 / N55)",
    "7.5t_N50_N62_N75": "7.5 t (N75 / N50 / N62)",
    "F_series_MD_heavy": "F-series / MD (heavy)",
}
# Visits a year per band, PRISM lane. cv_std covers all three truck rungs.
SVC_PRISM = {"LCV_D-Max": 1.0, "3.5t_N35": 0.5, "5.5t_N50_N55": 0.5, "7.5t_N50_N62_N75": 0.5,
             "F_series_MD_heavy": 0.6667}
# ITUK's IML v7 lane: filters 1.25, clutch and brake 0.5.
SVC_IML = {"LCV_D-Max": 1.0, "3.5t_N35": 0.5, "5.5t_N50_N55": 0.5, "7.5t_N50_N62_N75": 0.5,
           "F_series_MD_heavy": 0.6667}
IML_FILTER_CATS = {"oil_filter", "fuel_filter", "air_filter"}
IML_VISITS_FILTER = 1.25
IML_VISITS_WEAR = 0.5


def load_factors() -> tuple[dict[str, float], dict[str, float], dict[str, dict], dict[str, float]]:
    from modules.pms_capture_config import (  # noqa: PLC0415
        CONSUMABLE_FACTOR,
        COUNTRY_OVERRIDES,
        LCV_BUCKET_FACTOR_OVERRIDES,
        WEAR_FACTOR,
    )

    return CONSUMABLE_FACTOR, WEAR_FACTOR, COUNTRY_OVERRIDES, LCV_BUCKET_FACTOR_OVERRIDES


def build_band_expected() -> pd.DataFrame:
    """Expected service demand per market x band x PMS category, both lanes."""
    buckets = pd.read_csv(PRISM_DATA_DIR / "uio_by_model_bucket.csv").set_index("distributor_code")
    sh = pd.read_csv(PRISM_DATA_DIR / "uio_ld_n35_share.csv")
    n35_share = dict(zip(sh.distributor_code, sh.n35_share))
    # The 5.5 t share, and which side of the 3.5 t split it is carved from: `n75` for most markets,
    # `n35` where the recorded 3.5 t share is itself the NMR count (Malta, Cyprus), so no NMR truck
    # is counted on two rungs. See the evidence_note column of the file.
    s55 = pd.read_csv(PRISM_DATA_DIR / "uio_n55_share.csv")
    n55_share = dict(zip(s55.distributor_code, s55.n55_share))
    n55_from = dict(zip(s55.distributor_code, s55.taken_from))
    cons, wear, country, lcv_override = load_factors()
    factors = {**cons, **wear}

    cats = sorted(factors.keys())
    rows = []
    for db, b in buckets.iterrows():
        cv = float(b["cv_std_uio"])
        fs = float(b["f_series_uio"])
        lcv = float(b["lcv_uio"])
        s = float(n35_share.get(db, 0.0))
        s55 = float(n55_share.get(db, 0.0))
        if n55_from.get(db, "n75") == "n35":
            if s55 > s + 1e-9:
                raise SystemExit(f"{db}: 5.5 t share {s55} carved from a 3.5 t share of only {s}")
            s35, s75 = s - s55, 1 - s
        else:
            if s + s55 > 1 + 1e-9:
                raise SystemExit(f"{db}: 3.5 t {s} + 5.5 t {s55} exceed the N-series fleet")
            s35, s75 = s, 1 - s - s55
        uio = {
            "3.5t_N35": cv * s35,
            "5.5t_N50_N55": cv * s55,
            "7.5t_N50_N62_N75": cv * s75,
            "F_series_MD_heavy": fs,
            "LCV_D-Max": lcv,
        }
        # ITUK is the only market on the IML v7 lane.
        is_ituk = db == "ITUK"
        lane = "IML v7 (ITUK)" if is_ituk else "PRISM network"
        override = (country.get(db) or {}).get("factors") or {}

        for band, band_uio in uio.items():
            for cat in cats:
                if band_uio <= 0:
                    continue
                factor = float(factors[cat])
                if cat in override:
                    factor = float(override[cat])
                elif band == "LCV_D-Max" and cat in lcv_override:
                    factor = float(lcv_override[cat])
                visits = SVC_PRISM[band]
                if is_ituk:
                    visits = IML_VISITS_FILTER if cat in IML_FILTER_CATS else IML_VISITS_WEAR
                rows.append({
                    "distributor_code": db,
                    "band": band,
                    "band_label": BAND_LABEL[band],
                    "pms_category": cat,
                    "lane": lane,
                    "uio_units": round(band_uio, 1),
                    "visits_per_year": visits,
                    "category_factor": factor,
                    "expected_qty_per_year": round(band_uio * visits * factor, 1),
                })
    out = pd.DataFrame(rows)
    # Share of the market's expected demand that sits in each band.
    tot = out.groupby(["distributor_code", "pms_category"])["expected_qty_per_year"].transform("sum")
    out["_share_raw"] = out["expected_qty_per_year"] / tot
    out["share_of_market_category_pct"] = (100 * out["_share_raw"]).round(2)
    return out


def build_actuals_and_capture() -> pd.DataFrame:
    """Market x PMS category x year actuals and capture, on both clocks.

    Capture and actuals are market-level by construction: the billing has no vehicle, so they
    cannot be pushed into a band. This frame is joined to the band expectation on market and
    category, and the flag on the join says so.
    """
    pms = pd.read_csv(DERIVED_DIR / "pms_capture_by_db_year.csv")
    tot = pms[pms.line_type == "total"].copy()
    return tot[[
        "distributor_code", "pms_category", "year",
        "expected_qty", "actual_qty", "actual_rev_eur", "capture_rate",
        "avg_sp_eur", "revenue_gap_eur",
    ]].rename(columns={
        "expected_qty": "market_expected_qty",
        "actual_qty": "market_actual_qty",
        "actual_rev_eur": "market_actual_eur",
        "capture_rate": "market_capture_rate",
        "avg_sp_eur": "market_avg_sp_eur",
        "revenue_gap_eur": "market_gap_eur",
    })


def build_aim_evolution() -> pd.DataFrame:
    """AIM level 1 and level 2 billed euro per market per year, on both clocks."""
    sf = pd.read_parquet(DERIVED_DIR / "sales_fact.parquet")
    sf["_pn"] = sf.part_number.map(norm)
    sf["d"] = pd.to_datetime(sf.billing_date, errors="coerce")
    sf = sf.dropna(subset=["d"])
    dim = pd.read_csv(DERIVED_DIR / "distributor_dimension.csv")
    sf["distributor_code"] = sf.sold_to_sap.map(dict(zip(dim.sold_to_sap, dim.distributor_code)))
    sf = sf[sf.distributor_code.notna()]
    sf["year"] = sf["d"].dt.year
    sf["month"] = sf["d"].dt.month
    # ISZE financial year: April to March, labelled by the year that closes it.
    sf["fy_label"] = sf["year"] + (sf["month"] >= 4).astype(int)

    aim = pd.read_csv(DERIVED_DIR / "aim_master_v2.csv", dtype=str,
                      usecols=["part_number", "aim_l1_fixed", "aim_l2_fixed"], low_memory=False)
    aim["_pn"] = aim.part_number.map(norm)
    aim = aim.drop_duplicates("_pn")
    sf = sf.merge(aim[["_pn", "aim_l1_fixed", "aim_l2_fixed"]], on="_pn", how="left")
    sf["aim_l1"] = sf.aim_l1_fixed.fillna("Unclassified")
    sf["aim_l2"] = sf.aim_l2_fixed.fillna("Unclassified")

    def summarise(clock_col, clock_name):
        g = (sf.groupby(["distributor_code", clock_col, "aim_l1", "aim_l2"], dropna=False)
             .agg(billed_eur=("net_sales_value", "sum"),
                  billed_qty=("billed_qty", "sum"),
                  distinct_pns=("part_number", "nunique"))
             .reset_index()
             .rename(columns={clock_col: "period"}))
        g["clock"] = clock_name
        return g

    cy = summarise("year", "CY")
    fy = summarise("fy_label", "FY")
    fy = fy.rename(columns={"period": "period"})
    out = pd.concat([cy, fy], ignore_index=True)
    out["period"] = out["period"].astype(int)
    out["billed_eur"] = out["billed_eur"].round(2)
    return out


def main() -> int:
    band = build_band_expected()
    actuals = build_actuals_and_capture()
    aim = build_aim_evolution()

    # Cartesian: every band row gets every year, carrying that market/category/year actual beside
    # it. actual_is_market_level says plainly that the actual is not band-specific.
    joined = band.merge(actuals, on=["distributor_code", "pms_category"], how="inner")
    joined["actual_is_market_level"] = True
    joined["expected_share_of_market_pct"] = joined["share_of_market_category_pct"]
    # From the unrounded share, so a market's band gaps add back to its market gap to the cent
    # (the rounded 2-decimal share left up to EUR 141 per market adrift; fixed 2026-09-23).
    joined["gap_eur_band_share"] = (joined["market_gap_eur"] * joined["_share_raw"]).round(2)
    joined = joined.drop(columns="_share_raw")

    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    joined.to_csv(BANDS_CSV, index=False)
    aim.to_csv(AIM_CSV, index=False)

    meta = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "generated_by": "scripts/build_pms_tonnage_model.py",
        "band_model": str(BANDS_CSV),
        "aim_model": str(AIM_CSV),
        "bands": BAND_ORDER,
        "rows": {"band_model": int(len(joined)), "aim_model": int(len(aim))},
        "lanes": {
            "IML v7 (ITUK)": "filters 1.25 visits/yr, clutch and brake 0.5, 22,389 DVLA fleet, "
                             "brake factor 0.4",
            "PRISM network": "cv 0.5, F-series 0.667, LCV 1.0 visits/yr, D-Max brake 0.4",
        },
        "limits": [
            "Actual billed units do not split by tonnage. The billing carries no vehicle, so the "
            "band columns carry the band's expected demand and the market's actual beside it. "
            "actual_is_market_level=True marks every such row; do not sum actuals down a band.",
            "The fleet vintage is 2025E for every year, so expected demand is flat over time by "
            "construction. Only the billing and the capture move.",
            "F-series exists as a fleet in three markets only (ITUK, Portugal, Ireland) and is "
            "1,238 vehicles in total. It carries an expected demand but almost no attributable "
            "billing, because the billing has no vehicle.",
            "UTI has no 3.5 t band at all: 2,360 CV warranty VINs show no NLR/NMR/NKR.",
            "The 5.5 t rung (NMR, the European N55) is split out of the N-series fleet with the "
            "per-market share in prism/data/uio_n55_share.csv: measured parc for Germany, "
            "registrations for Portugal and the ITUK VIN list, JP shipments elsewhere. Where the "
            "recorded 3.5 t share is itself the NMR count (Malta, Cyprus) the 5.5 t fleet is carved "
            "out of it; everywhere else out of the 7.5 t side. Total N-series fleet is unchanged.",
            "The ITUK lane is the IML v7 schedule and is not comparable with the PRISM lane. "
            "Never average or sum the two.",
            "AIM level 1 resolves on 99.3% of billed euro; level 2 on a little less. The "
            "remainder is reported as Unclassified rather than dropped.",
        ],
    }
    import json  # noqa: PLC0415

    META_JSON.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"  band model : {len(joined):,} rows -> {BANDS_CSV}")
    print(f"  aim model  : {len(aim):,} rows -> {AIM_CSV}")
    print(f"  markets    : {band.distributor_code.nunique()}, bands: {len(BAND_ORDER)}, "
          f"categories: {band.pms_category.nunique()}, years: "
          f"{sorted(int(y) for y in joined.year.unique())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
