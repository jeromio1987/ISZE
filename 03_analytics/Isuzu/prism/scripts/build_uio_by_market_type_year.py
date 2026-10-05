#!/usr/bin/env python3
"""
Publish the vehicle-in-service workbook's own year axis as a derived file.

WHY THIS EXISTS
---------------
`uio_by_model_bucket.csv` is a single column labelled 2025E, so every "euro per vehicle"
figure built from it is the raw euro move wearing a rate. Dividing one year's fleet into
three different years' billing cannot change a percentage: it is arithmetically the same
as dividing by 1. The workbook behind that file (`06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx`,
sheet `1.UIO Overview`) has carried one row per market x vehicle class x model type for
every year from 1990 to 2030 all along; only the derived file threw the year axis away.

WHAT THIS WRITES
----------------
`01_data/00_derived/uio_by_market_type_year.csv`
    distributor_code, market, vehicle_class, model_type, year, uio_units,
    is_actual, is_estimate, is_forecast, basis, source_note, band_note

  * 1990-2024 = actuals, 2025 = estimate, 2026-2030 = forecast. All three are flagged
    per row and the forecast rows are named as forecast, never presented as measured.
  * Distributor codes come from the SAME mapping the model bucket file uses (imported
    from `build_uio_by_model_bucket`), so the two files cannot drift apart.

TWO KNOWN DEFECTS ARE CARRIED, NOT HIDDEN
-----------------------------------------
  * LD-LABEL: the workbook's `LD` label is not a weight class. In Israel it is the whole
    N-series fleet at 6.5/7.5 t (the ministry band table starts at 6.5-7.5 t and the CV
    warranty VIN register holds no NLR at all); in most of Europe the same label mostly
    means 3.5 t, which is a different parts wallet. `band_note` says so per market and the
    target rate is NOT re-derived here - the per-market 3.5 t share lives in
    `uio_ld_n35_share.csv` and is applied by the spend model, not by this file.
  * UIO-FCAST: Israel (UTI) CV rows are ~25% LOW in every year against the Israeli
    ministry's own registrations, so any per-truck figure on UTI is flattered by an
    understated denominator. Every UTI CV row carries that in `fleet_quality_note`.
    The 2026-2030 forecast columns are separately overstated (+9% in 2026 to +59% by
    2030 on the grand total; far worse per market), so they are flagged forecast and
    nothing forward-looking should be divided by them without saying so.

The read-only rule: the workbook is opened read-only and is never written to.

Usage:
    python 03_analytics/Isuzu/prism/scripts/build_uio_by_market_type_year.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import openpyxl
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PRISM_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(PRISM_ROOT))

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from config import DERIVED_DIR, resolve_uio_path  # noqa: E402
from build_uio_by_model_bucket import (  # noqa: E402
    DIRECT_DISTRIBUTOR_COUNTRIES,
    EXCLUDED_DISTRIBUTOR_CODES,
    EXTRA_DIRECT_COUNTRY_CODES,
    _country_to_distributor_map,
)

OUTPUT_CSV = DERIVED_DIR / "uio_by_market_type_year.csv"
BUCKET_CSV = PRISM_ROOT / "data" / "uio_by_model_bucket.csv"

SHEET = "1.UIO Overview"
HEADER_ROW = 6          # 1-based row carrying the year labels
FIRST_DATA_ROW = 7
ACTUAL_THROUGH = 2024
ESTIMATE_YEAR = 2025

LD_NOTE_ISRAEL = (
    "LD is not a weight class here: this row is the whole N-series fleet at 6.5/7.5 t "
    "(the Ministry of Transport band table starts at 6.5-7.5 t and the CV warranty VIN "
    "register holds NPR75/FRR75/FSR90 and no NLR at all). It carries the 7.5 t parts "
    "wallet rate, not the 3.5 t one. Open issue LD-LABEL."
)
LD_NOTE_EU = (
    "LD means 3.5 t in most European markets, which is a different parts wallet rate from "
    "the 6.5/7.5 t reading of the same label. The band is per market and is not assumed "
    "here: the per-market 3.5 t share lives in uio_ld_n35_share.csv. Open issue LD-LABEL."
)
UTI_FLEET_NOTE = (
    "UTI CV rows run about 25% LOW in every year against the Israeli ministry's own "
    "registrations, so a per-truck figure on this denominator is flattered. "
    "Open issue UIO-FCAST."
)
FORECAST_NOTE = (
    "Forecast column. The workbook scraps about 3%/yr from 2026 while the 1990-2025 history "
    "uses a survival curve implying about 10.2%/yr (CV) and 12.3%/yr (LCV), so the "
    "forward years are overstated (+9% in 2026 to +59% by 2030 on the grand total, worse "
    "per market). Open issue UIO-FCAST. Never present a forecast year as measured."
)


def _year_columns(header: tuple) -> dict[int, int]:
    """year -> spreadsheet column index (0-based) for every year label in the header."""
    out: dict[int, int] = {}
    for i, v in enumerate(header):
        if v is None:
            continue
        s = str(v).strip()
        digits = "".join(ch for ch in s if ch.isdigit())
        if len(digits) == 4 and digits.startswith(("19", "20")):
            out[int(digits)] = i
    return out


def _distributor_codes() -> dict[str, str]:
    country_map = _country_to_distributor_map()
    out: dict[str, str] = {}
    for country in {c for c in country_map} | set(DIRECT_DISTRIBUTOR_COUNTRIES) | set(
        EXTRA_DIRECT_COUNTRY_CODES
    ):
        if country in DIRECT_DISTRIBUTOR_COUNTRIES:
            continue  # resolved per row from the workbook's own distributor column
        if country in EXTRA_DIRECT_COUNTRY_CODES:
            out[country] = EXTRA_DIRECT_COUNTRY_CODES[country]
        else:
            out[country] = country_map[country]
    return out


def build() -> tuple[pd.DataFrame, dict]:
    wb = openpyxl.load_workbook(resolve_uio_path(), read_only=True, data_only=True)
    ws = wb[SHEET]
    rows = list(ws.iter_rows(values_only=True))
    header = rows[HEADER_ROW - 1]
    ycols = _year_columns(header)
    if not ycols:
        raise ValueError(f"no year columns found on row {HEADER_ROW} of {SHEET}")

    country_to_code = _distributor_codes()
    years = sorted(ycols)

    recs: list[dict] = []
    skipped_countries: set[str] = set()
    for row_no, r in enumerate(rows[FIRST_DATA_ROW - 1:], start=FIRST_DATA_ROW):
        if r[0] is None:
            break  # end of the market block; what follows are the summary tables
        country, cv_lcv, model_type, uio_distributor = r[1], r[2], r[3], r[5]
        if cv_lcv not in ("CV", "LCV"):
            continue
        if country in DIRECT_DISTRIBUTOR_COUNTRIES:
            code = uio_distributor
        else:
            code = country_to_code.get(country)
        if not code or code in EXCLUDED_DISTRIBUTOR_CODES:
            skipped_countries.add(str(country))
            continue

        band_note = ""
        if str(model_type) == "LD":
            band_note = LD_NOTE_ISRAEL if country == "ISRAEL" else LD_NOTE_EU
        fleet_note = ""
        if country == "ISRAEL" and cv_lcv == "CV":
            fleet_note = UTI_FLEET_NOTE

        for year in years:
            raw = r[ycols[year]]
            value = None if raw is None else float(raw)
            if value is None:
                continue
            if year <= ACTUAL_THROUGH:
                basis = "actual"
            elif year == ESTIMATE_YEAR:
                basis = "estimate"
            else:
                basis = "forecast"
            notes = [n for n in (band_note, fleet_note,
                                 FORECAST_NOTE if basis == "forecast" else "") if n]
            recs.append({
                "distributor_code": code,
                "market": str(country),
                "vehicle_class": str(cv_lcv),
                "model_type": str(model_type),
                "year": int(year),
                "uio_units": round(value, 1),
                "is_actual": basis == "actual",
                "is_estimate": basis == "estimate",
                "is_forecast": basis == "forecast",
                "basis": basis,
                "source_note": f"ISUZU_UIO_Overview_2026.xlsx sheet '{SHEET}' row {row_no} "
                               f"({country} / {cv_lcv} / {model_type} / {uio_distributor}); "
                               f"column {year}",
                "band_note": band_note,
                "fleet_quality_note": fleet_note,
            })

    df = pd.DataFrame(recs).sort_values(
        ["distributor_code", "vehicle_class", "model_type", "year"]).reset_index(drop=True)
    meta = {
        "years": years,
        "skipped_countries": sorted(skipped_countries),
        "rows": len(df),
    }
    return df, meta


def reconcile_2025(df: pd.DataFrame) -> pd.DataFrame:
    """2025 column of the workbook against every 2025 row of the derived bucket file."""
    got = (df[df.year == ESTIMATE_YEAR]
           .groupby(["distributor_code", "vehicle_class", "model_type"], as_index=False)
           .uio_units.sum())
    piv = got.pivot_table(index="distributor_code",
                          columns=["vehicle_class", "model_type"],
                          values="uio_units", aggfunc="sum").fillna(0.0)

    def col(cls: str, mts: list[str]) -> pd.Series:
        s = pd.Series(0.0, index=piv.index)
        for mt in mts:
            if (cls, mt) in piv.columns:
                s = s + piv[(cls, mt)]
        return s

    mine = pd.DataFrame({
        "cv_std_uio": col("CV", ["LD", "MD"]),
        "f_series_uio": col("CV", ["F-Series"]),
        "lcv_uio": col("LCV", ["LCV"]),
    })
    mine["total"] = mine.sum(axis=1)

    base = pd.read_csv(BUCKET_CSV).set_index("distributor_code")
    out = mine.join(base[["cv_std_uio", "f_series_uio", "lcv_uio"]],
                    how="outer", rsuffix="_derived").fillna(0.0)
    out["source_year"] = base["source_year"]
    out["delta_total"] = out["total"] - (
        out["cv_std_uio_derived"] + out["f_series_uio_derived"] + out["lcv_uio_derived"])
    out["max_component_delta"] = (
        (out["cv_std_uio"] - out["cv_std_uio_derived"]).abs()
        .combine((out["f_series_uio"] - out["f_series_uio_derived"]).abs(), max)
        .combine((out["lcv_uio"] - out["lcv_uio_derived"]).abs(), max))
    return out


def main() -> int:
    df, meta = build()
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)

    print(f"Wrote {len(df):,} rows to {OUTPUT_CSV}")
    print(f"  markets          : {df.distributor_code.nunique()}")
    print(f"  years            : {meta['years'][0]} to {meta['years'][-1]}")
    print(f"  actual rows      : {int(df.is_actual.sum()):,}")
    print(f"  estimate rows    : {int(df.is_estimate.sum()):,}")
    print(f"  forecast rows    : {int(df.is_forecast.sum()):,}")
    print(f"  excluded markets : {', '.join(meta['skipped_countries']) or 'none'}")

    rec = reconcile_2025(df)
    print()
    print("2025 RECONCILIATION against data/uio_by_model_bucket.csv")
    print(rec[["total", "cv_std_uio_derived", "delta_total", "max_component_delta"]]
          .to_string())
    worst = float(rec.max_component_delta.max())
    print(f"  worst single-component delta: {worst:.4f}")
    if worst > 0.5:
        print("  RECONCILIATION FAIL: the workbook's 2025 column does not reproduce the "
              "derived bucket file")
        return 1
    print("  RECONCILIATION PASS: the workbook's 2025 column reproduces the derived file")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
