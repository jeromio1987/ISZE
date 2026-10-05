"""Build the commercial warranty datasets and workbook.

One place, one run. Everything here is derived from two sources and nothing is typed by hand.

Sources (read-only):
  01_data/00_derived/warranty_fy26_raw.csv     LCV / D-Max claim export, AssessMonth 202504-202603
  01_data/06_Warranty/*.xlsx                   CV truck claim sheets (5 claim-level sheets)

Outputs, all under 01_data/00_derived/warranty_commercial/:
  *.csv                                        the datasets, one file per commercial question,
                                               every market inside the file (general, not per market)
  Warranty_Commercial_Datasets_2026-09-18.xlsx the same tables as sheets
  README.md                                    what each file is, and the limits that travel with it

Currency: the D-Max export is one IMG European export, not one currency, so JPY are converted at a
flat 163.7. Absolute euros for a non-EUR market carry a few percent of noise; shares and medians do
not. `warranty_fy26_raw.csv` is left untouched.

Run:  python 01_data/91_build/build_warranty_commercial_datasets.py
"""
from __future__ import annotations

import sys
import warnings
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
WARRANTY_XLSX = ROOT / "01_data" / "06_Warranty"
LCV_RAW = ROOT / "01_data" / "00_derived" / "warranty_fy26_raw.csv"
OUT = ROOT / "01_data" / "00_derived" / "warranty_commercial"
JPY = 163.7          # workspace standard, matches build_warranty_canonical.py
GBP_TO_EUR = 1.12    # stated assumption — the CV file carries no GBP/EUR rate of its own
AS_OF = date(2026, 9, 18)

# Commercial layer: the wallet and billing files are a calendar year, the claim file is a 28-month
# window. Ratios must be taken on claims of the SAME year, or they are overstated by ~2.3x.
COMMERCIAL_YEAR = 2025

# Claim-file market names -> workspace distributor codes. MIDI-group markets bill under one code
# and MIDI is not in the GPS base (dropped as a non-customer in 2026-07-02), so they are excluded
# from the ratio table rather than given a fabricated denominator.
CV_MARKET_TO_DB = {
    "UK": "ITUK", "ISRAEL": "UTI", "PORTUGAL": "PORTUGAL", "HUNGARY": "HUNGARY",
    "IRELAND": "IRELAND", "ROMANIA": "ROMANIA", "CYPRUS": "CYPRUS", "MALTA": "MALTA",
    "GREECE": "GREECE",
}

# ─── CV currency, and why this is not a detail ────────────────────────────────
# The CV claim file's `CRNCY` column holds TWO tokens, not one:
#     "EUR EUR"  -> the amount is in EUR   (Israel, Portugal, Ireland, Germany, Cyprus, Malta, Greece)
#     "EUR GBP"  -> the amount is in GBP   (UK — 11,956 lines, the largest book in the file)
#     "JPY EUR"  -> the amount is in JPY   (Italy, Spain, France, Switzerland and the rest)
# Verified two ways: the string itself, and the file's own `JPY_PARTSTTL / PARTAMT1` ratio, which
# is ~1.00 on the JPY-flagged rows and ~170 on the EUR-flagged ones.
#
# Summing PARTAMT1 raw mixes EUR, GBP and JPY into one number and is meaningless. An earlier pass
# did exactly that and produced a €93.8m Italian figure that was really ¥93.8m. Normalise first.
CV_CRNCY_MAP = {
    "EUR EUR": ("EUR", 1.0),
    "EUR GBP": ("GBP", GBP_TO_EUR),
    "JPY EUR": ("JPY", 1.0 / JPY),
}

# The file's own internal JPY conversion is ~170.4, not 163.7, so JPY-market euros computed here
# run about 4% above what the file's own arithmetic would give. Kept at 163.7 for consistency with
# the rest of the workspace; the direction of the difference is stated in the README.


# The warranty limits used to split cost into "Isuzu pays" and "goodwill". These are the stated
# terms, not a measurement.
LIMIT_MONTHS = 36
LIMIT_KM = 100_000

# ---------------------------------------------------------------- component families
# Ordered so the most specific pattern wins; reversed when applied.
FAMILIES: list[tuple[str, str]] = [
    ("Emissions aftertreatment", r"DPF|PARTICULATE|UREA|DEF |NOX|SCR|CATALYST|EGR"),
    ("Steering", r"POWER STEERING|STEERING"),
    ("Powertrain (engine/turbo/injection)", r"ENGINE|TURBO|INJECTOR|FUEL INJECTION|CYLINDER HEAD|BLOCK"),
    ("Cooling", r"RADIATOR|COOLANT|INTERCOOL|THERMOSTAT|WATER PUMP"),
    ("Electrical & electronics", r"WIRING|SENSOR|CONTROL UNIT|CONTROLLER|CAMERA|RADAR|RELAY|ALTERNATOR|STARTER"),
    ("Transmission & driveline", r"TRANSMISSION|CLUTCH|TRANSFER|PROPELLER|DIFFERENTIAL|AXLE"),
    ("Brakes", r"BRAKE|PAD|ROTOR|DISC|CALIPER|SHOE|ABS"),
    ("Suspension & linkage", r"SUSPENSION|SPRING|SHOCK|DAMPER|BUSHING|BALL JOINT|LINK"),
    ("Body, cab & interior", r"SEAT|SUNSHADE|MIRROR|DOOR|WINDOW|GLASS|WIPER|BUMPER|GRILLE"),
    ("Cabin comfort & infotainment", r"RADIO|AUDIO|DISPLAY|AIR CON|A/C|HEATER|BLOWER|COMPRESSOR"),
    ("Filters & service items", r"FILTER|OIL|BELT|BATTERY|LUBRIC"),
]


def family_of(text: pd.Series) -> pd.Series:
    out = pd.Series("Other / not classified", index=text.index)
    for label, pattern in reversed(FAMILIES):
        out[text.str.contains(pattern, na=False, regex=True)] = label
    return out


def clean_op(s: pd.Series) -> pd.Series:
    return (s.astype(str).str.strip().str.upper()
            .str.replace(r"\s+", " ", regex=True)
            .replace({"NAN": "(not recorded)"}))


# ------------------------------------------------------------------------- load LCV
def load_lcv() -> pd.DataFrame:
    d = pd.read_csv(LCV_RAW, low_memory=False)
    d["parts_eur"] = np.where(d.CurrencyParts.eq("JPY"), d.PartClaimAmt / JPY, d.PartClaimAmt)
    d["parts_admitted_eur"] = np.where(d.CurrencyParts.eq("JPY"), d.PartAdmitAmt / JPY, d.PartAdmitAmt)
    d["operation"] = clean_op(d.OperationDescription)
    d["family"] = family_of(d.operation)
    d["odometer_km"] = pd.to_numeric(d.Mileage, errors="coerce")
    d["retail_date"] = pd.to_datetime(d.RetailDate, errors="coerce")
    d["repair_date"] = pd.to_datetime(d.RODate, errors="coerce")
    d["age_years"] = ((d.repair_date - d.retail_date).dt.days / 365.25).round(2)
    d["market"] = d.DistributorName.astype(str).str.strip()
    d["part_number"] = d.PartsNo.astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    d["vin"] = d.Vinno.astype(str).str.strip().str.upper()
    has_pn = d.part_number.str.len() >= 8
    d["has_part_number"] = has_pn

    # lines with a real parts charge: a labour-only or reprogramming row is not a parts claim
    d["billable"] = d.parts_eur > 5
    d["position"] = np.select(
        [
            (d.odometer_km < LIMIT_KM) & (d.age_years < LIMIT_MONTHS / 12),
            d.odometer_km >= LIMIT_KM,
            d.age_years >= LIMIT_MONTHS / 12,
        ],
        ["inside both limits", "over distance limit", "over age limit"],
        default="unknown",
    )
    return d


# -------------------------------------------------------------------------- load CV
def load_cv() -> pd.DataFrame:
    frames = []
    for fname, sheet in [
        ("Warranty_CV_2025.xlsx", "Sheet1"),
        ("Warranty_CV_2025.xlsx", "DATA WITHOUT MIDI"),
        ("CV Warranty.xlsx", "10_25-12_2025"),
        ("CV Warranty.xlsx", "2024"),
        ("CV warranty01_03_2026.xlsx", "Sheet1"),
    ]:
        d = pd.read_excel(WARRANTY_XLSX / fname, sheet_name=sheet)
        d.columns = [str(c).strip().upper() for c in d.columns]
        frames.append(d)
    cv = pd.concat(frames, ignore_index=True)
    cv = cv.drop_duplicates(subset=["VIN17", "BILLYMD", "PARTNBR", "DOCNBR"])
    cv["operation"] = clean_op(cv.OPE_NAME)
    cv["family"] = family_of(cv.operation)
    cv["odometer_km"] = pd.to_numeric(cv.MILE, errors="coerce")
    cv["labour_eur"] = pd.to_numeric(cv.LBRAMT, errors="coerce").fillna(0)

    # currency: normalise BEFORE any euro total is taken. See CV_CRNCY_MAP above.
    crncy_raw = cv.CRNCY.astype(str).str.strip().str.upper()
    cv["currency"] = crncy_raw.map(lambda v: CV_CRNCY_MAP.get(v, ("UNKNOWN", np.nan))[0])
    cv["fx_to_eur"] = crncy_raw.map(lambda v: CV_CRNCY_MAP.get(v, ("UNKNOWN", np.nan))[1])
    cv["parts_local"] = pd.to_numeric(cv.PARTAMT1, errors="coerce")
    cv["parts_eur"] = cv.parts_local * cv.fx_to_eur
    cv["parts_jpy_equivalent"] = pd.to_numeric(cv.JPY_PARTSTTL, errors="coerce")
    unmapped = cv.currency.eq("UNKNOWN")
    if unmapped.any():
        print(f"  WARNING: {int(unmapped.sum())} CV lines carry an unrecognised CRNCY token and are "
              f"excluded from every euro total: {sorted(cv.loc[unmapped, 'CRNCY'].astype(str).unique())}")

    cv["retail_date"] = pd.to_datetime(
        cv.RETA6.astype(str).str.replace(r"\.0$", "", regex=True).str.strip(),
        format="%Y%m", errors="coerce")
    cv["claim_date"] = pd.to_datetime(cv.BILLYMD.astype(str).str.strip(), format="%Y%m%d",
                                      errors="coerce")
    cv["age_years"] = ((cv.claim_date - cv.retail_date).dt.days / 365.25).round(2)
    cv["market"] = cv.CTY_NAME.astype(str).str.strip().str.upper()
    cv["dealer_code"] = cv.DLR.astype(str).str.strip().str.upper()
    cv["failure_code"] = cv.TR_CD.astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    cv["part_number"] = cv.PARTNBR.astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    cv["vin"] = cv.VIN17.astype(str).str.strip().str.upper()
    cv["has_part_number"] = cv.part_number.str.len() >= 8
    cv["module"] = "CV truck"
    cv["position"] = np.select(
        [
            (cv.odometer_km < LIMIT_KM) & (cv.age_years < LIMIT_MONTHS / 12),
            cv.odometer_km >= LIMIT_KM,
            cv.age_years >= LIMIT_MONTHS / 12,
        ],
        ["inside both limits", "over distance limit", "over age limit"],
        default="unknown",
    )
    return cv


# ------------------------------------------------------------------------ build: LCV
def lcv_datasets(d: pd.DataFrame) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    bill = d[d.billable & d.has_part_number].copy()
    total = bill.parts_eur.sum()

    # 1. cost by component family
    fam = bill.groupby("family").agg(
        claim_lines=("parts_eur", "size"),
        parts_turnover_eur=("parts_eur", "sum"),
        part_numbers=("part_number", "nunique"),
        median_odometer_km=("odometer_km", "median"),
        median_age_years=("age_years", "median"),
    )
    inside = bill[bill.position == "inside both limits"].groupby("family").parts_eur.sum()
    outside = bill[bill.position.isin(["over distance limit", "over age limit"])].groupby("family").parts_eur.sum()
    fam["inside_limits_eur"] = inside
    fam["outside_limits_eur"] = outside
    fam = fam.fillna(0)
    fam["outside_limits_share"] = (fam.outside_limits_eur / fam.parts_turnover_eur).round(3)
    fam["share_of_parts_turnover"] = (fam.parts_turnover_eur / total).round(4)
    out["warranty_cost_by_component_family.csv"] = fam.sort_values(
        "parts_turnover_eur", ascending=False).round(2).reset_index()

    # 2. cost by position against the limits
    pos = bill.groupby("position").agg(
        claim_lines=("parts_eur", "size"),
        parts_turnover_eur=("parts_eur", "sum"),
    )
    pos["share_of_parts_turnover"] = (pos.parts_turnover_eur / pos.parts_turnover_eur.sum()).round(4)
    pos["parts_turnover_per_line_eur"] = (pos.parts_turnover_eur / pos.claim_lines).round(0)
    out["warranty_cost_by_limit_position.csv"] = pos.sort_values(
        "parts_turnover_eur", ascending=False).round(2).reset_index()

    # 3. cost by market, with the settlement ratio
    mk = d.groupby("market").agg(
        claim_lines=("parts_eur", "size"),
        parts_claimed_eur=("parts_eur", "sum"),
        parts_admitted_eur=("parts_admitted_eur", "sum"),
        lines_with_part_number=("has_part_number", "sum"),
        median_odometer_km=("odometer_km", "median"),
    )
    inside_m = bill[bill.position == "inside both limits"].groupby("market").parts_eur.sum()
    outside_m = bill[bill.position.isin(["over distance limit", "over age limit"])].groupby("market").parts_eur.sum()
    mk["inside_limits_eur"] = inside_m
    mk["outside_limits_eur"] = outside_m
    mk = mk.fillna(0)
    mk["outside_limits_share"] = np.where(
        (mk.inside_limits_eur + mk.outside_limits_eur) > 0,
        (mk.outside_limits_eur / (mk.inside_limits_eur + mk.outside_limits_eur)).round(3), np.nan)
    mk["over_age_eur"] = bill[bill.position == "over age limit"].groupby("market").parts_eur.sum()
    mk["over_distance_eur"] = bill[bill.position == "over distance limit"].groupby("market").parts_eur.sum()
    mk = mk.fillna(0)
    mk["admitted_vs_claimed_ratio"] = (mk.parts_admitted_eur / mk.parts_claimed_eur).round(3)
    mk["part_number_coverage"] = (mk.lines_with_part_number / mk.claim_lines).round(3)
    out["warranty_cost_by_market.csv"] = mk.sort_values(
        "parts_claimed_eur", ascending=False).round(2).reset_index()

    # 4. the most expensive repair lines
    top = d[d.billable].groupby("operation").agg(
        claim_lines=("parts_eur", "size"),
        parts_turnover_eur=("parts_eur", "sum"),
        parts_admitted_eur=("parts_admitted_eur", "sum"),
        median_odometer_km=("odometer_km", "median"),
        median_age_years=("age_years", "median"),
        markets_present=("market", "nunique"),
        family=("family", "first"),
    )
    top["parts_turnover_per_line_eur"] = (top.parts_turnover_eur / top.claim_lines).round(0)
    top["inside_limits_eur"] = bill[bill.position == "inside both limits"].groupby("operation").parts_eur.sum()
    top["outside_limits_eur"] = bill[bill.position.isin(
        ["over distance limit", "over age limit"])].groupby("operation").parts_eur.sum()
    top = top.fillna(0)
    top["outside_limits_share"] = np.where(
        top.parts_turnover_eur > 0,
        (top.outside_limits_eur / top.parts_turnover_eur).round(3), np.nan)
    out["warranty_top_repair_lines.csv"] = top.sort_values(
        "parts_turnover_eur", ascending=False).head(150).round(2).reset_index()

    # 5. part-number turnover
    pn = bill.groupby("part_number").agg(
        claim_lines=("parts_eur", "size"),
        parts_turnover_eur=("parts_eur", "sum"),
        markets_present=("market", "nunique"),
        median_odometer_km=("odometer_km", "median"),
        median_age_years=("age_years", "median"),
        family=("family", "first"),
    )
    pn["parts_turnover_per_line_eur"] = (pn.parts_turnover_eur / pn.claim_lines).round(0)
    pn = pn.sort_values("parts_turnover_eur", ascending=False)
    pn["cumulative_share_of_turnover"] = (pn.parts_turnover_eur.cumsum() / pn.parts_turnover_eur.sum()).round(4)
    out["warranty_part_turnover.csv"] = pn.round(2).reset_index()

    # 6. repeat repairs: the same operation on the same vehicle more than once
    rep = (d[d.billable].groupby(["vin", "operation"])
           .agg(times=("parts_eur", "size"), parts_turnover_eur=("parts_eur", "sum"),
                market=("market", "first"), family=("family", "first"),
                median_odometer_km=("odometer_km", "median")))
    rep = rep[rep.times > 1]
    out["warranty_repeat_repairs.csv"] = (rep.sort_values("parts_turnover_eur", ascending=False)
                                          .round(2).reset_index())
    return out


# ------------------------------------------------------------------------- build: CV
def cv_datasets(cv: pd.DataFrame) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    with_pn = cv[cv.has_part_number].copy()
    total = with_pn.parts_eur.sum()

    # 7. truck parts turnover by market, carrying its own coverage caveat as a column
    mk = cv.groupby("market").agg(
        claim_lines=("parts_eur", "size"),
        parts_turnover_eur=("parts_eur", "sum"),
        labour_eur=("labour_eur", "sum"),
        lines_with_part_number=("has_part_number", "sum"),
        median_odometer_km=("odometer_km", "median"),
        median_age_years=("age_years", "median"),
        vehicles=("vin", "nunique"),
        currency=("currency", "first"),
    )
    mk["part_number_coverage"] = (mk.lines_with_part_number / mk.claim_lines).round(3)
    mk["parts_turnover_per_line_eur"] = (mk.parts_turnover_eur / mk.claim_lines).round(0)
    out["warranty_cv_by_market.csv"] = mk.sort_values("claim_lines", ascending=False).round(2).reset_index()

    # 8. truck parts turnover by component family (emissions dominates)
    fam = with_pn.groupby("family").agg(
        claim_lines=("parts_eur", "size"),
        parts_turnover_eur=("parts_eur", "sum"),
        part_numbers=("part_number", "nunique"),
        median_odometer_km=("odometer_km", "median"),
    )
    fam["share_of_parts_turnover"] = (fam.parts_turnover_eur / total).round(4)
    out["warranty_cv_by_component_family.csv"] = fam.sort_values(
        "parts_turnover_eur", ascending=False).round(2).reset_index()

    # 9. truck part-number turnover
    pn = with_pn.groupby("part_number").agg(
        claim_lines=("parts_eur", "size"),
        parts_turnover_eur=("parts_eur", "sum"),
        markets_present=("market", "nunique"),
        median_odometer_km=("odometer_km", "median"),
        family=("family", "first"),
    )
    pn["parts_turnover_per_line_eur"] = (pn.parts_turnover_eur / pn.claim_lines).round(0)
    pn = pn.sort_values("parts_turnover_eur", ascending=False)
    pn["cumulative_share_of_turnover"] = (pn.parts_turnover_eur.cumsum() / pn.parts_turnover_eur.sum()).round(4)
    out["warranty_cv_part_turnover.csv"] = pn.round(2).reset_index()

    # 9b. truck repairs by operation — the truck counterpart of warranty_top_repair_lines.csv.
    #     This was missing from the first build, and its absence is why a wrong truck figure for the
    #     power steering gear survived two passes: there was no truck table to compare against.
    ops = cv[cv.parts_eur > 0].groupby("operation").agg(
        claim_lines=("parts_eur", "size"),
        parts_turnover_eur=("parts_eur", "sum"),
        labour_eur=("labour_eur", "sum"),
        median_odometer_km=("odometer_km", "median"),
        median_age_years=("age_years", "median"),
        markets_present=("market", "nunique"),
        family=("family", "first"),
    )
    ops["parts_turnover_per_line_eur"] = (ops.parts_turnover_eur / ops.claim_lines).round(0)
    out["warranty_cv_top_repair_lines.csv"] = ops.sort_values(
        "parts_turnover_eur", ascending=False).head(100).round(2).reset_index()

    # 10. dealer concentration
    dl = cv.groupby(["dealer_code", "market", "currency"]).agg(
        claim_lines=("parts_eur", "size"),
        parts_turnover_eur=("parts_eur", "sum"),
        vehicles=("vin", "nunique"),
        median_odometer_km=("odometer_km", "median"),
    )
    dl["share_of_claim_lines"] = (dl.claim_lines / dl.claim_lines.sum()).round(4)
    out["warranty_cv_dealer_concentration.csv"] = dl.sort_values(
        "claim_lines", ascending=False).round(2).reset_index()

    # 11. failure-code profile
    fc = cv.groupby("failure_code").agg(
        claim_lines=("parts_eur", "size"),
        lines_with_part_number=("has_part_number", "sum"),
        parts_turnover_eur=("parts_eur", "sum"),
        labour_eur=("labour_eur", "sum"),
        median_odometer_km=("odometer_km", "median"),
    )
    fc["part_number_coverage"] = (fc.lines_with_part_number / fc.claim_lines).round(3)
    fc["is_administrative"] = fc.part_number_coverage < 0.1
    out["warranty_cv_failure_code_profile.csv"] = fc.sort_values(
        "claim_lines", ascending=False).round(2).reset_index()

    # 12. what each money column does and does not mean — the audit trail for the euro figures
    fx = cv[cv.parts_eur.notna()].groupby(["currency", "market"]).agg(
        claim_lines=("parts_eur", "size"),
        parts_local=("parts_local", "sum"),
        parts_eur=("parts_eur", "sum"),
        parts_jpy_equivalent=("parts_jpy_equivalent", "sum"),
    )
    fx["fx_to_eur"] = fx.index.get_level_values("currency").map(
        {"EUR": 1.0, "GBP": GBP_TO_EUR, "JPY": 1.0 / JPY})
    fx = fx.reset_index()
    out["warranty_cv_currency_audit.csv"] = fx.sort_values("parts_eur", ascending=False).round(2)

    # 13. THE COMMERCIAL LAYER. Warranty cost against the business, not just counted.
    #     Period alignment is mandatory here: the claim file spans 28 months while the wallet and
    #     billing files are one calendar year. Comparing them whole inflated every ratio ~2.3x
    #     before this filter existed. Always filter claims to the wallet's own year first.
    wallet = pd.read_csv(ROOT / "01_data" / "00_derived" / "wallet_waterfall.csv",
                         encoding="utf-8-sig")
    wallet = wallet[wallet.year == COMMERCIAL_YEAR][
        ["distributor_code", "theoretical_wallet_eur", "captured_total_eur", "uio_units", "gps_pct"]]
    cy = cv[cv.claim_date.dt.year == COMMERCIAL_YEAR]
    rows = []
    for market, code in CV_MARKET_TO_DB.items():
        sub = cy[cy.market == market]
        ww = wallet[wallet.distributor_code == code]
        if sub.empty or ww.empty:
            continue
        r = ww.iloc[0]
        rows.append({
            "market": market,
            "distributor_code": code,
            "claim_lines": len(sub),
            "warranty_parts_eur": sub.parts_eur.sum(),
            "target_wallet_eur": r.theoretical_wallet_eur,
            "parts_billed_eur": r.captured_total_eur,
            "uio_units": r.uio_units,
            "warranty_eur_per_uio": sub.parts_eur.sum() / r.uio_units,
            "warranty_pct_of_target_wallet": sub.parts_eur.sum() / r.theoretical_wallet_eur * 100,
            "warranty_pct_of_parts_billed": sub.parts_eur.sum() / r.captured_total_eur * 100,
            "gps_pct": r.gps_pct,
        })
    out["warranty_cv_commercial_by_market.csv"] = (
        pd.DataFrame(rows).sort_values("warranty_eur_per_uio", ascending=False).round(2))

    # 14. who pays for the failure, decided by where it fails
    ops = out["warranty_cv_top_repair_lines.csv"]
    ops = ops[ops.claim_lines >= 45].copy()
    ops["who_pays"] = np.select(
        [
            ops.median_odometer_km < 60_000,
            ops.median_odometer_km < 140_000,
        ],
        ["Isuzu — fails well inside warranty",
         "boundary — price-list and campaign question"],
        default="distributor — outside warranty, aftermarket demand",
    )
    keep = ["operation", "family", "claim_lines", "parts_turnover_eur", "parts_turnover_per_line_eur",
            "median_odometer_km", "median_age_years", "markets_present", "who_pays"]
    out["warranty_operations_by_who_pays.csv"] = (
        ops[[c for c in keep if c in ops.columns]]
        .sort_values(["who_pays", "parts_turnover_eur"], ascending=[True, False]).round(2))
    return out


# -------------------------------------------------------------------------- write
def write_csvs(tables: dict[str, pd.DataFrame]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        path = OUT / name
        table.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"  {name:46s} {len(table):6,d} rows")


def write_workbook(tables: dict[str, pd.DataFrame]) -> Path:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    wb.remove(wb.active)
    navy = PatternFill("solid", fgColor="15233C")
    head_font = Font(color="F7F4EE", bold=True, size=10)

    for name, table in tables.items():
        sheet = name.replace(".csv", "")[:31]
        ws = wb.create_sheet(sheet)
        ws.append(list(table.columns))
        for cell in ws[1]:
            cell.fill = navy
            cell.font = head_font
            cell.alignment = Alignment(vertical="center", wrap_text=True)
        for row in table.itertuples(index=False):
            ws.append([None if (isinstance(v, float) and np.isnan(v)) else v for v in row])
        ws.freeze_panes = "A2"
        # Widths. The pre-delivery check requires column B (the description column) to be at least
        # 28 wide and any column headed "name"/"dealer" to be at least 12, so those floors are
        # applied to every sheet rather than only where the data happens to be long.
        MIN_B, MIN_TEXT, MIN_NUM, MAX_W = 28.0, 12.0, 16.0, 46.0
        for i, col in enumerate(table.columns, start=1):
            longest = int(table[col].astype(str).str.len().max() or 8)
            floor = MIN_B if i == 2 else MIN_NUM
            if table[col].dtype == object or "dealer" in str(col).lower() or "name" in str(col).lower():
                floor = max(floor, MIN_TEXT)
            ws.column_dimensions[get_column_letter(i)].width = min(max(floor, longest + 2), MAX_W)
        # wrap the long text columns so nothing clips
        for i, col in enumerate(table.columns, start=1):
            if table[col].dtype == object and table[col].astype(str).str.len().max() > 24:
                for cell in ws[get_column_letter(i)][1:]:
                    cell.alignment = Alignment(wrap_text=True, vertical="top")
    path = OUT / f"Warranty_Commercial_Datasets_{AS_OF.isoformat()}.xlsx"
    wb.save(path)
    return path


def main() -> None:
    print("loading sources")
    lcv = load_lcv()
    cv = load_cv()
    print(f"  LCV claim lines {len(lcv):,} | CV claim lines {len(cv):,} (de-duplicated)")

    tables = {}
    tables.update(lcv_datasets(lcv))
    tables.update(cv_datasets(cv))

    print("writing CSV datasets")
    write_csvs(tables)
    wb = write_workbook(tables)
    print(f"  workbook {wb.name} ({wb.stat().st_size / 1024:,.0f} KB)")
    print("done")


def reconciliation(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Headline totals, so the file carries its own check rather than asking the reader to add up.

    Every euro here is normalised: CV at its own currency (EUR / GBP x1.12 / JPY /163.7), LCV at the
    export's per-line currency (EUR / JPY / 163.7).
    """
    rows = []
    lcv_market = tables["warranty_cost_by_market.csv"]
    cv_market = tables["warranty_cv_by_market.csv"]
    lcv_pos = tables["warranty_cost_by_limit_position.csv"]
    rows += [
        ("LCV (D-Max) claim lines", float(lcv_market.claim_lines.sum())),
        ("LCV (D-Max) parts claimed EUR", float(lcv_market.parts_claimed_eur.sum())),
        ("LCV (D-Max) parts admitted EUR", float(lcv_market.parts_admitted_eur.sum())),
        ("CV (truck) claim lines", float(cv_market.claim_lines.sum())),
        ("CV (truck) parts turnover EUR", float(cv_market.parts_turnover_eur.sum())),
        ("CV (truck) labour EUR (recording differs by market)", float(cv_market.labour_eur.sum())),
        ("LCV share of parts turnover outside the 3yr/100,000km limits",
         float(lcv_pos.loc[lcv_pos.position.isin(["over age limit", "over distance limit"]),
                           "share_of_parts_turnover"].sum())),
    ]
    return pd.DataFrame(rows, columns=["measure", "value"])


def main() -> None:
    print("loading sources")
    lcv = load_lcv()
    cv = load_cv()
    print(f"  LCV claim lines {len(lcv):,} | CV claim lines {len(cv):,} (de-duplicated)")

    tables = {}
    tables.update(lcv_datasets(lcv))
    tables.update(cv_datasets(cv))
    recon = reconciliation(tables)
    tables["warranty_commercial_reconciliation.csv"] = recon

    print("writing CSV datasets")
    write_csvs(tables)
    wb = write_workbook(tables)
    print(f"  workbook {wb.name} ({wb.stat().st_size / 1024:,.0f} KB)")
    print()
    print(recon.to_string(index=False))
    print("done")


if __name__ == "__main__":
    main()
