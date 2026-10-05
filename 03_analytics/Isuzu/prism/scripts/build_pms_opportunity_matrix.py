#!/usr/bin/env python3
"""
Contract 3 — PMS Opportunity Matrix.

Output: Data/derived/pms_opportunity_matrix.csv
Sources: pms_capture_by_db_year.csv + gps_spu_by_distributor.csv

Run after build_bvp_p0_p1.py and build_bvp_p4_p5.py (GPS SPU).

Partial-year annotation (added 2026-09-22, SPU-PARTIAL follow-up)
-----------------------------------------------------------------
``expected_qty`` comes from fleet x services-per-year, so it is a **full-year**
denominator - verified identical in 2023, 2024, 2025 and 2026. On the 2026 rows the
actual side is eight months (billing to 2026-08-31). ``revenue_gap_eur`` is

    max(expected_qty - actual_qty, 0) x avg_sp_eur

so on a partial year the bracket is (twelve-month expectation - eight-month actual).
It is not a false number - it is the honest gap against the year's full expectation -
but it is **inflated by the four missing months**, and reading it beside a full year
as though both were like-for-like overstates the newest year by about 39% on the
network total. Nothing in this file said so.

Two things are emitted so a reader can tell:

  * ``period_basis`` / ``coverage_note``  - the same two columns and wording used on
    gps_spu_by_distributor.csv, so one reader learns one convention.
  * ``gap_eur_like_for_like``            - the same gap with the expectation put on
    the row's own coverage (the full year for a full-year row, so it equals
    ``revenue_gap_eur`` exactly there). **This rests on an assumption** - that the
    year's expectation falls evenly, which it does not (filters and brakes are
    seasonal) - so the assumption is stated in the column beside it and the figure is
    a comparator, not a replacement. ``revenue_gap_eur`` is deliberately untouched.

A silent guard is one the next person removes, so the annotation is re-emitted every
run.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    DERIVED_DIR,
    GPS_SPU_BY_DB_CSV,
    PMS_CAPTURE_BY_DB_CSV,
)
from modules.year_coverage import is_partial, year_coverage  # noqa: E402

OUTPUT_CSV = DERIVED_DIR / "pms_opportunity_matrix.csv"

PARTIAL_BASIS = "partial_year"
FULL_BASIS = "full_year"

# Same wording as gps_spu_by_distributor.csv / the family and PMS slices.
PARTIAL_COVERAGE_NOTE = (
    "PARTIAL YEAR - actual_qty covers part of the calendar year, NOT 12 months, "
    "while expected_qty is a full year. revenue_gap_eur is therefore the gap against "
    "the FULL YEAR expectation and is larger than a like-for-like gap; "
    "gap_eur_like_for_like puts the expectation on the same period. See "
    "01_data/00_derived/_data_integrity_open_issues.md."
)
FULL_COVERAGE_NOTE = "FULL YEAR - calendar year complete."

L4L_ASSUMPTION_PARTIAL = (
    "Sets expected_qty to coverage x expected_qty, where coverage is the share of the "
    "calendar year the billing data reaches (from modules.year_coverage). ASSUMES the "
    "year's expectation falls evenly across months, which it does not - filters and "
    "brakes are seasonal. A comparator, not a replacement for revenue_gap_eur."
)
L4L_ASSUMPTION_FULL = "No pro-rating: a full-year row needs none. Equals revenue_gap_eur."

NEW_COLUMNS = [
    "gap_eur_like_for_like",
    "period_basis",
    "coverage_note",
    "like_for_like_assumption",
    "year_coverage_pct",
]


def build_pms_opportunity_matrix(
    pms_path: Path = PMS_CAPTURE_BY_DB_CSV,
    gps_path: Path = GPS_SPU_BY_DB_CSV,
) -> pd.DataFrame:
    if not pms_path.exists():
        raise FileNotFoundError(f"Missing {pms_path}")
    if not gps_path.exists():
        raise FileNotFoundError(f"Missing {gps_path}")

    pms = pd.read_csv(pms_path)
    gps = pd.read_csv(gps_path)[["year", "distributor_code", "country", "region"]]

    keys = ["year", "distributor_code", "pms_category"]
    total = pms[pms["line_type"] == "total"].copy()
    genuine = pms[pms["line_type"] == "genuine"].copy()

    total = total[total["expected_qty"] > 0]
    if total.empty:
        return pd.DataFrame()

    gen_cols = {
        "capture_rate": "capture_rate_genuine",
        "actual_qty": "actual_qty_genuine",
    }
    gen = genuine[keys + ["capture_rate"]].rename(columns=gen_cols)

    out = total[keys + [
        "uio_units",
        "expected_qty",
        "actual_qty",
        "actual_rev_eur",
        "capture_rate",
        "revenue_gap_eur",
        "revenue_gap_quotable",
    ]].rename(columns={"capture_rate": "capture_rate_total"})

    out = out.merge(gen, on=keys, how="left")
    out["capture_rate_genuine"] = out["capture_rate_genuine"].fillna(0.0)

    out["avg_sp_eur"] = np.where(
        out["actual_qty"] > 0,
        out["actual_rev_eur"] / out["actual_qty"],
        0.0,
    )
    out["tam_eur"] = out["expected_qty"] * out["avg_sp_eur"]
    out["genuine_bvp_gap_pp"] = out["capture_rate_total"] - out["capture_rate_genuine"]
    out["uio_units"] = out["uio_units"].astype(int)

    out = out.merge(gps, on=["year", "distributor_code"], how="left")

    # ── Partial-year annotation (SPU-PARTIAL follow-up, 2026-09-22) ───────────
    # expected_qty is a full-year figure; on a partial year the actual side is not,
    # so revenue_gap_eur is inflated by the missing months. Say so, and give the
    # like-for-like comparator beside it rather than touching the original.
    cov = year_coverage()
    out["year_coverage_pct"] = out["year"].map(cov)
    partial = out["year"].map(is_partial)
    out["period_basis"] = partial.map({True: PARTIAL_BASIS, False: FULL_BASIS})
    out["coverage_note"] = partial.map(
        {True: PARTIAL_COVERAGE_NOTE, False: FULL_COVERAGE_NOTE}
    )
    # Pro-rate ONLY a partial year, and do it algebraically off revenue_gap_eur
    # rather than by recomputing the bracket. Two reasons, both learned the hard way:
    #   1. year_coverage() reports 0.9918-0.9973 for 2023-2025 (billing stops a few
    #      days short of 31 December). Scaling a full year would move 602 figures for
    #      nothing, so the shortfall is 0 on a full-year row.
    #   2. expected_qty / actual_qty in the source are stored to one decimal, so
    #      recomputing max(expected - actual, 0) - which is what pms_engine did -
    #      carries up to +/-0.1 qty of rounding, about +/-EUR 8 at an EUR 80 unit
    #      price. Deriving from revenue_gap_eur is exact: with coverage 1.0 it returns
    #      revenue_gap_eur unchanged, to the cent.
    shortfall = np.where(partial, 1.0 - out["year_coverage_pct"], 0.0)
    out["gap_eur_like_for_like"] = np.maximum(
        out["revenue_gap_eur"] - out["tam_eur"] * shortfall, 0.0
    ).round(2)
    out["like_for_like_assumption"] = partial.map(
        {True: L4L_ASSUMPTION_PARTIAL, False: L4L_ASSUMPTION_FULL}
    )
    # A full-year row must not move at all - that is the whole point of the guard.
    full = out["period_basis"].eq(FULL_BASIS)
    drift = (out.loc[full, "gap_eur_like_for_like"]
             - out.loc[full, "revenue_gap_eur"]).abs()
    if bool((drift > 0.01).any()):
        raise SystemExit(
            "refusing to write: gap_eur_like_for_like differs from revenue_gap_eur on "
            f"{int((drift > 0.01).sum())} full-year row(s) - a full year must not be "
            "pro-rated"
        )
    # The annotation must not be lost again, and a partial row must not claim to be
    # a full one.
    blank = out["coverage_note"].fillna("").astype(str).str.strip().eq("")
    if bool((partial & blank).any()):
        raise SystemExit("refusing to write: a partial-year row carries no coverage note")

    columns = [
        "distributor_code",
        "pms_category",
        "year",
        "capture_rate_total",
        "capture_rate_genuine",
        "revenue_gap_eur",
        "revenue_gap_quotable",
        "gap_eur_like_for_like",
        "avg_sp_eur",
        "tam_eur",
        "uio_units",
        "genuine_bvp_gap_pp",
        "country",
        "region",
        "period_basis",
        "coverage_note",
        "like_for_like_assumption",
    ]
    out = out[columns].sort_values(
        ["year", "distributor_code", "pms_category"]
    ).reset_index(drop=True)
    return out


def _compare(out_path: Path, old_path: Path) -> None:
    """Report whether a rebuild moved anything it should not have."""
    old = pd.read_csv(old_path)
    new = pd.read_csv(out_path)
    keep = ["distributor_code", "pms_category", "year"]
    shared = [c for c in old.columns if c in new.columns and c not in keep]
    m = old[keep + shared].merge(
        new[keep + shared], on=keep, how="outer",
        suffixes=("_old", "_new"), indicator=True,
    )
    print(f"  rows: old {len(old)}, new {len(new)}; "
          f"only-old {int((m['_merge'] == 'left_only').sum())}, "
          f"only-new {int((m['_merge'] == 'right_only').sum())}")
    for c in shared:
        a, b = m[f"{c}_old"], m[f"{c}_new"]
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            d = (a.astype(float) - b.astype(float)).abs()
            print(f"  {c:26s} max abs diff {d.max():.6f}   rows>0.01 "
                  f"{int((d > 0.01).sum())}")
        else:
            n = int((a.astype(str) != b.astype(str)).sum())
            print(f"  {c:26s} text column        differing rows {n}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the PMS opportunity matrix.")
    ap.add_argument(
        "--out",
        default=str(OUTPUT_CSV),
        help="Where to write. Point it at a temp file to preview a change without "
             "touching the live derived file.",
    )
    ap.add_argument(
        "--compare-to",
        default=None,
        help="An existing CSV to diff the unchanged columns against, so a rebuild can "
             "be checked before it is adopted.",
    )
    args = ap.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df = build_pms_opportunity_matrix()
    if df.empty:
        print("  WARNING: no rows produced")
        return 1
    df.to_csv(out_path, index=False)
    print(f"pms_opportunity_matrix: {len(df):,} rows -> {out_path}")
    if args.compare_to:
        _compare(out_path, Path(args.compare_to))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
