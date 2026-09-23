#!/usr/bin/env python3
"""GPS x PMS-capture strategic matrix by distributor x year.

Axis change 2026-07-17
----------------------
The x-axis used to be AIM pricing-risk exposure (`aim_high_risk_pct`) gated at a
hardcoded `RISK_HIGH_PCT = 0.12`. No distributor has ever crossed that line
(all-time max 0.0487, CY2025 network 0.0099), so `aim_low_risk` was True for
every row and the quadrant collapsed into a 1-D restatement of `gps_high` --
`margin_risk` had 0 rows ever, `priority_target` had 1 (the UNMAPPED null row).

x is now **PMS total capture**, which has real spread. AIM columns are retained
as passthrough context but no longer drive the quadrant.

Other fixes in the same pass:
  * Median benchmarks are computed **per year**, not pooled across all years.
    The pooled median (EUR 160.72) was dragged down ~EUR 30/unit by partial-year
    rows; a within-year median keeps a partial year internally comparable.
  * No `fillna` coercion onto an axis. Rows without a real GPS or capture value
    are `insufficient_data`, not silently "low". Previously `gps_spu.fillna(0)`
    classified the 4 no-UIO markets as "low GPS" and `aim_high_risk_pct.fillna(1.0)`
    invented a 100%-risk "priority target" out of the UNMAPPED row.
  * Each row carries `year_coverage_pct` / `is_partial_year` so downstream
    consumers can refuse to read a part-year absolute as a full-year number.

Part-year re-check 2026-09-22 (SPU-PARTIAL follow-up)
----------------------------------------------------
This file was re-examined because `gps_spu_by_distributor.csv` was found to pair a
part-year numerator with a full-year target. **The 2026 quadrant LABELS are not
misleading and are unchanged.** Established, not assumed:

  * Both axes are a value against a **within-year** median, so every distributor is
    truncated by the same window and the comparison is internally fair. That is the
    same principle the pipeline applies elsewhere.
  * Scaling the GPS axis - alone, not just both axes together - by 8/12 or 12/8
    changes **no** 2026 quadrant. The six 2026 `priority_target` markets
    (GREECE, HUNGARY, IUK, NORWAY, SWEDEN, UMI) sit in two tight groups,
    58.0-142.8 below the 119.997 median and 174.1-248.1 above it, so the bands are
    wide enough to absorb a 50% axis move.
  * Those six are also `priority_target` in 2024 and 2025 on the same method, so
    the 2026 labels are not an artefact of the partial year.

What **is** easy to misread, and why this note exists: `gps_spu_eur` is a **rate for
the eight months the row covers**, not a full-year rate, and `capture_axis` is an
eight-month numerator over a **full-year** `expected_qty` (that denominator is
identical in 2023, 2024, 2025 and 2026 - it is fleet x services/year). Both are
correctly computed for what they are. A reader who treats the column as a €/truck
rate comparable with 2025 will be wrong; the row's own `is_partial_year` and
`year_coverage_pct` are the guard. **Do not "fix" this by blanking the quadrant or
the rate - the ranking is sound and blanking it would lose the only spread the
matrix has.** Residual risk, stated plainly: the two-group structure is what makes
the ranking scale-robust, and if the fleet moves so that a market sits near the
median, that market's quadrant would become scale-sensitive.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    AIM_EXPOSURE_BY_DB_CSV,
    DERIVED_DIR,
    GPS_SPU_BY_DB_CSV,
    PMS_CAPTURE_BY_DB_CSV,
)
from modules.year_coverage import is_partial, year_coverage  # noqa: E402

OUT_CSV = DERIVED_DIR / "aim_gps_matrix.csv"
OUT_PARQUET = DERIVED_DIR / "aim_gps_matrix.parquet"

# Filter core: the categories whose expected-demand denominator is a plain
# per-service consumable. Emitted alongside the all-category capture so the
# scope sensitivity is visible rather than buried in a scope choice.
#   - air_filter carries FACTS.md flag C (0.5 interval factor is a PROVISIONAL
#     assumption pending IML confirmation, not an IML figure).
FILTER_CORE_CATS = ("oil_filter", "fuel_filter", "air_filter")

QUADRANT_LABELS = {
    "defend": "Defend (high GPS - high capture)",
    "attach_gap": "Attach gap (high GPS - low capture)",
    "wallet_gap": "Wallet gap (low GPS - high capture)",
    "priority_target": "Priority target (low GPS - low capture)",
    "insufficient_data": "Insufficient data (no GPS and/or no capture basis)",
}


def _capture_by_db_year(cats: tuple[str, ...] | None = None) -> pd.DataFrame:
    """Weighted PMS capture per distributor-year: sum(actual) / sum(expected).

    Uses line_type='total' only -- genuine/bvp/total share one expected_qty, so
    summing across line_type would treble-count the denominator.
    Matches dashboard_contracts.md contract 9 (`total_capture`).
    """
    df = pd.read_csv(PMS_CAPTURE_BY_DB_CSV)
    df = df[df["line_type"] == "total"]
    if cats:
        df = df[df["pms_category"].isin(cats)]
    g = (
        df.groupby(["year", "distributor_code"])
        .agg(
            pms_expected_qty=("expected_qty", "sum"),
            pms_actual_qty=("actual_qty", "sum"),
            pms_categories=("pms_category", "nunique"),
        )
        .reset_index()
    )
    g = g[g["pms_expected_qty"] > 0].copy()
    g["capture"] = (g["pms_actual_qty"] / g["pms_expected_qty"]).round(4)
    return g


def _quadrant(gps_high, capture_high) -> str:
    if pd.isna(gps_high) or pd.isna(capture_high):
        return "insufficient_data"
    if gps_high and capture_high:
        return "defend"
    if gps_high and not capture_high:
        return "attach_gap"
    if not gps_high and capture_high:
        return "wallet_gap"
    return "priority_target"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--scope",
        choices=["all", "filters"],
        default="all",
        help="Category scope driving the capture axis. 'all' matches "
        "dashboard_contracts.md contract 9; 'filters' uses oil/fuel/air only.",
    )
    args = ap.parse_args()

    for p in (GPS_SPU_BY_DB_CSV, AIM_EXPOSURE_BY_DB_CSV, PMS_CAPTURE_BY_DB_CSV):
        if not p.exists():
            print(f"Missing {p.name} -- run build_bvp_p4_p5.py / P0-P1 first", flush=True)
            return 1
    gps = pd.read_csv(GPS_SPU_BY_DB_CSV)
    aim = pd.read_csv(AIM_EXPOSURE_BY_DB_CSV)

    g = gps.rename(
        columns={
            "spend_per_unit_eur": "gps_spu_eur",
            "total_sales_eur": "gps_sales_eur",
            "traffic_light": "gps_traffic_light",
        }
    )[
        [
            "year",
            "distributor_code",
            "country",
            "region",
            "gps_sales_eur",
            "uio_units",
            "gps_spu_eur",
            "gps_traffic_light",
        ]
    ]

    a = aim.rename(
        columns={
            "high_risk_rev_pct": "aim_high_risk_pct",
            "aim_match_rate_rev": "aim_match_rate",
        }
    )[
        [
            "year",
            "distributor_code",
            "net_sales_eur",
            "aim_matched_rev_eur",
            "aim_match_rate",
            "high_risk_rev_eur",
            "aim_high_risk_pct",
            "strategic_rev_eur",
        ]
    ]

    cap_all = _capture_by_db_year().rename(columns={"capture": "pms_capture_all"})
    cap_flt = _capture_by_db_year(FILTER_CORE_CATS)[
        ["year", "distributor_code", "capture"]
    ].rename(columns={"capture": "pms_capture_filters"})

    df = g.merge(a, on=["year", "distributor_code"], how="outer")
    df = df.merge(cap_all, on=["year", "distributor_code"], how="left")
    df = df.merge(cap_flt, on=["year", "distributor_code"], how="left")

    axis_col = "pms_capture_all" if args.scope == "all" else "pms_capture_filters"
    df["capture_axis"] = df[axis_col]
    df["capture_axis_scope"] = args.scope

    # ── Partial-year coverage ────────────────────────────────────────────────
    cov = year_coverage()
    df["year_coverage_pct"] = df["year"].map(cov)
    df["is_partial_year"] = df["year"].map(is_partial)

    # ── Per-year medians. Within-year comparison stays fair even in a partial
    #    year because every distributor is truncated by the same window.
    df["gps_median_benchmark_eur"] = df.groupby("year")["gps_spu_eur"].transform("median")
    df["capture_median_benchmark"] = df.groupby("year")["capture_axis"].transform("median")

    # ── Axis flags. NaN stays NaN -- never coerced onto an axis. ─────────────
    df["gps_high"] = (
        (df["gps_spu_eur"] >= df["gps_median_benchmark_eur"])
        .astype("boolean")
        .mask(df["gps_spu_eur"].isna())
    )
    df["capture_high"] = (
        (df["capture_axis"] >= df["capture_median_benchmark"])
        .astype("boolean")
        .mask(df["capture_axis"].isna())
    )

    df["quadrant"] = [
        _quadrant(gh, ch) for gh, ch in zip(df["gps_high"], df["capture_high"])
    ]
    df["quadrant_label"] = df["quadrant"].map(QUADRANT_LABELS)

    df = df.sort_values(["year", "distributor_code"]).reset_index(drop=True)
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    df.to_parquet(OUT_PARQUET, index=False)

    print(f"  -> {len(df):,} rows -> {OUT_CSV}  (capture axis scope={args.scope})")
    print(f"     year coverage: {ftmt_cov(cov)}")
    for yr in sorted(df["year"].dropna().unique()):
        sub = df[df["year"] == yr]
        part = " [PARTIAL]" if bool(sub["is_partial_year"].iloc[0]) else ""
        med_g = sub["gps_median_benchmark_eur"].iloc[0]
        med_c = sub["capture_median_benchmark"].iloc[0]
        counts = sub["quadrant"].value_counts().to_dict()
        print(
            f"     {int(yr)}{part} median GPS EUR {med_g:,.2f} / capture {med_c:.4f} -> {counts}"
        )
    return 0


def ftmt_cov(cov: dict[int, float]) -> str:
    return ", ".join(f"{y}={v:.0%}" for y, v in sorted(cov.items()))


if __name__ == "__main__":
    raise SystemExit(main())
