"""Shared PMS capture categories and demand factors (P1 build + live recompute)."""

from __future__ import annotations

from pathlib import Path

import yaml

_DEFAULT_CONSUMABLE: dict[str, float] = {
    "oil_filter": 1.0,
    "fuel_filter": 1.0,
    "air_filter": 0.5,  # PROVISIONAL (air element ~every 2nd service vs oil every service) — confirm with IML; added 2026-07-02
    "urea_filter": 1.0,
    "blower_filter": 1.0,  # Jerome 2026-07-26 — align with oil/fuel/urea; was 0.25 cabin placeholder
}

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
    "cv_std": 0.5,      # PROVISIONAL — LD+MD collapsed into one bucket, pending a
                        # real IML LD/MD interval split (Jerome 2026-07-15: "collapse
                        # LD+MD but flag it"). Matches the pre-existing N75 default.
    "f_series": 0.6667, # PROVISIONAL — 30,000km interval / 20,000km assumed avg
                        # annual mileage (Isuzu Truck UK service book, no real
                        # F-Series mileage confirmed yet).
    "lcv": 1.0,         # CONFIRMED — 20,000km interval / 20,000km flat mileage
                        # assumption (session 2026-07-15, D-Max UK owner's handbook).
}

BUCKET_SERVICES_PER_YEAR_OVERRIDES: dict[str, dict[str, float]] = {
    "UTI": {"cv_std": 1.25},  # confirmed real 50,000km/yr annual mileage, IML CV
                              # study via Jerome 2026-07-10 (50,000/40,000km interval).
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
