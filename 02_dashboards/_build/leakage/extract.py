"""Distributor Leakage Cockpit - data extractor.

One pass over the derived layer, one payload. The HTML builder never touches a
CSV; it only reads payload.json. That keeps the audience switch (internal vs
customer) a pure downstream decision, and makes field-stripping auditable.

Run:  python 02_dashboards\\_build\\leakage\\extract.py
      python 02_dashboards\\_build\\leakage\\extract.py --check   (print sanity numbers)

House rules enforced here, not in the renderer:
  * isze-gaps-need-context.mdc - every gap carries euro + service family + fleet.
  * Payroll of truth: _verification_report.json must be green or we refuse to build.
  * No invented series. Where a source stops, the payload says so and the renderer
    prints a data-gap banner rather than interpolating.

Rate conventions are NOT uniform in the derived layer and are declared explicitly
below. `capture_rate` is a 0-1 fraction; `gps_pct` is 0-100; `vs_network_risk_pp` is
already in percentage points. Guessing these silently corrupts every gap on the page,
so each column goes through a named converter.
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import sys
from datetime import date, datetime

import pandas as pd

def _sum(xs):
    return sum(x for x in xs if x is not None)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# --------------------------------------------------------------------- paths
# ISZE_ROOT env wins; fall back to the repo this file sits in. No hardcoded user path.
ROOT = os.environ.get("ISZE_ROOT") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)
D = os.path.join(ROOT, "01_data", "00_derived")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "payload.json")

YEARS = [2023, 2024, 2025, 2026]
CURRENT_YEAR = 2026
YTD_NOTE = "CY2026 runs to 30 June"
PEER_MIN_MEMBERS = 3          # below this a peer median is suppressed, not averaged
PLACEHOLDER_SPU_EUR = 250.0   # flat per-vehicle ceiling placeholder in wallet_waterfall

# Measured annual distance, km/yr. Model default is a flat 20,000 (see honesty module).
KM = {
    "IUK": (14494, "N35 Grafter odometer intervals", "9,006 mi median, 18,277 intervals, 5,421 vehicles"),
    "UTI": (51680, "CV warranty odometer", "confirmed against the market's own 50,000"),
    "ITUK": (16688, "UK warranty VIN sample", "contradicts the 50,000 km/yr the market supplied"),
    "N35": (12165, "CV warranty odometer", "PROVISIONAL, all-market"),
    "N75": (35217, "CV warranty odometer", "PROVISIONAL, all-market"),
    "F": (45630, "CV warranty odometer", "PROVISIONAL, all-market"),
}
KM_MODEL = 20000

# Dealer-grain sales-to-dealer files. Only ONE of these carries real dealer outlet names -
# see _dealer_audit().
DEALER_LONG = sorted(glob.glob(os.path.join(D, "dealer_sellout_long_*.csv")))

GAP_TYPE_LABEL = {
    "substitution": "Bought another brand instead",
    "under_service": "Fewer service visits than the fleet needs",
    "catalog_gap": "No part of ours fits this application",
}

# Plain-business wording for the action ledger's signal types. The labels a distributor reads
# describe what is happening in the market; they never name an internal register.
SIGNAL_LABEL = {
    "LEAKAGE": "Your network sold more than it bought from us",
    "REPLENISHMENT": "Selling through faster than we ship",
    "DEFECTION": "Stopped ordering this part",
    "CATALOGUE_GAP": "No part of ours fits this application",
    "EARLY_WARNING": "Worth watching",
    "ACCOUNT_HEALTH": "Account review",
    "PRICE_REVISION": "Pricing review",
    "BOOK_B": "Pricing review",
}
# How many part lines per market reach the page. The register is far larger than a reader can
# use, and embedding all of it multiplies the file size for no benefit.
ACTION_LINE_CAP = 40
# Which signals can appear in a distributor pack. Pricing review is ours to conduct, not
# theirs to read, so it stays internal.
SIGNAL_CUSTOMER_OK = {"LEAKAGE", "REPLENISHMENT", "DEFECTION", "CATALOGUE_GAP"}
ACTION_LABEL = {
    "REVIEW_LEAKAGE": "Review this with the market",
    "REVIEW_HIGH_LIST_EXPOSURE": "Review the price position",
    "REVIEW_OVERSTOCK": "Rebalance the stock position",
    "REVIEW_REPLENISHMENT": "Adjust the replenishment plan",
    "REVIEW_CATALOGUE_GAP": "Raise a range gap",
    "MONITOR": "Monitor",
}

# ---------------------------------------------------------------- intervals
# THE RULE, in three levels. Each category in each market takes the best level available:
#
#   1. ITUK'S OWN DATA          - ITUK supplied figures the generic schedule does not carry.
#                                 Source: 01_data/03_PMS/ISZE_ITUK_Brake_Factor_IML_Ask_2026-07-23.md
#   2. THE VEHICLE-FAMILY SCHEDULE - the supplier maintenance schedule for the family the market
#                                 actually sells. CV markets take the N-series schedule; LCV/pickup
#                                 markets take the D-Max schedule. Sources:
#                                 01_data/03_PMS/PMS_Intervals_Authoritative_Sources.md (N-series,
#                                 Rene Paul GIDSS, 2026-07-16)
#                                 03_analytics/Isuzu/prism/data/lcv_pms_genuine.yaml (D-Max)
#   3. PLACEHOLDER              - no defensible source. Marked as such on the face.
#
# A truck interval must never be applied to a pickup market or the reverse, which is why the
# family matters. A MIXED market is the hard case: it sells both, this layer has no vehicles-in-
# service split by weight class, and the two families have different intervals. Such a market
# therefore gets NO sourced interval rather than the wrong family's number.

# N-series (CV truck). From the GIDSS schedules.
SCHEDULE_CV = {
    "Oil Filter": 40000,             # NPR75 4HK1: filter with the oil, every 40,000 km
    "Fuel Filter": 40000,            # NPR75 4HK1: element every 40,000 km or 12 months
    "Urea (AdBlue) Filter": 200000,  # NPR75 4HK1 and NPR85 MY14: every 200,000 km
}

# D-Max / LCV (pickup). From lcv_pms_genuine.yaml, itself sourced from the D-Max handbook plus
# Jerome-confirmed working assumptions where the manufacturer interval does not exist.
SCHEDULE_LCV = {
    "Oil Filter": 20000,             # the model's service interval is the oil filter interval
    "Fuel Filter": 20000,
    "Brake Pad": 50000,              # front 50,000 / rear 75,000; front is the binding figure
    "Brake Rotor": 100000,           # 0.2 wear factor = paired with every second front pad change
}

# ITUK'S OWN figures. These override the family schedule for ITUK only, and must not travel.
ITUK_INTERVAL = {
    "Brake Pad": 100000,             # ITUK-supplied flat interval, front+rear as one paired event
    "Brake Shoe": 100000,            # ITUK-supplied flat interval, paired with the pad change
    "Urea (AdBlue) Filter": 200000,  # same as the schedule; ITUK confirmed it
}

BASIS_LABEL = {
    "ituk": "Your own interval data",
    "cv_schedule": "N-series maintenance schedule",
    "lcv_schedule": "D-Max maintenance schedule",
    "both_schedules": "Both maintenance schedules agree",
    "placeholder": "Model placeholder",
}

INTERVAL_NOTE = {
    "Oil Filter": "CV: NPR75 4HK1 replaces the filter with the oil at 40,000 km. "
                  "D-Max: the 20,000 km service interval is the filter interval.",
    "Fuel Filter": "CV: NPR75 4HK1 replaces the element at 40,000 km or 12 months. "
                   "D-Max: 20,000 km service interval.",
    "Urea (AdBlue) Filter": "CV: NPR75 4HK1 and NPR85 MY14 replace it every 200,000 km. "
                            "No D-Max interval is recorded in our sources.",
    "Brake Pad": "Your own figure: a flat 100,000 km interval with front and rear replaced "
                 "together. D-Max pickup: front 50,000 km, rear 75,000 km.",
    "Brake Shoe": "Your own figure: a flat 100,000 km interval paired with the pad change. "
                  "No D-Max figure in our sources.",
    "Brake Rotor": "D-Max pickup: rotors are paired with every second front pad change. "
                   "No CV interval in the maintenance schedule.",
    "Air Filter": "No replacement interval in our sources for the CV model: the schedule replaces "
                  "it on the vehicle's own indicator, which is not a fixed distance. The model's "
                  "figure is a placeholder.",
    "Clutch Disc": "No clutch replacement interval in any schedule. The N-series schedule gives a "
                   "clutch FLUID interval at 40,000 km, which is a different part.",
    "Clutch Pressure Plate": "No clutch replacement interval in any schedule.",
    "Clutch Kit": "No clutch replacement interval in any schedule.",
    "Release Bearing": "No clutch replacement interval in any schedule.",
    "Clutch Booster": "Not in any maintenance schedule.",
    "Pilot Bearing": "Not in any maintenance schedule, and no CV market has ever bought one.",
    "Blower Unit Filter": "The schedule says clean as needed, not replace. No replacement interval "
                          "exists, and no CV market has ever bought one.",
}

ITUK_KM = 50000
ITUK_BRAKE_UNITS_OPEN = True

# Below this share of the fleet, a capture rate is meaningless: the numerator counts the whole
# market while the denominator counts part of it. 95% lets a market with a tiny minority family
# still be scored, and excludes the cases that invert the number.
MIN_COVERAGE_PCT = 95.0

# ------------------------------------------------------------------ basis

# Categories with zero units sold across every CV market in the network, measured on CY2025
# billing across all 22 markets. Scoring these against a CV market measures the model rather
# than the market, and together they inflated ITUK's scored denominator by 24,600 units.
CV_ZERO_SALES = {"Blower Unit Filter", "Pilot Bearing"}

# MEASURED annual distance per market, from CV warranty odometer data.
#   Source: 01_data/90_INBOX/_cv_warranty_mileage_validation.md (2026-09-16, section 3)
#   Derived table: 01_data/00_derived/warranty_cv_km_age_by_market.csv
#
# The previous model applied one flat 20,000 km a year to every market. Measured distance
# tracks truck weight class, a 3.7x spread, and the flat figure is wrong for most markets:
# the UK measures 16,688, Israel 51,680. Every expected-demand figure depends on this, so the
# per-market measured figure is used where a market has one and the flat default only where it
# does not, with the source printed on the face.
#
# The measurement is deliberately the ALL-CLASS median rather than a class-weighted sum. A
# class-weighted model needs UIO split by weight class, which this layer does not carry; that is
# a PRISM engine change, not a reporting change. The all-class figure is a real measurement of
# the same fleet, so it is used, and the limitation is stated.
MEASURED_KM = {
    "ISRAEL": (51680, "measured, 2,001 VINs"),
    "UTI": (51680, "measured, Israel book"),
    "UK": (16688, "measured, 5,873 VINs"),
    "ITUK": (16688, "measured, UK book"),
    "PORTUGAL": (27072, "measured, 240 VINs"),
    "IRELAND": (24044, "measured, 37 VINs"),
    "SPAIN": (19754, "measured, 1,246 VINs"),
    "HUNGARY": (31264, "measured, 49 VINs"),
    "ROMANIA": (30820, "measured, 39 VINs"),
    "ITALY": (11961, "measured, 5,952 VINs"),
    "FRANCE": (9963, "measured, 1,347 VINs"),
    "GERMANY": (11980, "measured, 27 VINs, thin"),
    "SWITZERLAND": (9564, "measured, 611 VINs"),
    "POLAND": (16168, "measured, 95 VINs"),
    "CROATIA": (15231, "measured, 27 VINs, thin"),
    "CYPRUS": (35679, "measured, 8 VINs, thin"),
    "MALTA": (17705, "measured, 5 VINs, thin"),
    "GREECE": (1590, "measured, 1 VIN, not usable"),
}
KM_MODEL_FALLBACK = (20000, "model default, no measurement for this market")

# ------------------------------------------------------------------ basis
# Like-for-like reporting window. Every current-year figure is compared with the SAME months
# of prior years, and shown as an average month. A part year must never be set against a full
# year: the 2026 expected-service-demand denominator in the derived layer is a FULL year while
# 2026 actuals cover six months, so the filed 2026 capture rate reads roughly half its
# like-for-like value. Both are carried and the basis is printed on the face.
YTD_MONTHS = 6           # January to June
YTD_LABEL = "to 30 June"
AVG_LABEL = "average month"
PERIODS_PER_YEAR = 12

LAYER_LABEL = {"all": "Total", "bvp": "Another brand", "genuine": "Own brand"}


# ------------------------------------------------------------------ converters
def f(v, d=2):
    """Float or None. Never NaN - NaN in the payload fails the ship gate."""
    if v is None:
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if x != x or x in (float("inf"), float("-inf")):
        return None
    return round(x, d)


def i(v):
    x = f(v, 0)
    return None if x is None else int(x)


def frac_pct(v, d=2):
    """0-1 fraction -> percent. capture_rate, high_risk_rev_pct, bvp_share_eur."""
    x = f(v, 8)
    return None if x is None else round(x * 100, d)


def as_pct(v, d=2):
    """Already in percent. gps_pct, percentile_rank, wallet_2030_vs_2024_pct."""
    return f(v, d)


def eur(v, d=2):
    return f(v, d)


def build_uio_mix() -> dict:
    """Vehicles in service split by vehicle family, per market.

    This is what decides which maintenance schedule applies. The `scope` label in the dimension
    file is not reliable for this: four markets are labelled MIXED while being 91% or more one
    family, so the label alone would give them no interval at all when the dominant family's
    schedule plainly applies."""
    p = os.path.join(ROOT, "03_analytics", "Isuzu", "prism", "data", "uio_by_model_bucket.csv")
    if not os.path.exists(p):
        return {}
    df = pd.read_csv(p)
    out = {}
    for _, r in df.iterrows():
        code = clean(r.distributor_code)
        if not code:
            continue
        truck = (f(r.cv_std_uio) or 0.0) + (f(r.f_series_uio) or 0.0)
        pickup = f(r.lcv_uio) or 0.0
        tot = truck + pickup
        out[code] = {
            "truck_uio": i(truck), "pickup_uio": i(pickup), "total_uio": i(tot),
            "truck_pct": eur(truck / tot * 100, 1) if tot else None,
            "pickup_pct": eur(pickup / tot * 100, 1) if tot else None,
            "source_year": clean(r.source_year),
        }
    return out


def read(name: str) -> pd.DataFrame:
    """Read a CSV by name under 01_data/00_derived, or by repo-relative path when the
    name contains a separator (e.g. '01_data/17_interactions/x.csv')."""
    p = name if os.path.isabs(name) else (
        os.path.normpath(os.path.join(ROOT, name))
        if ("/" in name or os.sep in name) else os.path.join(D, name)
    )
    if not os.path.exists(p):
        raise SystemExit(f"FATAL source missing: {p}")
    return pd.read_csv(p)


# ------------------------------------------------------- monthly billing index
_SF_CACHE: dict | None = None


def monthly_billing() -> dict:
    """Monthly billed parts value per market, from the billing line file.

    This is the only source with true month grain, so it carries the dynamics and the
    like-for-like window. Credit notes and returns are excluded, as everywhere else.
    """
    global _SF_CACHE
    if _SF_CACHE is not None:
        return _SF_CACHE
    print("  reading billing lines for month grain ...", flush=True)
    sf = pd.read_parquet(os.path.join(D, "sales_fact.parquet"),
                         columns=["billing_date", "sold_to_sap", "net_sales_value",
                                  "billed_qty", "saty", "year"])
    dim = read("distributor_dimension.csv")
    mp = {}
    for _, r in dim.iterrows():
        code = clean(r.distributor_code)
        if code:
            mp[r.sold_to_sap] = code
    sf = sf[~sf.saty.isin(["CR", "RE"])].copy()
    sf["db"] = sf.sold_to_sap.map(mp)
    sf = sf[sf.db.notna()]
    d = pd.to_datetime(sf.billing_date)
    sf["ym"] = d.dt.strftime("%Y-%m")
    sf["mon"] = d.dt.month
    sf["y"] = d.dt.year

    by = {}
    for (db, y, m), g in sf.groupby(["db", "y", "mon"]):
        by.setdefault(db, {}).setdefault(int(y), {})[int(m)] = {
            "eur": float(g.net_sales_value.sum()), "qty": float(g.billed_qty.sum()),
        }
    months = sorted(sf.ym.unique().tolist())
    _SF_CACHE = {"by": by, "months": months, "last": str(d.max().date()),
                 "first": str(d.min().date())}
    return _SF_CACHE


def h1(row: dict, year: int) -> dict | None:
    """Sum the window months for a market-year, from the monthly index."""
    yr = row.get(year)
    if not yr:
        return None
    got = [yr[m] for m in range(1, YTD_MONTHS + 1) if m in yr]
    if len(got) < YTD_MONTHS:
        return None
    return {"eur": sum(g["eur"] for g in got), "qty": sum(g["qty"] for g in got),
            "months": len(got)}


def full_year(row: dict, year: int) -> dict | None:
    yr = row.get(year)
    if not yr:
        return None
    got = [yr[m] for m in range(1, 13) if m in yr]
    if len(got) < 12:
        return None
    return {"eur": sum(g["eur"] for g in got), "qty": sum(g["qty"] for g in got),
            "months": len(got)}


def monthly_series(row: dict, months: list[str]) -> list[dict]:
    """Every available month for one market, in order, as a dynamics series."""
    out = []
    for ym in months:
        y, m = int(ym[:4]), int(ym[5:7])
        v = (row.get(y) or {}).get(m)
        out.append({"ym": ym, "eur": eur(v["eur"]) if v else None,
                    "qty": i(v["qty"]) if v else None})
    return [x for x in out if x["eur"] is not None]


# ---------------------------------------------------------------- verification
def load_verification() -> dict:
    p = os.path.join(D, "_verification_report.json")
    if not os.path.exists(p):
        raise SystemExit(f"FATAL verification report missing: {p}")
    with open(p, encoding="utf-8") as fh:
        r = json.load(fh)
    s = r.get("summary") or {}
    return {
        "generated_at": r.get("generated_at"),
        "pass": s.get("pass"), "warn": s.get("warn"), "fail": s.get("fail"),
        "ok": bool(s.get("ok")),
    }


SLUG_LABEL = {
    "air_filter": "Air filter", "blower_filter": "Blower unit filter", "brake_lining": "Brake lining",
    "brake_pad": "Brake pad", "brake_rotor": "Brake rotor", "brake_shoe": "Brake shoe",
    "bushing": "Bushing", "center_bearing": "Centre bearing", "clutch_booster": "Clutch booster",
    "clutch_disc": "Clutch disc", "clutch_kit": "Clutch kit",
    "clutch_pressure_plate": "Clutch pressure plate", "engine_mount": "Engine mount",
    "fan_belt": "Fan belt", "fuel_filter": "Fuel filter", "generator": "Generator",
    "hub_bearing": "Hub bearing", "hub_oil_seal": "Hub oil seal", "king_pin": "King pin",
    "leaf_spring": "Leaf spring", "oil_filter": "Oil filter", "pilot_bearing": "Pilot bearing",
    "release_bearing": "Release bearing", "shock_absorber": "Shock absorber",
    "starter": "Starter motor", "urea_filter": "Urea (AdBlue) filter", "water_pump": "Water pump",
    "wheel_pin": "Wheel pin", "wiper_blade": "Wiper blade",
    "air_filter_assembly": "Air filter assembly",
    # part-family labels from the mix and risk layers
    "Belts_Cooling": "Belts and cooling",
    "Cab_Misc": "Cab and interior",
    "Clutch_Driveline": "Clutch and driveline",
    "PMS_Filters": "Service filters",
    "Suspension_Chassis": "Suspension and chassis",
    "Electrical": "Electrical",
}


def pretty(name: str) -> str:
    """Turn a pipeline slug into a label a distributor can read: 'fuel_filter' -> 'Fuel filter'."""
    s = str(name).strip()
    if s in SLUG_LABEL:
        return SLUG_LABEL[s]
    return " ".join(w.capitalize() for w in s.replace("-", "_").split("_") if w)


def clean(v) -> str:
    """pandas turns a missing value into the string 'nan' or 'None', which is truthy and
    silently creates junk dimension members such as a 'scope:nan' peer group."""
    if v is None:
        return ""
    s = str(v).strip()
    return "" if s.lower() in ("nan", "none", "null", "-") else s


# ------------------------------------------------------------------- dimension
def load_dimension() -> tuple[dict, list[str]]:
    dim = read("distributor_dimension.csv")
    dbs: dict[str, dict] = {}
    for _, r in dim.iterrows():
        code = clean(r.distributor_code)
        if not code or clean(r.network_role) != "network_db" or code in dbs:
            continue
        name = clean(r.customer_name)
        dbs[code] = {
            "code": code,
            "name": name or code,
            "scope": clean(r.scope) or "UNSPECIFIED",
            "region": clean(r.region) or "UNSPECIFIED",
            "in_pms": clean(r.in_pms_source).lower() == "yes",
            "fy2026_net_sales_eur": eur(r.fy2026_net_sales_eur),
        }
    return dbs, sorted(dbs)


# ------------------------------------------------------------------- peer groups
SCOPE_LABEL = {
    "CV": "CV truck distributors",
    "LCV": "LCV and pickup distributors",
    "MIXED": "Mixed CV and LCV distributors",
}
REGION_LABEL = {
    "UK": "UK and Ireland", "WEST": "Western Europe", "NORDICS": "Nordics",
    "EAST": "Central and Eastern Europe", "SOUTH": "Southern Europe",
    "CIS": "CIS countries", "MIDDLE_EAST": "Middle East", "ISRAEL": "Israel",
    "MENA": "Middle East and North Africa", "DACH": "DACH", "BENELUX": "Benelux",
    "IBERIA": "Iberia", "MED": "Mediterranean",
}


def build_peer_groups(dbs: dict) -> dict:
    """Peer groups. Customer-type first, per Jerome: an LCV market is benchmarked against
    LCV markets. Membership is never named - only the count and the median travel.

    A customer-type pool is added per scope, because the exact scope can be too thin to
    benchmark: ITUK is a CV market and there are only two CV markets in the network, so a
    median of two would read as a benchmark when it is one other market. The pool widens to
    include mixed-customer markets, which is still a defensible comparison for a truck
    business, and it is labelled so the reader knows what they are being compared with."""
    groups: dict[str, dict] = {}

    def add(key, label, members, kind):
        m = sorted(x for x in members if x in dbs)
        groups[key] = {"key": key, "label": label, "kind": kind, "members": m,
                       "thin": len(m) < PEER_MIN_MEMBERS}

    scopes = {d["scope"] for d in dbs.values()}
    for scope in sorted(scopes):
        add(f"scope:{scope}", SCOPE_LABEL.get(scope, f"{scope} distributors"),
            [c for c, d in dbs.items() if d["scope"] == scope], "scope")

    # Pools: the fallback used when the exact customer type is too thin.
    add("pool:CV", "CV and mixed-customer markets",
        [c for c, d in dbs.items() if d["scope"] in ("CV", "MIXED")], "pool")
    add("pool:LCV", "LCV and pickup markets",
        [c for c, d in dbs.items() if d["scope"] in ("LCV",)], "pool")
    add("pool:MIXED", "Mixed and CV markets",
        [c for c, d in dbs.items() if d["scope"] in ("MIXED", "CV")], "pool")

    for reg in sorted({d["region"] for d in dbs.values()}):
        add(f"region:{reg}", REGION_LABEL.get(reg, reg.title()),
            [c for c, d in dbs.items() if d["region"] == reg], "region")

    # Fleet-size bands, so a small market is not benchmarked against a giant.
    w = read("wallet_waterfall.csv")
    u25 = w[w.year == 2025].set_index("distributor_code").uio_units.to_dict()
    for code in dbs:
        dbs[code]["uio_2025"] = i(u25.get(code))
    bands = [("fleet:xs", "Under 2,000 vehicles", 0, 2000),
             ("fleet:s", "2,000 to 9,999 vehicles", 2000, 10000),
             ("fleet:m", "10,000 to 24,999 vehicles", 10000, 25000),
             ("fleet:l", "25,000 vehicles and above", 25000, 10**9)]
    for key, label, lo, hi in bands:
        add(key, label, [c for c, d in dbs.items()
                         if d.get("uio_2025") is not None and lo <= d["uio_2025"] < hi], "fleet")
    add("all", "All ISZE parts markets", list(dbs), "all")
    return groups


def default_peer_for(groups: dict, code: str, dbs: dict) -> str | None:
    """The best defensible benchmark for one market: exact customer type, else the customer-
    type pool, else the region, else everything."""
    info = dbs.get(code) or {}
    scope = info.get("scope")
    candidates = [f"scope:{scope}", f"pool:{scope}", f"region:{info.get('region')}", "all"]
    for key in candidates:
        g = groups.get(key)
        if g and not g["thin"] and code in g["members"]:
            return key
    for key in candidates:
        g = groups.get(key)
        if g and not g["thin"]:
            return key
    return "all"


# ---------------------------------------------------------------------- modules
def mod_evolution(dbs: dict) -> dict:
    """Module 1 - is the parts business growing, and is it accelerating or slowing?

    All comparisons are like-for-like: the same months of each year, and an average month so a
    part-year total is never set against a full-year total. Monthly movement carries the
    dynamics, because a single annual percentage hides whether a market is recovering or
    falling away inside the year."""
    ex = read("aim_exposure_by_db_year.csv")          # total parts net sales, 22 DBs
    gps = read("gps_spu_by_distributor.csv")          # GPS-eligible parts sales
    mb = monthly_billing()
    months = mb["months"]

    rows = []
    for code in dbs:
        e = ex[(ex.distributor_code == code) & (ex.year.isin(YEARS))]
        g = gps[(gps.distributor_code == code) & (gps.year.isin(YEARS))]
        if e.empty:
            rows.append({"db": code, "years": [], "ytd": [], "monthly": [],
                         "metric_growth_pct": None, "metric_avg_month_eur": None,
                         "unavailable": "No billing extract for this market"})
            continue

        by_year = {int(r.year): r for _, r in e.iterrows()}
        gy = {int(r.year): r for _, r in g.iterrows()}
        series = []
        for y in YEARS:
            r = by_year.get(y)
            if r is None:
                continue
            series.append({
                "year": y,
                "parts_eur": eur(r.net_sales_eur),
                "gps_eligible_eur": eur(gy[y].total_sales_eur) if y in gy else None,
                "warranty_eur": eur(gy[y].warranty_parts_eur) if y in gy else None,
                "uio": i(gy[y].uio_units) if y in gy else None,
                "is_part_year": y == CURRENT_YEAR,
            })

        # ---- like-for-like: same months of each year, plus an average month
        mrow = mb["by"].get(code, {})
        ytd = []
        for y in YEARS:
            w = h1(mrow, y)
            if not w:
                continue
            ytd.append({
                "year": y, "eur": eur(w["eur"]), "qty": i(w["qty"]), "months": w["months"],
                "avg_month_eur": eur(w["eur"] / w["months"]),
                "avg_month_qty": i(w["qty"] / w["months"]),
                "is_part_year": y == CURRENT_YEAR,
            })
        growth = None
        prior = next((x for x in ytd if x["year"] == CURRENT_YEAR - 1), None)
        cur = next((x for x in ytd if x["year"] == CURRENT_YEAR), None)
        if cur and prior and prior["eur"]:
            growth = f((cur["eur"] / prior["eur"] - 1) * 100, 1)

        # full-year context, for the table only - never used to compare against a part year
        full = []
        for y in YEARS:
            w = full_year(mrow, y)
            if not w:
                continue
            full.append({"year": y, "eur": eur(w["eur"]),
                         "avg_month_eur": eur(w["eur"] / w["months"]), "months": w["months"]})

        # ---- dynamics: every month, so a trend can be seen rather than inferred
        mseries = monthly_series(mrow, months)

        row = {
            "db": code, "years": series, "ytd": ytd, "full": full, "monthly": mseries,
            "metric_growth_pct": growth,
            "metric_avg_month_eur": cur["avg_month_eur"] if cur else None,
            "decomp": None, "forward": None, "unavailable": None,
        }
        rows.append(row)

    idx = {r["db"]: r for r in rows}

    # How the CY2024 -> CY2025 move splits, summed across the classified part families. The
    # source has NO mix leg (delta_mix_eur is zero on every row) so volume and price only.
    # It also covers only the classified families, so the coverage share is carried and stated.
    wf = read("revenue_waterfall.csv")
    for code in dbs:
        w = wf[(wf.distributor_code == code) & (wf.year_to == 2025)]
        if w.empty or code not in idx:
            continue
        vol = eur(w.delta_volume_eur.sum())
        price = eur(w.delta_price_eur.sum())
        base = eur(w.revenue_base_eur.sum())
        total_move = eur(w.total_delta_eur.sum())
        r = idx[code]
        full_base = (r.get("metric_cy2024_eur")
                     or next((f["eur"] for f in r.get("full", []) if f["year"] == 2024), None))
        r["decomp"] = {
            "volume_eur": vol, "price_eur": price, "base_eur": base, "total_eur": total_move,
            "families": int(w.product_family.nunique()),
            "mix_note": ("Summed across the classified part families, volume and price only. "
                         "The source carries no mix effect and does not cover every part, so it "
                         "explains part of the move rather than all of it."),
        }

    # Forward ceiling, modelled - labelled as modelled everywhere it appears. Field names
    # avoid the word "wallet": a distributor can read the embedded data, and the approved
    # wording is target spend ceiling.
    runway = read("revenue_runway.csv")
    for code in dbs:
        r = runway[(runway.distributor_code == code) & (runway.year == 2030)]
        if r.empty or code not in idx:
            continue
        t = r.iloc[0]
        idx[code]["forward"] = {
            "year": 2030, "ceiling_2030_eur": eur(t.wallet_eur),
            "vs_2024_pct": as_pct(t.wallet_2030_vs_2024_pct),
            "cum_ceiling_eur": eur(t.cum_wallet_2026_2030_eur),
            "modelled": True,
        }

    cur_tot = sum((next((x["eur"] for x in r["ytd"] if x["year"] == CURRENT_YEAR), 0) or 0)
                  for r in rows)
    return {"rows": rows,
            "network_ytd_eur": eur(cur_tot),
            "window_months": YTD_MONTHS,
            "window_label": f"January to June, {YTD_MONTHS} months",
            "month_count": len(months),
            "billing_first": mb["first"], "billing_last": mb["last"],
            "peer_metric_label": "Parts value, same six months of the year",
            "peer_metrics": ["metric_growth_pct", "metric_avg_month_eur"]}


def mod_dynamics(dbs: dict) -> dict:
    """Module 2 - monthly movement, so the trend is visible rather than inferred.

    A single annual percentage cannot show whether a market turned up or down part way through
    the year. This carries every month of billed parts value, and the same months of the prior
    year, so the comparison is like for like at every point."""
    mb = monthly_billing()
    months = mb["months"]

    rows = []
    for code in dbs:
        mrow = mb["by"].get(code, {})
        series = monthly_series(mrow, months)
        # prior-year month, aligned by month number, so each point has a like-for-like twin
        prior = []
        for s in series:
            y, m = int(s["ym"][:4]), int(s["ym"][5:7])
            pv = (mrow.get(y - 1) or {}).get(m)
            prior.append({"ym": f"{y-1}-{m:02d}",
                          "eur": eur(pv["eur"]) if pv else None})
        cur_year = [s for s in series if s["ym"].startswith(str(CURRENT_YEAR))]
        prev_same = [p for p in prior if p["ym"].startswith(str(CURRENT_YEAR - 1))]
        growth = None
        c = sum(x["eur"] or 0 for x in cur_year)
        p = sum(x["eur"] or 0 for x in prev_same)
        if p:
            growth = f((c / p - 1) * 100, 1)
        rows.append({
            "db": code, "monthly": series, "prior_year": prior,
            "metric_growth_pct": growth,
            "metric_avg_month_eur": eur(c / len(cur_year)) if cur_year else None,
            "months_with_data": len(series),
            "unavailable": None if series else "No monthly billing for this market",
        })

    return {"rows": rows, "months": months, "month_count": len(months),
            "billing_first": mb["first"], "billing_last": mb["last"],
            "peer_metric_label": "Average month, current year",
            "peer_metrics": ["metric_growth_pct", "metric_avg_month_eur"]}


def mod_gps(dbs: dict) -> dict:
    """Module 2 - target spend per truck versus what we actually billed."""
    w = read("wallet_waterfall.csv")
    g = read("gps_spu_by_distributor.csv")

    rows = []
    for code in dbs:
        ww = w[(w.distributor_code == code) & (w.year.isin(YEARS))]
        gg = g[(g.distributor_code == code) & (g.year.isin(YEARS))]
        if ww.empty and gg.empty:
            rows.append({"db": code, "years": [], "metric_gps_pct": None,
                         "metric_spu_eur": None, "unavailable": "No GPS coverage for this market"})
            continue
        series = []
        for y in YEARS:
            a = ww[ww.year == y]
            b = gg[gg.year == y]
            a = a.iloc[0] if not a.empty else None
            b = b.iloc[0] if not b.empty else None
            if a is None and b is None:
                continue
            series.append({
                "year": y,
                "ceiling_eur": eur(a.theoretical_wallet_eur) if a is not None else None,
                "captured_eur": eur(a.captured_total_eur) if a is not None else None,
                "addressable_gap_eur": eur(a.addressable_uncaptured_eur) if a is not None else None,
                "structural_eur": eur(a.structural_nonaddressable_eur) if a is not None else None,
                "beyond_ceiling_eur": eur(a.over_target_eur) if a is not None else None,
                # Two different denominators exist in the pipeline. The ceiling waterfall
                # must pair with its own share, so that is primary; the other benchmark is
                # carried separately and labelled as such.
                "gps_pct": as_pct(a.gps_pct) if a is not None else None,
                "gps_vs_upper_benchmark_pct": (frac_pct(b.gps_capture_vs_max) if b is not None else None),
                "spend_per_unit_eur": eur(b.spend_per_unit_eur) if b is not None else None,
                "uio": (i(b.uio_units) if b is not None else i(a.uio_units) if a is not None else None),
                "warranty_gap": (bool(b.warranty_data_gap)
                                 if b is not None and pd.notna(b.warranty_data_gap) else None),
            })
        y25 = next((s for s in series if s["year"] == 2025), None)
        rows.append({
            "db": code, "years": series,
            "metric_gps_pct": y25["gps_pct"] if y25 else None,
            "metric_spu_eur": y25["spend_per_unit_eur"] if y25 else None,
            "unavailable": None,
        })

    # ceiling composition for the honesty module: how much of it is a flat placeholder
    w25 = w[w.year == 2025].copy()
    w25["spu"] = w25.theoretical_wallet_eur / w25.uio_units
    flat = w25[w25.spu.round(1) == PLACEHOLDER_SPU_EUR]
    tot = float(w25.theoretical_wallet_eur.sum())
    # Flat-placeholder disclosure, kept market by market so a customer pack can be told
    # about itself without naming the other seven markets that share the placeholder.
    per_market = {}
    for _, r in w25.iterrows():
        per_market[str(r.distributor_code)] = {
            "spu": eur(r.spu),
            "is_placeholder": bool(round(float(r.spu), 1) == PLACEHOLDER_SPU_EUR),
        }
    ceiling = {
        "n_markets": int(len(w25)),
        "flat_markets": sorted(flat.distributor_code.tolist()),
        "flat_n": int(len(flat)),
        "flat_share_ceiling_pct": eur(flat.theoretical_wallet_eur.sum() / tot * 100, 1) if tot else None,
        "ceiling_total_eur": eur(tot),
        "spu_min": eur(w25.spu.min()), "spu_median": eur(w25.spu.median()), "spu_max": eur(w25.spu.max()),
        "placeholder_eur": PLACEHOLDER_SPU_EUR,
        "per_market": per_market,
    }
    return {"rows": rows, "ceiling": ceiling, "peer_metric_label": "Spend per truck CY2025",
            "peer_metrics": ["metric_gps_pct", "metric_spu_eur"]}


def mod_pms(dbs: dict) -> dict:
    """Module 4 - which service families are won, which are lost, and which way are they moving.

    Three corrections are applied here, all of which change the answer:

    1. LIKE FOR LIKE. The current-year expected-demand denominator in the source is a FULL year
       while the current-year actuals cover six months, so the filed current-year rate reads
       roughly half its like-for-like value. Both are carried and the window one is the basis.

    2. ADBLUE INTERVAL. The source uses a 39,499 km implied interval for the AdBlue filter. The
       authoritative GIDSS schedule says 200,000 km. That is a 5x error and it halved the
       modelled ITUK gap on its own: the gap on this category was overstated by roughly
       EUR 830,000 network-wide across the 18 scored markets.

    3. SCOPE. Two categories have never been bought by any CV market in the network, so scoring
       them against a CV market measures the model. They are dropped for CV markets, which
       lifts ITUK's scored capture rate by about 14 percentage points on its own.

    Categories with no replacement interval in the authoritative schedule are still shown, but
    they are marked `interval_confirmed: false` so the reader can tell a measured figure from a
    modelled one."""
    p = read("pms_capture_by_db_year.csv")
    p = p[p.line_type == "total"]
    ct = read("capture_trajectory.csv")
    ytd_frac = YTD_MONTHS / PERIODS_PER_YEAR
    uio_mix = build_uio_mix()

    # Per-market mileage, from the measured table where a market has one, else the model default.
    mb = monthly_billing()
    measured_kpi = read("warranty_cv_km_age_by_market.csv")
    km_measured = {}
    for _, r in measured_kpi.iterrows():
        m = clean(r.market).upper()
        v = f(r.km_yr_all_median, 0) if "km_yr_all_median" in measured_kpi.columns else None
        if m and v:
            km_measured[m] = v

    rows = []
    for code in dbs:
        sub = p[p.distributor_code == code].copy()
        if sub.empty:
            rows.append({"db": code, "categories": [], "metric_capture_pct": None,
                         "metric_gap_eur": None,
                         "unavailable": "No service-family demand model for this market"})
            continue

        scope = clean(dbs[code].get("scope"))
        # ONE mileage figure per market, coherent across every category. Using 50,000 km for a
        # brake interval while using 20,000 km for a filter in the same market would mix a truck
        # number with a car number and produce a denominator that belongs to neither.
        km_used, km_note = MEASURED_KM.get(code, KM_MODEL_FALLBACK)
        # The D-Max service interval is 20,000 km and the model assumes 20,000 km a year for a
        # pickup, so its annual distance and its interval coincide. The measured odometer figures
        # cover CV trucks, not pickups, so they are not applied to the pickup part of a fleet.
        KM_PICKUP = 20000

        mix = uio_mix.get(code) or {}
        truck_uio = mix.get("truck_uio") or 0.0
        pickup_uio = mix.get("pickup_uio") or 0.0
        fleet_uio = truck_uio + pickup_uio

        def exp_for(r):
            """Expected units = sum over the fleet of (vehicles x annual km / interval).

            Only the parts of the fleet that HAVE a replacement interval for this category can
            contribute. A market that is 60% pickup contributes on its pickup vehicles for a
            pickup-only category and says so, rather than treating the whole fleet as pickups.
            """
            cat = r.category_label
            total = 0.0
            covered = 0.0
            if truck_uio:
                iv = (ITUK_INTERVAL.get(cat) if code == "ITUK" and cat in ITUK_INTERVAL
                      else SCHEDULE_CV.get(cat))
                if iv:
                    total += truck_uio * (km_used / iv)
                    covered += truck_uio
            if pickup_uio:
                iv = SCHEDULE_LCV.get(cat)
                if iv:
                    total += pickup_uio * (KM_PICKUP / iv)
                    covered += pickup_uio
            if not covered:
                return r.expected_qty      # no part of this fleet has a sourced interval
            return total

        def coverage_for(cat):
            """What share of this market's fleet the expectation actually covers."""
            t = bool(truck_uio and (ITUK_INTERVAL.get(cat) if code == "ITUK"
                                    and cat in ITUK_INTERVAL else SCHEDULE_CV.get(cat)))
            p = bool(pickup_uio and SCHEDULE_LCV.get(cat))
            covered = (truck_uio if t else 0.0) + (pickup_uio if p else 0.0)
            return (covered / fleet_uio * 100.0) if fleet_uio else 0.0

        def basis_for(cat):
            """The basis must describe what ACTUALLY contributed, not what the schedule
            catalogue contains. A truck-only market has no pickup fleet, so a pickup-only
            category covers nothing here and must read as a placeholder, not as a schedule."""
            if code == "ITUK" and cat in ITUK_INTERVAL and truck_uio:
                return "ituk"
            t = bool(truck_uio and SCHEDULE_CV.get(cat))
            p = bool(pickup_uio and SCHEDULE_LCV.get(cat))
            if t and p:
                return "both_schedules"
            if t:
                return "cv_schedule"
            if p:
                return "lcv_schedule"
            return "placeholder"

        sub["exp_adj"] = sub.apply(exp_for, axis=1)
        sub["basis"] = sub.category_label.map(basis_for)
        dropped = sorted(set(sub.category_label) & CV_ZERO_SALES) if scope == "CV" else []
        # Reference year for the like-for-like comparison.
        ref = sub[sub.year == 2025]
        exp_ref = f(ref.exp_adj.sum(), 0)
        act_ref = f(ref.actual_qty.sum(), 0)

        cats = []
        for cat, cs in sub.groupby("category_label"):
            if cat in dropped:
                continue
            series = []
            for y in YEARS:
                y_ = cs[cs.year == y]
                if y_.empty:
                    continue
                r = y_.iloc[0]
                e = f(r.exp_adj, 0)
                a = f(r.actual_qty, 0)
                sp = f(r.avg_sp_eur)
                # Capture is ALWAYS actual over the adjusted expected, on both bases. The filed
                # rate is kept alongside only so the correction can be shown.
                filed = frac_pct(r.capture_rate)
                cap_adj = frac_pct(a / e) if e else None
                lfl = None
                if e and y == CURRENT_YEAR:
                    # The adjusted expected is a full-year figure. The current year is six
                    # months, so the window expectation is the six-month share of it. This must
                    # be divided, not multiplied: without it the window rate reads 17x too low.
                    lfl = frac_pct(a / (e * ytd_frac))
                elif e:
                    lfl = cap_adj
                # Gap rebuilt on the adjusted denominator, at the observed selling price.
                gap_new = max(0.0, (e - a) * sp) if (e and sp is not None) else None
                b = basis_for(cat)
                cov = coverage_for(cat)
                # A capture rate is only interpretable when the expectation covers essentially the
                # whole fleet. If it covers less, the numerator counts the whole market while the
                # denominator counts part of it, which produces nonsense: a market that is 99%
                # pickup reads 627% on a truck-only part, because a few truck units billed market
                # wide are divided by an expectation built on its tiny truck fleet alone. Such a
                # category is marked not scored rather than printed with a meaningless percentage.
                scored_here = cov >= MIN_COVERAGE_PCT
                series.append({
                    "year": y,
                    "capture_pct": filed,
                    "capture_adj_pct": cap_adj if scored_here else None,
                    "capture_lfl_pct": lfl if scored_here else None,
                    "capture_unscored_pct": None if scored_here else cap_adj,
                    "coverage_pct": eur(cov, 1),
                    "scored": scored_here,
                    "interval_km": (None if b == "placeholder" else
                                    (ITUK_INTERVAL.get(cat) if b == "ituk"
                                     else SCHEDULE_CV.get(cat) or SCHEDULE_LCV.get(cat))),
                    "basis": b,
                    "interval_confirmed": b != "placeholder",
                    "is_part_year": y == CURRENT_YEAR,
                    "gap_eur": eur(gap_new) if scored_here else None,
                    "gap_eur_source": eur(r.revenue_gap_eur),
                    "actual_eur": eur(r.actual_rev_eur),
                    "expected_qty": i(r.expected_qty),
                    "expected_qty_adj": i(e),
                    "actual_qty": i(a),
                    "avg_price_eur": sp,
                    "unbought_qty": i(e - a) if e is not None and a is not None else None,
                })
                continue
            tr = ct[(ct.distributor_code == code)
                    & (ct.pms_category == cs.iloc[0].pms_category) & (ct.year == 2025)]
            slope = r2 = None
            declining = None
            if not tr.empty:
                slope = frac_pct(tr.iloc[0].trend_slope_pp_per_year)
                r2 = f(tr.iloc[0].trend_r2, 2)
                declining = bool(tr.iloc[0].alert_declining)
            y25 = next((s for s in series if s["year"] == 2025), None)
            y26 = next((s for s in series if s["year"] == CURRENT_YEAR), None)
            b = basis_for(cat)
            cov = coverage_for(cat)
            scored_here = cov >= MIN_COVERAGE_PCT
            # The brake unit question is open: whether one paired front+rear job is one part unit
            # or two. Rather than pick one, the band is carried so the page can show both ends.
            unit_open = (scored_here and cat in ("Brake Pad", "Brake Shoe")
                         and ITUK_BRAKE_UNITS_OPEN and truck_uio > 0)
            cats.append({
                "category": str(cat), "years": series, "slope_pp": slope, "slope_r2": r2,
                "declining": declining,
                "interval_km": (None if b == "placeholder" else
                                (ITUK_INTERVAL.get(cat) if b == "ituk"
                                 else SCHEDULE_CV.get(cat) or SCHEDULE_LCV.get(cat))),
                "interval_cv_km": SCHEDULE_CV.get(cat),
                "interval_lcv_km": SCHEDULE_LCV.get(cat),
                "basis": b,
                "basis_label": BASIS_LABEL.get(b, b),
                "coverage_pct": eur(cov, 1),
                "scored": scored_here,
                "interval_confirmed": b != "placeholder",
                "interval_note": INTERVAL_NOTE.get(cat),
                "unit_definition_open": unit_open,
                "capture_2025_pct": (y25["capture_adj_pct"] if (y25 and scored_here) else None),
                "capture_2025_unscored_pct": (y25["capture_unscored_pct"] if y25 else None),
                "capture_2025_alt_pct": (frac_pct(y25["actual_qty"] / (y25["expected_qty_adj"] * 2))
                                         if unit_open and y25 else None),
                "capture_2026_lfl_pct": (y26["capture_lfl_pct"] if (y26 and scored_here) else None),
                "gap_2025_eur": (y25["gap_eur"] if (y25 and scored_here) else None),
                "gap_2025_eur_placeholder": (y25["gap_eur"] if (y25 and not scored_here) else None),
                "gap_2025_alt_eur": (eur(max(0.0, (y25["expected_qty_adj"] * 2 - y25["actual_qty"])
                                             * y25["avg_price_eur"]))
                                     if unit_open and y25 and y25["avg_price_eur"] else None),
                "gap_2025_eur_source": y25["gap_eur_source"] if y25 else None,
            })
        cats.sort(key=lambda c: -(c["gap_2025_eur"] or 0))

        s26 = sub[sub.year == CURRENT_YEAR]
        exp26 = f(sum(c["years"][-1]["expected_qty_adj"] for c in cats
                      if c["years"] and c["years"][-1]["year"] == CURRENT_YEAR
                      and c.get("scored")), 0)
        act26 = f(sum(c["years"][-1]["actual_qty"] for c in cats
                      if c["years"] and c["years"][-1]["year"] == CURRENT_YEAR
                      and c.get("scored")), 0)
        gap_ref = f(sum((c["gap_2025_eur"] or 0) for c in cats))
        gap_src = f(sum((c["gap_2025_eur_source"] or 0) for c in cats))
        # Split the gap by how much it can be trusted. Hiding the placeholder-based part would
        # remove EUR 657K of scale from ITUK; printing it unqualified would imply we know it.
        # So it is carried, and named.
        gap_firm = f(sum((c["gap_2025_eur"] or 0) for c in cats if c.get("scored")))
        gap_placeholder = f(sum((c["gap_2025_eur_placeholder"] or 0) for c in cats
                                if not c.get("scored")))

        rows.append({
            "db": code, "categories": cats, "scope": scope,
            "uio": i(sub.uio_units.max()) if sub.uio_units.notna().any() else None,
            "km_used": i(km_used), "km_note": km_note,
            "km_measured": km_used != KM_MODEL_FALLBACK[0],
            "truck_uio": i(truck_uio), "pickup_uio": i(pickup_uio),
            "truck_pct": eur(truck_uio / fleet_uio * 100, 1) if fleet_uio else None,
            "pickup_pct": eur(pickup_uio / fleet_uio * 100, 1) if fleet_uio else None,
            "fleet_note": ("-".join(
                p for p in [
                    ("%s trucks" % format(int(truck_uio), ",")) if truck_uio else "",
                    ("%s pickups" % format(int(pickup_uio), ",")) if pickup_uio else "",
                ] if p) or "fleet split not available"),
            "expected_qty_2025": i(exp_ref), "actual_qty_2025": i(act_ref),
            "expected_qty_2026": i(exp26), "actual_qty_2026": i(act26),
            "metric_capture_pct": frac_pct(act_ref / exp_ref) if exp_ref else None,
            "metric_capture_2026_lfl_pct": (frac_pct(act26 / (exp26 * ytd_frac))
                                            if exp26 else None),
            "metric_gap_eur": gap_ref,
            "metric_gap_firm_eur": gap_firm,
            "metric_gap_placeholder_eur": gap_placeholder,
            "gap_eur_source": gap_src,
            "gap_correction_eur": eur(gap_ref - gap_src),
            "dropped_categories": dropped,
            "scored_categories": len(cats),
            "unscored_categories": [c["category"] for c in cats if not c.get("scored")],
            "unconfirmed_categories": [c["category"] for c in cats if not c["interval_confirmed"]],
            "interval_adjusted_categories": [c["category"] for c in cats if c["interval_confirmed"]],
            "unavailable": None,
        })

    return {"rows": rows,
            "peer_metric_label": "Service-demand capture, CY2025 full year",
            "peer_metrics": ["metric_capture_pct", "metric_gap_eur"],
            "window_months": YTD_MONTHS,
            "intervals": {"cv_schedule": SCHEDULE_CV, "lcv_schedule": SCHEDULE_LCV,
                          "ituk_own": ITUK_INTERVAL},
            "dropped_for_cv": sorted(CV_ZERO_SALES),
            "denominator_note": (
                f"The current-year expected-demand figure in the source is a full 12 months "
                f"while the current-year actuals cover {YTD_MONTHS} months, so the filed "
                f"current-year rate reads roughly half its like-for-like value."),
            "interval_note": (
                "Expected demand is rebuilt on the component replacement intervals in the "
                "supplier maintenance schedules rather than the model's placeholder factors. "
                "Where no replacement interval exists, the figure is marked as unconfirmed "
                "instead of being presented as measured.")}


def mod_actions(dbs: dict) -> dict:
    """Module 8 - what to act on, at part-number level.

    This is the conclusions layer: a named part, what is happening to it, what it is worth and
    what we propose to do. Part numbers carry a description where one exists in any approved
    layer; where it does not, the line is shown with its group rather than dropped or invented.
    Pricing-review signals are excluded from a customer pack, because that work is ours."""
    al = read("action_ledger_open.csv")

    # One description map from every approved layer that carries one.
    desc: dict[str, str] = {}
    for f, pnc, dc in [("revision_book_b_top_review.csv", "pn", "description"),
                       ("dealer_sellout_pn_audit.csv", "part_number", "description"),
                       ("sellout_aim_top_pn_2025.csv", "part_number", "description")]:
        p = os.path.join(D, f)
        if not os.path.exists(p):
            continue
        try:
            df = pd.read_csv(p, usecols=[pnc, dc])
        except Exception:
            continue
        df["k"] = df[pnc].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        df["v"] = df[dc].astype(str).str.strip()
        df = df[(df.v != "") & (df.v.str.lower() != "nan")]
        for k, v in zip(df.k, df.v):
            desc.setdefault(k, v)

    al["k"] = al.entity_key.astype(str).str.strip()
    al["desc"] = al.k.map(desc)

    rows = []
    for code in dbs:
        d = al[al.db_code == code]
        pns = d[d.entity_grain == "PN"]
        lines = []
        for _, t in pns.iterrows():
            sig = str(t.signal_type)
            lines.append({
                "pn": str(t.entity_key),
                "description": (str(t.desc) if isinstance(t.desc, str) and t.desc
                                else None),
                "signal": sig,
                "signal_label": SIGNAL_LABEL.get(sig, sig.replace("_", " ").title()),
                "customer_ok": sig in SIGNAL_CUSTOMER_OK,
                "eur": eur(t.eur_at_stake),
                "basis": str(t.eur_basis) if pd.notna(t.eur_basis) else None,
                "action": (ACTION_LABEL.get(str(t.recommended_action), None)
                           if pd.notna(t.recommended_action) else None),
                "seen": str(t.last_seen_on) if pd.notna(t.last_seen_on) else None,
            })
        lines.sort(key=lambda x: -(x["eur"] or 0))

        # group the conclusions so the reader gets a short list, not a data dump
        by_signal: dict[str, dict] = {}
        for l in lines:
            if not l["customer_ok"]:
                continue
            g = by_signal.setdefault(l["signal"], {"signal": l["signal"],
                                                   "label": l["signal_label"],
                                                   "eur": 0.0, "n": 0})
            g["eur"] += l["eur"] or 0
            g["n"] += 1
        for g in by_signal.values():
            g["eur"] = eur(g["eur"])

        # The payload carries only the lines a reader can actually see, plus the grouped totals.
        # The full register is 22,738 PN rows; embedding all of it would make the file megabytes
        # larger for no reader benefit, since the panel shows the largest lines and a filter.
        top = [l for l in lines if l["customer_ok"]][:ACTION_LINE_CAP]
        rows.append({
            "db": code,
            "top": top,
            "by_signal": sorted(by_signal.values(), key=lambda x: -(x["eur"] or 0)),
            "metric_eur_at_stake": eur(sum(l["eur"] or 0 for l in lines if l["customer_ok"])),
            "n_lines": len([l for l in lines if l["customer_ok"]]),
            "n_private": len([l for l in lines if not l["customer_ok"]]),
            "n_named": len([l for l in top if l["description"]]),
            "unavailable": None if lines else "No part-level actions raised for this market",
        })
    return {"rows": rows,
            "peer_metric_label": "Value in raised part-level actions",
            "peer_metrics": ["metric_eur_at_stake"],
            "basis_note": ("Value is the trailing twelve months or last twelve months at the "
                           "observed price, depending on the source. Each line carries its own "
                           "basis."),
            "customer_ok_signals": sorted(SIGNAL_CUSTOMER_OK)}


def mod_mix(dbs: dict) -> dict:
    """Module 4 - is the mix drifting toward competing brands?"""
    m = read("mix_genuine_bvp_pms.csv")
    c = read("db_parts_mix_classification.csv")

    rows = []
    for code in dbs:
        cl = c[c.distributor_code == code]
        yr = []
        for y in YEARS:
            r = cl[cl.year == y]
            if r.empty:
                continue
            t = r.iloc[0]
            yr.append({"year": y, "total_eur": eur(t.total_eur), "bvp_eur": eur(t.bvp_eur),
                       "genuine_contested_eur": eur(t.genuine_contested_eur),
                       "genuine_only_eur": eur(t.genuine_only_eur),
                       "bvp_pct": frac_pct(t.bvp_pct),
                       "genuine_only_pct": frac_pct(t.genuine_only_pct),
                       "contested_bvp_capture": frac_pct(t.contested_bvp_capture)})

        bm = m[m.distributor_code == code]
        fams = []
        for fam, fs in bm.groupby("product_family"):
            f25 = fs[fs.year == 2025]
            if f25.empty:
                continue
            t = f25.iloc[0]
            fams.append({"family": pretty(fam), "total_eur": eur(t.total_eur),
                         "bvp_share_pct": frac_pct(t.bvp_share_eur),                         "yoy_pp": as_pct(t.bvp_share_eur_yoy_pp),
                         "substitution_flag": (str(t.substitution_flag)
                                               if pd.notna(t.substitution_flag) else None)})
        fams.sort(key=lambda x: -(x["total_eur"] or 0))

        y25 = next((x for x in yr if x["year"] == 2025), None)
        rows.append({"db": code, "years": yr, "families": fams,
                     "metric_bvp_pct": y25["bvp_pct"] if y25 else None,
                     "unavailable": None if yr else "No mix extract for this market"})
    return {"rows": rows, "peer_metric_label": "Other-brand share of parts value CY2025",
            "peer_metrics": ["metric_bvp_pct"]}


def mod_aim(dbs: dict) -> dict:
    """Module 5 - our own part-group classification, and how much euro sits in the groups
    we are least likely to keep. Group mix is CY2025 sales-to-dealer only; the trajectory
    is 2023-2026. Both vintages are printed on the face."""
    ex = read("aim_exposure_by_db_year.csv")
    fam = read("aim_bvp_family_risk.csv")
    a25 = read("sellout_aim_by_aim_l1_2025.csv")
    npct = read("network_percentile.csv")

    rows = []
    for code in dbs:
        e = ex[(ex.distributor_code == code) & (ex.year.isin(YEARS))]
        yr = []
        for y in YEARS:
            r = e[e.year == y]
            if r.empty:
                continue
            t = r.iloc[0]
            yr.append({"year": y, "net_sales_eur": eur(t.net_sales_eur),
                       "matched_eur": eur(t.aim_matched_rev_eur),
                       "match_rate_pct": frac_pct(t.aim_match_rate_rev),
                       "high_risk_eur": eur(t.high_risk_rev_eur),
                       "high_risk_pct": frac_pct(t.high_risk_rev_pct),
                       "strategic_eur": eur(t.strategic_rev_eur)})

        # Which group of our own part classification this market sits in. The percentile is
        # computed on the risk score, where a HIGHER score is worse, so a high percentile here
        # means MORE exposure even though the underlying column is called "rank".
        pct = npct[(npct.distributor_code == code) & (npct.year == 2025) & (npct.metric == "aim_risk")]
        y25 = next((x for x in yr if x["year"] == 2025), None)
        pct_val = as_pct(pct.iloc[0].percentile_rank, 0) if not pct.empty else None

        # Group mix from the sales-to-dealer file. Its buckets are genuine_only / genuine_contested
        # / bvp, not a "total" bucket, so the value is reconstructed and the buckets are kept.
        g = a25[a25.distributor_code == code]
        groups = []
        for l1, gs in g.groupby("aim_l1_report"):
            by_bucket = {}
            for _, t in gs.iterrows():
                by_bucket[str(t.aim_bucket)] = (by_bucket.get(str(t.aim_bucket)) or 0) + (eur(t.eur) or 0)
            v = eur(sum(by_bucket.values()))
            if not v:
                continue
            groups.append({"group": str(l1), "eur": v,
                           "genuine_only_eur": eur(by_bucket.get("genuine_only")),
                           "genuine_contested_eur": eur(by_bucket.get("genuine_contested")),
                           "bvp_eur": eur(by_bucket.get("bvp"))})
        groups.sort(key=lambda x: -(x["eur"] or 0))

        fr = fam[(fam.distributor_code == code) & (fam.year == 2025)]
        fams = []
        for _, t in fr.iterrows():
            fams.append({"family": pretty(t.product_family),
                         "total_eur": eur((t.genuine_eur or 0) + (t.bvp_eur or 0)),
                         "bvp_share_pct": frac_pct(t.bvp_share_eur),
                         "high_risk_eur": eur(t.aim_high_risk_rev_eur),
                         "high_risk_pct": frac_pct(t.aim_high_risk_rev_pct),
                         "network_median_pct": frac_pct(t.network_median_risk_pct),
                         "vs_network_pp": as_pct(t.vs_network_risk_pp)})
        fams.sort(key=lambda x: -(x["high_risk_eur"] or 0))

        rows.append({"db": code, "years": yr, "groups": groups, "families": fams,
                     "aim_risk_percentile": pct_val,
                     "metric_high_risk_pct": y25["high_risk_pct"] if y25 else None,
                     "metric_high_risk_eur": y25["high_risk_eur"] if y25 else None,
                     "group_total_eur": eur(sum(x["eur"] or 0 for x in groups)),
                     "group_source": ("CY2025 sales-to-dealer file" if groups else None),
                     "unavailable": None if yr else "No classification coverage for this market"})
    return {"rows": rows, "peer_metric_label": "Euro in high-risk part groups CY2025",
            "peer_metrics": ["metric_high_risk_pct", "metric_high_risk_eur"],
            "group_vintage": "CY2025 sales-to-dealer file",
            "trajectory_vintage": "CY2023 to CY2026 billing"}


def mod_subgroup(dbs: dict) -> dict:
    """Module 6 - subcategories, the competing-brand split, and why the gap exists."""
    s = read("substitution_by_db_year.csv")
    cr = read("capture_recovery_model.csv")

    rows = []
    for code in dbs:
        sub = s[(s.distributor_code == code) & (s.year == 2025)]
        groups = []
        for name, gs in sub.groupby("product_subgroup"):
            gen = eur(gs.genuine_eur.sum())
            bvp = eur(gs.bvp_eur.sum())
            groups.append({
                "subgroup": pretty(name), "total_eur": eur((gen or 0) + (bvp or 0)),
                "genuine_eur": gen, "bvp_eur": bvp,
                "bvp_share_pct": frac_pct(gs.bvp_share_units.mean()) if gs.bvp_share_units.notna().any() else None,
                "pairs_both_pct": frac_pct(gs.pct_pairs_both.mean()) if gs.pct_pairs_both.notna().any() else None,
                "pairs_bvp_only_pct": frac_pct(gs.pct_pairs_bvp_only.mean()) if gs.pct_pairs_bvp_only.notna().any() else None,
                "genuine_only_pairs": i(gs.pairs_genuine_only.sum()),
                "bvp_only_pairs": i(gs.pairs_bvp_only.sum()),
            })
        groups.sort(key=lambda x: -(x["total_eur"] or 0))

        c = cr[cr.distributor_code == code]
        by_type: dict[str, float] = {}
        for _, t in c.iterrows():
            k = str(t.gap_type)
            by_type[k] = by_type.get(k, 0.0) + (eur(t.gap_revenue_at_genuine) or 0.0)
        gaps = [{"gap_type": k, "label": GAP_TYPE_LABEL.get(k, k.replace("_", " ")),
                 "eur": eur(v)} for k, v in sorted(by_type.items(), key=lambda x: -x[1])]

        top = c.sort_values("gap_revenue_at_genuine", ascending=False).head(8)
        gap_rows = [{"category": pretty(t.pms_category),
                     "gap_type": str(t.gap_type),
                     "label": GAP_TYPE_LABEL.get(str(t.gap_type), ""),
                     "eur": eur(t.gap_revenue_at_genuine), "gap_units": i(t.gap_units),
                     "capture_pct": frac_pct(t.capture_rate_actual)}
                    for _, t in top.iterrows()]

        tot_q = f(sub.total_qty.sum(), 0)
        bvp_q = f(sub.bvp_qty.sum(), 0)
        rows.append({"db": code, "groups": groups, "gap_types": gaps, "top_gaps": gap_rows,
                     "substitution_eur": eur(sub.bvp_eur.sum()),
                     "metric_bvp_share_pct": frac_pct(bvp_q / tot_q) if tot_q else None,
                     "unavailable": None if not sub.empty else "No subcategory cross-reference for this market"})
    return {"rows": rows, "peer_metric_label": "Other-brand share of units CY2025",
            "peer_metrics": ["metric_bvp_share_pct"],
            "gap_vintage": "CY2026 model"}


def mod_unbilled(dbs: dict) -> dict:
    """Module 7 - where demand exists and we billed nothing, at service-family level."""
    pm = read("pms_opportunity_matrix.csv")
    p = read("pms_capture_by_db_year.csv")
    p = p[p.line_type == "total"]

    rows = []
    for code in dbs:
        q = pm[(pm.distributor_code == code) & (pm.year == 2025)]
        if q.empty:
            rows.append({"db": code, "families": [], "metric_gap_eur": None,
                         "unavailable": "No opportunity model for this market"})
            continue
        agg = q.groupby("pms_category").agg(
            gap=("revenue_gap_eur", "sum"), quotable=("revenue_gap_quotable", "sum"),
            tam=("tam_eur", "sum"), sp=("avg_sp_eur", "mean")).reset_index()
        src = p[(p.distributor_code == code) & (p.year == 2025)]
        cap = src.set_index("pms_category")
        fams = []
        for _, t in agg.iterrows():
            cat = t.pms_category
            c = cap.loc[cat] if cat in cap.index else None
            exp = f(c.expected_qty, 0) if c is not None else None
            act = f(c.actual_qty, 0) if c is not None else None
            fams.append({
                "category": str(c.category_label if c is not None else cat).replace("_", " ").title(),
                "gap_eur": eur(t.gap), "quotable_eur": eur(t.quotable), "tam_eur": eur(t.tam),
                "avg_price_eur": eur(t.sp),
                "capture_pct": frac_pct(act / exp) if exp else None,
                "expected_qty": i(exp), "actual_qty": i(act),
                "unbought_qty": i((exp - act) if exp is not None and act is not None else None),
            })
        fams.sort(key=lambda x: -(x["gap_eur"] or 0))
        rows.append({"db": code, "families": fams,
                     "uio": i(src.uio_units.max()) if not src.empty else None,
                     "metric_gap_eur": eur(agg.gap.sum()),
                     "unavailable": None})
    return {"rows": rows, "peer_metric_label": "Unbought service-part value CY2025",
            "peer_metrics": ["metric_gap_eur"]}


def mod_league(dbs: dict) -> dict:
    """Module 8 - INTERNAL ONLY. Who is critical, and what evidence says so."""
    risk = read("db_aftersales_risk.csv")
    ew = read("early_warning.csv")
    da = read("defection_alerts.csv")
    ah = read("01_data/17_interactions/account_health_latest_flagged.csv")
    w = read("wallet_waterfall.csv")

    rows = []
    for code in dbs:
        r = risk[risk.distributor_code == code]
        r = r.iloc[0] if not r.empty else None
        e = ew[ew.distributor_code == code]
        e = e.iloc[0] if not e.empty else None
        d = da[da.distributor_code == code]
        h = ah[ah.db_code == code]
        ww = w[(w.distributor_code == code) & (w.year == 2025)]
        ww = ww.iloc[0] if not ww.empty else None

        recoverable = None
        zero_rev = None
        if not d.empty:
            rec = d[d.alert.astype(str).str.contains("recover", case=False, na=False)]
            recoverable = eur(rec.trailing_12m_rev_eur.sum()) if not rec.empty else 0.0
            z = d[d.trailing_12m_rev_eur.fillna(0) == 0]
            zero_rev = eur(z.trailing_12m_rev_eur.sum()) if not z.empty else 0.0

        rows.append({
            "db": code,
            "risk_score": f(r.risk_score, 3) if r is not None else None,
            "risk_rank": i(r["rank"]) if r is not None else None,
            "net_sales_eur": eur(r.net_sales_eur) if r is not None else None,
            "undercut_pct": frac_pct(r.eucon_undercut_pct) if r is not None else None,
            "undercut_eur": eur(r.eucon_undercut_rev_eur) if r is not None else None,
            "high_risk_pct": frac_pct(r.high_risk_rev_pct) if r is not None else None,
            "contested_capture": frac_pct(r.contested_bvp_capture) if r is not None else None,
            "vor_urgent_share": frac_pct(r.vor_urgent_share) if r is not None else None,
            "gap_eur": eur(ww.addressable_uncaptured_eur) if ww is not None else None,
            "gps_pct": as_pct(ww.gps_pct) if ww is not None else None,
            "uio": i(ww.uio_units) if ww is not None else None,
            "ew_severity": i(e.severity) if e is not None else None,
            "ew_severity_name": str(e.severity_name) if e is not None else None,
            "ew_n_signals": i(e.n_signals) if e is not None else None,
            "ew_eur_exposed": eur(e.eur_exposed) if e is not None else None,
            "ew_why": str(e.why_this_cycle) if e is not None else None,
            "ew_sig_silence": f(e.sig_silence, 2) if e is not None else None,
            "ew_sig_capture": f(e.sig_capture, 2) if e is not None else None,
            "ew_sig_vor": f(e.sig_vor, 2) if e is not None else None,
            "ew_all_dormant": (bool(e.all_dormant)
                               if e is not None and pd.notna(e.all_dormant) else None),
            "defection_categories": i(len(d)) if not d.empty else 0,
            "defection_recoverable_eur": recoverable,
            "defection_zero_revenue_eur": zero_rev,
            "health_alert": str(h.iloc[0].alert_level) if not h.empty else None,
            "health_reasons": str(h.iloc[0].alert_reasons) if not h.empty else None,
        })
    rows.sort(key=lambda x: -(x["risk_score"] or 0))
    for n, r in enumerate(rows, 1):
        r["league_rank"] = n
    return {
        "rows": rows, "peer_metrics": [],
        "threshold_note": ("Alert thresholds are set by inspection, not calibrated against "
                           "outcomes. Treat severity as a conversation trigger, not a score."),
        "defection_note": ("Stopped-ordering counts are split: euro in categories that stopped "
                           "ordering but still trade elsewhere, versus categories where trailing "
                           "revenue is already zero. The second group is not recoverable and is not "
                           "counted as an opportunity."),
    }


def _dealer_audit() -> dict:
    """What dealer-level detail actually exists. Measured, not assumed.

    File names are deliberately not carried: they are internal pipeline artefacts and the
    word they contain is not approved wording. What matters to a reader is how many outlets
    and which years, and that is what is returned."""
    out: dict[str, dict] = {}
    for p in DEALER_LONG:
        try:
            df = pd.read_csv(p, usecols=lambda c: c in
                             ("distributor_code", "dealer_name", "grain", "year"))
        except Exception:
            continue
        code = str(df.distributor_code.iloc[0]) if "distributor_code" in df.columns and len(df) else "?"
        grains = sorted(df.grain.unique().tolist()) if "grain" in df.columns else []
        names = 0
        if "dealer_name" in df.columns:
            nm = df.dealer_name.fillna("").astype(str).str.strip()
            names = len({x for x in nm.unique() if x and x.lower() not in ("nan", "none", "-", "all")})
        years = sorted(df.year.dropna().astype(int).unique().tolist()) if "year" in df.columns else []
        rec = out.setdefault(code, {"code": code, "sources": [], "named_years": [],
                                    "max_dealers": 0, "dealer_grain_sources": 0})
        rec["sources"].append({"grain": ",".join(grains), "years": years, "dealers": names})
        if names > 1:
            rec["named_years"].extend(years)
            rec["dealer_grain_sources"] += 1
            rec["max_dealers"] = max(rec["max_dealers"], names)
    for rec in out.values():
        rec["named_years"] = sorted(set(rec["named_years"]))
        rec["has_dealer_detail"] = rec["dealer_grain_sources"] > 0
    return out


def mod_honesty(dbs: dict, verification: dict) -> dict:
    """Module 9 - what this page does not claim. Derived live, never copied."""
    p = read("pms_capture_by_db_year.csv")
    p25 = p[(p.year == 2025) & (p.line_type == "total")]

    wf = read("revenue_waterfall.csv")
    mix_dead = bool((wf.delta_mix_eur.fillna(0).abs() < 1e-9).all())

    dealer_cov = _dealer_audit()
    with_detail = sorted([c for c, v in dealer_cov.items() if v["has_dealer_detail"]])

    # Scope counts. A customer build restates these for one market so the pack never
    # describes how many markets exist, which markets are scored, or where detail exists.
    p25_codes = set(p25.distributor_code.unique())
    scored = sorted([c for c in dbs if c in p25_codes])
    scope = {
        "network_markets_n": len(dbs),
        "scored_markets_n": len(scored),
        "dealer_detail_n": len(with_detail),
        "captured_cells": int(len(p25)),
        "over_100": int(len(p25[p25.capture_rate > 1.0])),
        "over_100_share_pct": eur(len(p25[p25.capture_rate > 1.0]) / len(p25) * 100, 1) if len(p25) else None,
        "modelled_gap_eur": eur(p25.revenue_gap_eur.sum()),
        "fleet_uio": i(f(p25.uio_units.max(), 0)),
        "scored_markets": scored,
    }

    return {
        "verification": verification,
        "as_of": date.today().isoformat(),
        "current_year": CURRENT_YEAR,
        "scope": scope,
        "expected_demand_note": (
            "The units billed are real billing data. The expected demand they are compared against "
            "is a model built from assumed service intervals, pending supplier confirmation. Read the "
            "level as directional and the movement as the more reliable signal."),
        "settings_note": (
            "Every market is scored on the same approved settings. Those settings, and the list of "
            "markets they are applied to, are internal: this tells you what was measured, not how "
            "the network's own targets are set."),
        "mileage": {
            "model_default_km": KM_MODEL,
            "measured": [{"key": k, "km": v[0], "source": v[1], "note": v[2]} for k, v in KM.items()],
            "spread_note": (
                f"The model applies one flat {KM_MODEL:,} km a year to every market. Measured "
                "distance tracks truck weight class, a 3.7x spread. Every gap on this page moves "
                "with that assumption."),
        },
        "gap_vintage": (
            "Substitution, under-service and catalogue-gap typing is modelled for CY2026 only. "
            "There is no history for it, so it cannot be trended."),
        "mix_decomposition_gap": mix_dead,
        "mix_note": (
            "The revenue change is split into volume and price. A mix leg exists as a column but "
            "is zero on every row of the source, so no mix effect is reported."),
        "dealer_coverage": dealer_cov,
        "dealer_markets": with_detail,
        "uio_note": (
            f"Fleet denominator is vehicles in service: {scope['fleet_uio']:,} across the scored "
            "markets. A unit count without that base cannot be judged."
        ) if scope["fleet_uio"] else None,
        "gps_denominator_note": (
            "Target spend is shown against its ceiling, which is spend per vehicle in service. A "
            "second internal benchmark compares spend against an upper reference per market; the "
            "two give different percentages for the same market, so each is labelled where it "
            "appears and they are never mixed on one figure."),
        "peer_rule": (
            f"Benchmarks are an unlabelled median across comparable markets, always the same "
            f"customer type. A group with fewer than {PEER_MIN_MEMBERS} members is suppressed "
            "rather than averaged."),
        "peer_min_members": PEER_MIN_MEMBERS,
        "sources_note": (
            "Every figure is re-derived from the approved derived layer on the build date. "
            "Nothing is copied from a previous pack."),
    }


# ------------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="print sanity numbers and exit")
    args = ap.parse_args()

    print("verification report ...", flush=True)
    verification = load_verification()
    if not verification["ok"]:
        raise SystemExit(
            f"FATAL: _verification_report.json is not green "
            f"(pass={verification['pass']} warn={verification['warn']} fail={verification['fail']}). "
            "Rebuild the pipeline before trusting any number on this page."
        )
    print(f"  green: {verification['pass']} pass / {verification['warn']} warn / {verification['fail']} fail")

    dbs, network = load_dimension()
    print(f"  dimension: {len(network)} network distributors")

    print("modules ...", flush=True)
    modules = {
        "evolution": mod_evolution(dbs),
        "dynamics": mod_dynamics(dbs),
        "gps": mod_gps(dbs),
        "pms": mod_pms(dbs),
        "mix": mod_mix(dbs),
        "aim": mod_aim(dbs),
        "subgroup": mod_subgroup(dbs),
        "unbilled": mod_unbilled(dbs),
        "actions": mod_actions(dbs),
        "league": mod_league(dbs),
        "honesty": mod_honesty(dbs, verification),
    }
    for k, v in modules.items():
        print(f"  {k:10s} {len(v.get('rows', [])):3d} distributor rows")

    peer_groups = build_peer_groups(dbs)
    payload = {
        "meta": {
            "generated": datetime.now().isoformat(timespec="seconds"),
            "as_of": date.today().isoformat(),
            "verification": verification,
            "n_network_dbs": len(network),
            "years": YEARS,
            "current_year": CURRENT_YEAR,
            "ytd_note": YTD_NOTE,
            "peer_min_members": PEER_MIN_MEMBERS,
            "layer_labels": LAYER_LABEL,
            "network": {"uio_2025": i(_sum(d.get("uio_2025") for d in dbs.values()))},
            # Four different percentages in this workspace have all been called a GPS capture
            # percentage. Naming them here so the verifier can catch the wrong one being
            # quoted. Only the first is used by this tool.
            "legacy_bands": {
                "gps_pct_CEILING": "Capture against the modelled spend ceiling. Used by this tool.",
                "gps_pct_UPPER_REF": "Capture against an upper reference spend per market. A different denominator.",
                "capture_total_apps": "Share of expected service demand captured, including competing-brand parts.",
                "capture_genuine_apps": "Share of expected service demand captured on own-brand parts only.",
                "capture_total_legacy_UNRELIABLE": "Older capture percentage withdrawn at the 2026-06 integration. Do not quote.",
            },
            "sources": [
                "01_data/00_derived/_verification_report.json",
                "01_data/00_derived/distributor_dimension.csv",
                "01_data/00_derived/wallet_waterfall.csv",
                "01_data/00_derived/revenue_runway.csv",
                "01_data/00_derived/revenue_waterfall.csv",
                "01_data/00_derived/gps_spu_by_distributor.csv",
                "01_data/00_derived/pms_capture_by_db_year.csv",
                "01_data/00_derived/capture_trajectory.csv",
                "01_data/00_derived/pms_opportunity_matrix.csv",
                "01_data/00_derived/capture_recovery_model.csv",
                "01_data/00_derived/mix_genuine_bvp_pms.csv",
                "01_data/00_derived/db_parts_mix_classification.csv",
                "01_data/00_derived/aim_exposure_by_db_year.csv",
                "01_data/00_derived/aim_bvp_family_risk.csv",
                "01_data/00_derived/substitution_by_db_year.csv",
                "01_data/00_derived/sellout_aim_by_aim_l1_2025.csv",
                "01_data/00_derived/network_percentile.csv",
                "01_data/00_derived/db_aftersales_risk.csv",
                "01_data/00_derived/early_warning.csv",
                "01_data/00_derived/defection_alerts.csv",
                "01_data/17_interactions/account_health_latest_flagged.csv",
            ],
            "dealer_sources": [os.path.basename(p) for p in DEALER_LONG],
        },
        "dbs": dbs,
        "network_dbs": network,
        "peer_groups": peer_groups,
        "modules": modules,
    }

    if args.check:
        print()
        ev = modules["evolution"]
        ac = modules["actions"]
        print(f"billing window: {ev['billing_first']} -> {ev['billing_last']} "
              f"({ev['month_count']} months)")
        print(f"network parts, same six months of {CURRENT_YEAR}: "
              f"EUR {(ev['network_ytd_eur'] or 0)/1e6:.2f}M")
        c = modules["gps"]["ceiling"]
        print(f"ceiling CY2025: EUR {(c['ceiling_total_eur'] or 0)/1e6:.2f}M  "
              f"flat-{PLACEHOLDER_SPU_EUR:.0f} {c['flat_n']}/{c['n_markets']} "
              f"lock {c['flat_share_ceiling_pct']}%")
        h = modules["honesty"]
        sc = h["scope"]
        print(f"dealer detail markets: {sc['dealer_detail_n']} -> {h['dealer_markets']}")
        print(f"over-100 capture cells: {sc['over_100']}/{sc['captured_cells']} "
              f"= {sc['over_100_share_pct']}%")
        print(f"mix leg dead: {h['mix_decomposition_gap']}")
        print(f"scored markets: {sc['scored_markets_n']}/{sc['network_markets_n']}")
        print()
        print("like-for-like growth on the six-month window, all markets:")
        for r in sorted(ev["rows"], key=lambda x: -(x["metric_growth_pct"] or -999)):
            g = r["metric_growth_pct"]
            a = r["metric_avg_month_eur"]
            gs = "n/a" if g is None else f"{g:+7.1f}%"
            as_ = "n/a" if a is None else f"EUR {a:,.0f}"
            print(f"  {r['db']:12s} {gs}   avg month {as_}")
        print()
        print("part-number conclusions raised, per market:")
        tot = 0.0
        for r in sorted(ac["rows"], key=lambda x: -(x["metric_eur_at_stake"] or 0)):
            v = r["metric_eur_at_stake"] or 0
            tot += v
            if v:
                print(f"  {r['db']:12s} {r['n_lines']:6d} lines  {r['n_named']:5d} named  "
                      f"EUR {v:,.0f}")
        print(f"  {'TOTAL':12s} EUR {tot:,.0f}")
        return 0

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))
    kb = os.path.getsize(OUT) / 1024
    print(f"\n  -> {OUT} ({kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
