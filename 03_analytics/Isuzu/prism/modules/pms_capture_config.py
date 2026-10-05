"""Shared PMS capture categories and demand factors (P1 build + live recompute)."""

from __future__ import annotations

from pathlib import Path

import yaml

_DEFAULT_CONSUMABLE: dict[str, float] = {
    "oil_filter": 1.0,
    "fuel_filter": 1.0,
    "air_filter": 0.5,  # PROVISIONAL (air element ~every 2nd service vs oil every service) — confirm with IML; added 2026-07-02
    # AdBlue filter. Was 1.0 — one per service visit, the same rate as an oil filter — and that was
    # wrong by a factor of five. René Paul's GIDSS schedule gives the AdBlue filter at 200,000 km on
    # N-series (N_MY24, NPR75 / 4HK1: row "AdBlue filter", the line above "PM sensor"; the F-series
    # sheet names the equivalent row "AdBlue filter (4HK1-TCH engine model)", so it is the filter
    # element and not the tank). One N75 service visit covers 40,000 km, so 40,000/200,000 = 0.20.
    # The F-series runs a different interval (80,000 km) and is split out in
    # expected_by_category_bucketed() below, where the vehicle class is known.
    "urea_filter": 0.2,
    "blower_filter": 1.0,  # Jerome 2026-07-26 — align with oil/fuel/urea; was 0.25 cabin placeholder
}

# AdBlue filter interval on the F-series 4HK1-TCH, which the single scalar above cannot express:
# 80,000 km per René Paul's GIDSS F_MY24 p1 (Italy / Israel / Portugal / UK / Ireland block), against
# the provisional 30,000 km F-series visit interval in BUCKET_SERVICES_PER_YEAR = 0.375. The two
# classes differ by 1.875x, so the split has to happen where the classes are known.
UREA_FILTER_F_SERIES = 30_000 / 80_000

_DEFAULT_WEAR: dict[str, float] = {
    "brake_pad": 0.5,
    "brake_shoe": 0.5,
    "clutch_disc": 0.2,
    "clutch_pressure_plate": 0.2,
    "clutch_kit": 0.15,
    "release_bearing": 0.15,
    "pilot_bearing": 0.1,
    "clutch_booster": 0.1,
    "brake_rotor": 0.25,  # PROVISIONAL (rotors ~every 2nd pad change) — confirm with IML; added 2026-06-15
}

_ASSUMPTIONS_PATH = Path(__file__).resolve().parents[1] / "data" / "pms_capture_assumptions.yaml"


def _load_yaml() -> dict:
    if not _ASSUMPTIONS_PATH.is_file():
        return {}
    return yaml.safe_load(_ASSUMPTIONS_PATH.read_text(encoding="utf-8")) or {}


def _load_assumptions() -> tuple[dict[str, float], dict[str, float]]:
    raw = _load_yaml()
    cons = {**_DEFAULT_CONSUMABLE, **(raw.get("consumable_factor") or {})}
    wear = {**_DEFAULT_WEAR, **(raw.get("wear_factor") or {})}
    return cons, wear


def n75_addressable_pct() -> float:
    """PRISM capture denominator — separate from IML Model B (100% in iml_v7_ituk_cy2025.yaml)."""
    n75 = _load_yaml().get("n75_parc_assumptions") or {}
    return float(n75.get("addressable_pct", 1.00))


CONSUMABLE_FACTOR, WEAR_FACTOR = _load_assumptions()
CONSUMABLE_CATS = list(CONSUMABLE_FACTOR.keys())
P1_CATEGORIES = CONSUMABLE_CATS + list(WEAR_FACTOR.keys())


def _load_country_overrides() -> dict:
    """Per-distributor service-interval overrides (docs/pms_service_intervals.md §5). Empty = global."""
    return _load_yaml().get("country_overrides") or {}


COUNTRY_OVERRIDES = _load_country_overrides()

# ─── Real per-model-type-bucket UIO (2026-07-15 fix) ──────────────────────────
# Replaces the pms_engine.LCV_DISTRIBUTORS/CV_TRUCK_DISTRIBUTORS 2-market
# allowlist, which silently scored every other distributor (14 of 18) against
# the wrong vehicle class. See scripts/build_uio_by_model_bucket.py.

BUCKET_SERVICES_PER_YEAR: dict[str, float] = {
    "cv_std": 0.5,      # N75 / NPR75 basis: 40,000 km factory interval over the network's
                        # mileage assumption. N35 is NOT priced at this rate — see the share
                        # adjustment below.
    "f_series": 0.6667, # PROVISIONAL — 30,000km interval / 20,000km assumed avg
                        # annual mileage (Isuzu Truck UK service book, no real
                        # F-Series mileage confirmed yet).
    "lcv": 1.0,         # CONFIRMED — 20,000km interval / 20,000km flat mileage
                        # assumption (session 2026-07-15, D-Max UK owner's handbook).
}

# ─── N35 / N75 interval split (2026-09-18) ───────────────────────────────────
# The 3.5 t N35 and the 7.5 t N75 run different factory service intervals, and until now both were
# priced at the cv_std rate above. Sources agree, and they agree per model rather than per market:
#
#   N35  NLR87 / RZ4E  20,000 km   Duncan deck slide 14 (2026-09-15) + René GIDSS N_MY24 p6-8
#   N75  NPR75 / 4HK1  40,000 km   same two sources
#
# So an N35 needs twice the service visits of an N75 over the same distance. Expressed as a ratio
# rather than as kilometres, the mileage assumption cancels out and no unmeasured input is needed:
#
#   cv_std(market) = n35_share × 0.5 × (40,000 ÷ 20,000) + (1 − n35_share) × 0.5
#                  = 0.5 × (1 + n35_share)
#
# A market with no 3.5 t fleet (UTI, Greece, and every LCV-only market) has a share of zero and is
# therefore unchanged. Only markets with a measured N35 fleet move, and only by their own share.
# The share is measured per market in data/uio_ld_n35_share.csv, with its evidence note.
#
# ITUK is INCLUDED, applied 2026-09-18. Its N35 share is measured at 50.51% and its two intervals are
# the ones that started this fix (Duncan deck slide 14 + René GIDSS). The IML v7 lane
# (iml_v7_ituk_cy2025.yaml, the external published deck at 35.1% oil-filter cover) is NOT touched:
# it is is a separately agreed external basis, and the two lanes were already different by design
# (IML 35.1% vs PRISM 116.4%). UTI is excluded because its cv_std is an explicit 1.25 override and
# it has no 3.5 t fleet.
N35_RATIO_EXCLUDED: set[str] = {"UTI"}
def _n35_share_by_distributor() -> dict[str, float]:
    p = Path(__file__).resolve().parents[1] / "data" / "uio_ld_n35_share.csv"
    if not p.is_file():
        return {}
    import pandas as pd  # noqa: PLC0415

    d = pd.read_csv(p)
    return {str(r["distributor_code"]): float(r["n35_share"]) for _, r in d.iterrows()}


N35_SHARE = _n35_share_by_distributor()
N35_INTERVAL_KM = 20_000
N75_INTERVAL_KM = 40_000
N35_TO_N75_VISIT_RATIO = N75_INTERVAL_KM / N35_INTERVAL_KM  # 2.0 — N35 needs double the visits

BUCKET_SERVICES_PER_YEAR_OVERRIDES: dict[str, dict[str, float]] = {
    "UTI": {"cv_std": 1.25},  # confirmed real 50,000km/yr annual mileage, IML CV
                              # study via Jerome 2026-07-10 (50,000/40,000km interval).
}
# Apply the tonnage ratio to every market with a measured N35 fleet, except those excluded.
for _db, _share in N35_SHARE.items():
    if _share <= 0 or _db in N35_RATIO_EXCLUDED:
        continue
    if _db in BUCKET_SERVICES_PER_YEAR_OVERRIDES:
        continue
    _base = BUCKET_SERVICES_PER_YEAR["cv_std"]
    BUCKET_SERVICES_PER_YEAR_OVERRIDES[_db] = {
        "cv_std": round(_base * (1.0 + _share * (N35_TO_N75_VISIT_RATIO - 1.0)), 4)
    }

# Session-confirmed D-Max-specific factor, overriding the generic global wear_factor
# for the LCV bucket component only (front brake-kit basis, 50,000km vs the global
# 20,000km-oil-visit-based 0.5 used for truck brakes).
LCV_BUCKET_FACTOR_OVERRIDES: dict[str, float] = {
    "brake_pad": 0.4,
}

_UIO_BUCKET_PATH = Path(__file__).resolve().parents[1] / "data" / "uio_by_model_bucket.csv"


def load_uio_by_bucket() -> dict[str, dict[str, float]]:
    """distributor_code -> {"cv_std", "f_series", "lcv"} real UIO split.

    Empty dict if the file hasn't been generated yet (run
    scripts/build_uio_by_model_bucket.py) — callers must treat that as "no real
    bucket data for this distributor" and fall back to the legacy single-scope
    calculation, not an error.
    """
    if not _UIO_BUCKET_PATH.is_file():
        return {}
    import pandas as pd

    df = pd.read_csv(_UIO_BUCKET_PATH)
    return {
        row["distributor_code"]: {
            "cv_std": float(row["cv_std_uio"]),
            "f_series": float(row["f_series_uio"]),
            "lcv": float(row["lcv_uio"]),
        }
        for _, row in df.iterrows()
    }


UIO_BY_BUCKET = load_uio_by_bucket()
