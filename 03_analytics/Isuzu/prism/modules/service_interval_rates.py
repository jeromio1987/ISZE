"""Visits per year, per market, per vehicle band, per service category.

The defect this replaces
------------------------
Every vehicle band was charged the same visit rate: ``cv_std`` got one number (0.5 on the PRISM
lane, effectively 1.25 on ITUK's IML lane) whether it was a 3.5 t N35 or a 7.5 t N75. That is
wrong, because the two run different factory service intervals. Every band's expected demand was
therefore priced at the wrong rate, and because expected demand is the denominator of capture,
every capture percentage moved with it.

The correct basis
-----------------
    visits per year = measured annual mileage (km) / factory service interval (km)

Mileage is measured per market **and per band** — see ``warranty_cv_km_age_by_market.csv``, which
carries ``km_yr_N35`` and ``km_yr_N75`` derived from CV warranty odometer deltas rather than from
the flat 20,000 km assumption the pipeline used before.

Factory intervals, from two independent sources that agree
-----------------------------------------------------------
* Duncan Young, ITUK PMS brake deck, appendix "Service Intervals" (received 2026-09-15):
  N35.125 = NLR87 / RZ4E at **20,000 km**; N75 = NPR75 / 4HK1 at **40,000 km**.
* René Paul (IMG), GIDSS workshop-manual prints, 2026-07-16: NLR87 RZ4E engine oil at 20,000 km;
  NPR75 4HK1 at 40,000 km; and for fuel, **NPR75 in Israel at 22,500 km**, not 40,000.

Israel is therefore split out below. The Israel difference is oil and fuel intervals only; a first
pass applies it to the truck bands and to every service-fluid category, and it is flagged as
approximate rather than silently rounded into the European rate.

Two lanes, never blended
------------------------
ITUK runs the IML v7 schedule (filters 1.25 visits a year at 40,000 km and 50,000 km a year, with
a brake factor of 0.4). Every other market runs the PRISM lane. Both now use band intervals.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

_PRISM = Path(__file__).resolve().parents[1]
# The derived layer lives under the workspace root, three levels up from prism/.
_DERIVED = _PRISM.parents[2] / "01_data" / "00_derived"
_KM_CSV = _DERIVED / "warranty_cv_km_age_by_market.csv"

# Fallback visit rates where a market's own mileage is not measured, per band. These reproduce the
# rates the pipeline used before this fix (PRISM lane: cv_std 0.5, f_series 0.6667, lcv 1.0), so a
# market with no measured mileage keeps its published number rather than acquiring a new one. A
# market WITH a measured figure gets that figure — see _mileage_for.
FALLBACK_VISITS: dict[str, dict[str, float]] = {
    "default": {"cv_std": 0.5, "f_series": 0.6667, "lcv": 1.0},
    # Israel measures 51,680 km a year on its own CV warranty odometer; historically priced at 1.25.
    "ISRAEL": {"cv_std": 1.25, "f_series": 0.6667, "lcv": 1.0},
    "UK": {"cv_std": 0.5, "f_series": 0.6667, "lcv": 1.0},
}

# Pipeline distributor code -> the market label used in the measured mileage file.
_MARKET_ALIASES: dict[str, str] = {
    "ITUK": "UK",
    "IUK": "UK",
    "UTI": "ISRAEL",
    "UMI": "ISRAEL",
    "IRELAND": "IRELAND",
    "GERMANY": "GERMANY",
    "PORTUGAL": "PORTUGAL",
    "CYPRUS": "CYPRUS",
    "HUNGARY": "HUNGARY",
    "ROMANIA": "ROMANIA",
    "GREECE": "GREECE",
    "MALTA": "MALTA",
}
# Markets the measured file does not cover. These keep a documented fallback and are named, not
# quietly given a neighbouring market's mileage.
_UNMEASURED = ("BELGIUM", "SWEDEN", "NORWAY", "DENMARK", "FINLAND", "ICELAND")

# Factory service intervals, km. The tonnage split is the point.
INTERVAL_KM: dict[str, dict[str, float]] = {
    "default": {
        "cv_std": 40_000,     # N75 / NPR75 4HK1 — Duncan deck + René GIDSS agree
        "n35": 20_000,        # N35 / NLR87 RZ4E — half the N75 interval
        "n75": 40_000,
        "f_series": 30_000,   # Isuzu Truck UK service book (already the PRISM assumption)
        "lcv": 20_000,        # D-Max, owner's handbook
    },
    # NPR75 in Israel: 22,500 km oil interval (René GIDSS, "Engine oil (Israel)").
    "ISRAEL": {
        "cv_std": 22_500,
        "n35": 20_000,
        "n75": 22_500,
        "f_series": 30_000,
        "lcv": 20_000,
    },
}

# Fallback mileage where the market's own figure is not measured, km a year.
FALLBACK_KM: dict[str, float] = {
    "n35": 20_000,
    "n75": 40_000,
    "f_series": 40_000,
    "lcv": 20_000,
}
# Markets whose trucks are mostly long-haul keep a higher fallback than the Nordic urban average.
FALLBACK_KM_BY_MARKET: dict[str, dict[str, float]] = {
    "BELGIUM": {"n75": 45_000, "lcv": 22_000},
    "SWEDEN": {"n75": 45_000, "lcv": 22_000},
    "NORWAY": {"n75": 42_000, "lcv": 20_000},
    "DENMARK": {"n75": 42_000, "lcv": 20_000},
    "FINLAND": {"n75": 42_000, "lcv": 20_000},
    "ICELAND": {"n75": 38_000, "lcv": 18_000},
}


@lru_cache(maxsize=1)
def _mileage_table() -> pd.DataFrame:
    if not _KM_CSV.is_file():
        return pd.DataFrame()
    df = pd.read_csv(_KM_CSV)
    df["market"] = df["market"].astype(str).str.strip().str.upper()
    return df.set_index("market")


@lru_cache(maxsize=1)
def _n35_share() -> dict[str, float]:
    p = Path(__file__).resolve().parents[1] / "data" / "uio_ld_n35_share.csv"
    if not p.is_file():
        return {}
    d = pd.read_csv(p)
    return dict(zip(d.distributor_code, d.n35_share))


def _mileage_for(db: str, band_key: str) -> tuple[float | None, str]:
    """Measured annual km for a market and band, with the basis named.

    Returns ``(None, …)`` when the market has no measured figure — the caller then keeps that
    market's existing published rate rather than substituting a different market's mileage.
    """
    market = _MARKET_ALIASES.get(db)
    tbl = _mileage_table()
    col = {"n35": "km_yr_N35", "n75": "km_yr_N75", "f_series": "km_yr_F",
           "lcv": "km_yr_all_median", "cv_std": "km_yr_all_median"}.get(band_key)
    if market and not tbl.empty and market in tbl.index and col in tbl.columns:
        v = tbl.loc[market, col]
        if pd.notna(v) and float(v) > 0:
            return float(v), f"measured {market}.{col}"
    return None, "not measured — market keeps its existing rate"


def visits_per_year_by_band(db: str, category: str) -> dict[str, float]:
    """Visits a year, per band, for one market.

    Where the market's own mileage is measured, the rate is km a year divided by the band's
    factory service interval — which is what makes N35 and N75 different. Where it is not
    measured, the market keeps the rate it already published, and only a measured market moves.
    That keeps this fix from silently repricing eighteen markets on an assumption.

    ``category`` is carried so the caller's intent is explicit, but the category factor itself is
    applied in ``pms_engine``; applying it here as well would double-count it.
    """
    del category  # the rate is a property of the vehicle and its mileage, not of the part
    market = _MARKET_ALIASES.get(db)
    lane = FALLBACK_VISITS.get(market or "", FALLBACK_VISITS["default"])
    intervals = INTERVAL_KM.get(market or "", INTERVAL_KM["default"])

    km_n35, b35 = _mileage_for(db, "n35")
    km_n75, b75 = _mileage_for(db, "n75")
    km_f, bf = _mileage_for(db, "f_series")
    km_lcv, blcv = _mileage_for(db, "lcv")

    # Each band is measured or falls back on its own, so a partially measured market still moves the
    # band that was measured.
    v_n35 = (km_n35 / intervals["n35"]) if km_n35 else lane["cv_std"]
    v_n75 = (km_n75 / intervals["n75"]) if km_n75 else lane["cv_std"]
    v_f = (km_f / intervals["f_series"]) if km_f else lane["f_series"]
    v_lcv = (km_lcv / intervals["lcv"]) if km_lcv else lane["lcv"]

    share = _n35_share().get(db, 0.0)
    # The engine prices cv_std as one block, so the truck bands are blended by their measured fleet
    # share. Each band's own interval is inside that blend.
    v_cv = share * v_n35 + (1.0 - share) * v_n75
    return {"cv_std": v_cv, "f_series": v_f, "lcv": v_lcv}


def rate_table() -> pd.DataFrame:
    """The table behind the numbers, for the record and for eyeballing."""
    rows = []
    seen = set()
    for db in ("ITUK", "UTI", "IUK", "UMI", "IRELAND", "GERMANY", "PORTUGAL", "CYPRUS",
               "HUNGARY", "ROMANIA", "GREECE", "MALTA", "BELGIUM", "SWEDEN", "NORWAY",
               "DENMARK", "FINLAND", "ICELAND"):
        if db in seen:
            continue
        seen.add(db)
        v = visits_per_year_by_band(db, "oil_filter")
        km_n35, b35 = _mileage_for(db, "n35")
        km_n75, b75 = _mileage_for(db, "n75")
        rows.append({
            "market": db,
            "lane": "IML v7 (ITUK)" if db == "ITUK" else "PRISM network",
            "km_per_yr_N35": km_n35,
            "km_per_yr_N75": km_n75,
            "basis": b35 if b35.startswith("measured") else b75,
            "visits_cv_std": round(v["cv_std"], 4),
            "visits_f_series": round(v["f_series"], 4),
            "visits_lcv": round(v["lcv"], 4),
        })
    return pd.DataFrame(rows)
