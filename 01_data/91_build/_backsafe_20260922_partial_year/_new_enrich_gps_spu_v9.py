#!/usr/bin/env python3
"""
Enrich gps_spu_by_distributor.csv with GPS v9 max-spend targets (UIO v18 + study rates).

Run after build_bvp_p4_p5.py. Re-reads uio_v18_gps.json (build via Data/_build/gps_v9_loaders.py).

Partial-year guard (added 2026-09-22, SPU-PARTIAL)
-------------------------------------------------
The 2026 rows carry eight months of billing (to 2026-08-31) against a full-year
target. Dividing one by the other produces a capture rate that is not merely
incomparable, it is false, and the red light that comes with it reads as a
collapse that did not happen. The 2026-09-15 containment blanked those columns
in the file; this script put them straight back on 2026-09-21, because the guard
belonged here, in the writer, and not in the file.

So: a row whose own ``period_basis`` says ``partial_year`` (falling back to
``modules.year_coverage.is_partial``) gets NO capture percentage and NO colour.
``max_spend_eur``, ``total_sales_eur``, ``uio_units`` and ``spend_per_unit_eur``
are deliberately left alone - the target is a legitimately published full-year
figure, the sales figure and the fleet are facts, and the per-truck rate is
correctly computed for the part year it covers.

``period_basis`` and ``coverage_note`` are re-emitted every run so the annotation
cannot be lost again, and the script REFUSES TO WRITE if any partial-year row
still carries a percentage or a colour - a silent guard is one that the next
person removes.

See ``01_data/00_derived/_data_integrity_open_issues.md`` - SPU-PARTIAL.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DATA_BUILD_DIR, DERIVED_DIR, GPS_SPU_BY_DB_CSV  # noqa: E402
from modules.bvp_analytics import UIO_OVERRIDES  # noqa: E402
from modules.year_coverage import is_partial  # noqa: E402

V9_JSON = DATA_BUILD_DIR / "uio_v19_gps.json"
if not V9_JSON.is_file():
    V9_JSON = DATA_BUILD_DIR / "uio_v18_gps.json"


def _traffic_light_v9(capture: float) -> str:
    if pd.isna(capture):
        return "unknown"
    if capture >= 0.85:
        return "green"
    if capture >= 0.50:
        return "amber"
    return "red"


PARTIAL_BASIS = "partial_year"
FULL_BASIS = "full_year"

# Same wording the file already carries on its 2026 rows. Kept identical so the
# existing annotation is not restyled on every run.
PARTIAL_COVERAGE_NOTE = (
    "PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. "
    "Do not compare against a full-year row, and do not read a capture % or traffic "
    "light off this row: the max-spend target is a full-year figure. Basis not "
    "reconcilable to a clean quarter from sales_fact; see "
    "01_data/00_derived/_data_integrity_open_issues.md."
)
FULL_COVERAGE_NOTE = "FULL YEAR - calendar year complete."


def _is_partial_row(row) -> bool:
    """Is this a part-period numerator sitting over a full-period denominator?

    The row's own ``period_basis`` wins: it was written by whoever knew the
    extract date. Only when that column is absent or blank do we fall back to the
    billing-date coverage of the year in ``sales_fact``.
    """
    basis = str(row.get("period_basis") or "").strip().lower()
    if basis:
        return basis == PARTIAL_BASIS
    try:
        return bool(is_partial(int(row["year"])))
    except (TypeError, ValueError, KeyError):
        return False


def _ensure_basis_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Keep ``period_basis`` / ``coverage_note`` present so the warning survives.

    The 2026-09-21 regeneration dropped both columns and nothing noticed for a
    day. Rebuild them from ``year_coverage`` when they are absent, and fill any
    blank note on a partial row.
    """
    if "period_basis" not in df.columns:
        df["period_basis"] = [
            PARTIAL_BASIS if is_partial(int(y)) else FULL_BASIS for y in df["year"]
        ]
    else:
        blank = df["period_basis"].fillna("").astype(str).str.strip().eq("")
        if blank.any():
            df.loc[blank, "period_basis"] = [
                PARTIAL_BASIS if is_partial(int(y)) else FULL_BASIS
                for y in df.loc[blank, "year"]
            ]
    if "coverage_note" not in df.columns:
        df["coverage_note"] = ""
    partial = df["period_basis"].astype(str).str.strip().str.lower().eq(PARTIAL_BASIS)
    blank_note = df["coverage_note"].fillna("").astype(str).str.strip().eq("")
    df.loc[partial & blank_note, "coverage_note"] = PARTIAL_COVERAGE_NOTE
    df.loc[~partial & blank_note, "coverage_note"] = FULL_COVERAGE_NOTE
    return df


def _assert_no_capture_on_partial_rows(df: pd.DataFrame) -> None:
    """A row that says 'do not read a capture % off this row' must not carry one."""
    if "period_basis" not in df.columns:
        return
    bad = df[df["period_basis"].astype(str).str.strip().str.lower().eq(PARTIAL_BASIS)]
    if bad.empty:
        return
    for col in ("gps_capture_vs_max", "gps_capture_ex_warranty_vs_max"):
        if col in bad.columns:
            n = int(bad[col].notna().sum())
            if n:
                raise SystemExit(f"refusing to write: {n} partial-year rows carry {col}")
    for col in ("traffic_light_v9", "traffic_light_v9_ex_warranty"):
        if col in bad.columns:
            coloured = ~bad[col].fillna("").astype(str).str.strip().isin(["", "unknown"])
            n = int(coloured.sum())
            if n:
                raise SystemExit(
                    f"refusing to write: {n} partial-year rows carry a {col} colour"
                )


def main() -> None:
    if not GPS_SPU_BY_DB_CSV.exists():
        print("SKIP: gps_spu_by_distributor.csv missing", flush=True)
        return
    if not V9_JSON.exists():
        # Build snapshot on demand
        sys.path.insert(0, str(DATA_BUILD_DIR))
        import gps_v9_loaders as g9  # type: ignore

        g9.main()
        print("Built", V9_JSON, flush=True)

    payload = json.loads(V9_JSON.read_text(encoding="utf-8"))
    dists = payload.get("distributors", {})

    df = pd.read_csv(GPS_SPU_BY_DB_CSV)
    df = _ensure_basis_columns(df)
    max_spend: list[float | None] = []
    capture_pct: list[float | None] = []
    lights: list[str] = []

    for _, row in df.iterrows():
        db = row["distributor_code"]
        year = int(row["year"])
        partial = _is_partial_row(row)
        d = dists.get(db, {})
        ms = (d.get("max_spend") or {}).get(str(year))
        if ms is None and year == 2025:
            ms = (d.get("max_spend") or {}).get("2025")
        # Never let a refresh wipe a target the file already carries: the target
        # is a published figure, not a derived one.
        existing_ms = row.get("max_spend_eur")
        if ms is None and pd.notna(existing_ms) and float(existing_ms) > 0:
            ms = float(existing_ms)
        sales = float(row.get("total_sales_eur") or 0)
        max_spend.append(round(float(ms), 2) if ms else None)
        # A part-period numerator over a full-year denominator is not a capture %.
        # ``max_spend_eur`` itself stays: the target is a real, published figure.
        if partial:
            cap = None
        else:
            cap = sales / float(ms) if ms and float(ms) > 0 else None
        capture_pct.append(round(cap, 4) if cap is not None else None)
        if partial:
            lights.append("unknown")
        elif cap is not None:
            lights.append(_traffic_light_v9(cap))
        else:
            lights.append(row.get("traffic_light", "unknown"))

    df["max_spend_eur"] = max_spend
    df["gps_capture_vs_max"] = capture_pct
    df["traffic_light_v9"] = lights
    df["gps_capture_ex_warranty_vs_max"] = None
    df["traffic_light_v9_ex_warranty"] = None

    # Align 2025 UIO with v18 workbook totals where present (ITUK override kept in pipeline)
    def _uio_total(d: dict, year: int) -> float | None:
        uio_by_year = d.get("uio") or {}
        buckets = uio_by_year.get(year) or uio_by_year.get(str(year))
        if isinstance(buckets, dict):
            return sum(float(v) for v in buckets.values())
        if buckets is not None:
            return float(buckets)
        return None

    for idx, row in df[df["year"] == 2025].iterrows():
        db = row["distributor_code"]
        uio_v9 = _uio_total(dists.get(db, {}), 2025)
        if db in UIO_OVERRIDES:
            o = UIO_OVERRIDES[db]
            df.at[idx, "uio_units"] = int(o["uio_units"])
            df.at[idx, "uio_source"] = o["uio_source"]
            uio_v9 = float(o["uio_units"])
        elif uio_v9:
            df.at[idx, "uio_units"] = int(round(uio_v9))
            if str(row.get("uio_source", "")).startswith("v18"):
                df.at[idx, "uio_source"] = "v18_actual"
        if uio_v9 and row.get("total_sales_eur"):
            df.at[idx, "spend_per_unit_eur"] = round(
                float(row["total_sales_eur"]) / float(uio_v9), 2
            )
        sales = float(df.at[idx, "total_sales_eur"] or 0)
        ms = df.at[idx, "max_spend_eur"]
        if ms and float(ms) > 0 and not _is_partial_row(df.loc[idx]):
            cap = sales / float(ms)
            df.at[idx, "gps_capture_vs_max"] = round(cap, 4)
            df.at[idx, "traffic_light_v9"] = _traffic_light_v9(cap)
        sales_ex = df.at[idx, "sales_ex_warranty_eur"]
        if ms and pd.notna(sales_ex) and float(ms) > 0 and not _is_partial_row(df.loc[idx]):
            cap_ex = float(sales_ex) / float(ms)
            df.at[idx, "gps_capture_ex_warranty_vs_max"] = round(cap_ex, 4)
            df.at[idx, "traffic_light_v9_ex_warranty"] = _traffic_light_v9(cap_ex)
        if pd.notna(df.at[idx, "sales_ex_warranty_eur"]) and uio_v9:
            df.at[idx, "spend_per_unit_ex_warranty_eur"] = round(
                float(df.at[idx, "sales_ex_warranty_eur"]) / float(uio_v9 or row["uio_units"]), 2
            )

    for idx, row in df.iterrows():
        ms = row.get("max_spend_eur")
        sales_ex = row.get("sales_ex_warranty_eur")
        if ms and pd.notna(sales_ex) and float(ms) > 0 and not _is_partial_row(row):
            cap_ex = float(sales_ex) / float(ms)
            df.at[idx, "gps_capture_ex_warranty_vs_max"] = round(cap_ex, 4)
            df.at[idx, "traffic_light_v9_ex_warranty"] = _traffic_light_v9(cap_ex)

    _assert_no_capture_on_partial_rows(df)
    df.to_csv(GPS_SPU_BY_DB_CSV, index=False)
    n_ms = df["max_spend_eur"].notna().sum()
    n_partial = int(
        df["period_basis"].astype(str).str.strip().str.lower().eq(PARTIAL_BASIS).sum()
    )
    print(
        f"enrich_gps_spu_v9: {len(df)} rows, max_spend on {n_ms}, "
        f"{n_partial} partial-year rows held at unknown -> {GPS_SPU_BY_DB_CSV}",
        flush=True,
    )


if __name__ == "__main__":
    main()
