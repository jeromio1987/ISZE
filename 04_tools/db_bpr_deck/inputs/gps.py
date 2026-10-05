"""Parts billed against the modelled spend of the fleet, and the service-demand denominators.

Both come from files the pipeline already builds, so the deck and the dashboards cannot drift:

  gps_spu_by_distributor.csv     parts billed, vehicles in service, spend per unit, target, capture
  wallet_waterfall.csv           the modelled spend and what is captured against it
  pms_capture_by_db_year.csv     expected replacement units and actual, per service family, per year
  mix_genuine_bvp_by_family.csv  billing split between Genuine and Best Value Parts

Where a figure is known not to be quotable (a capture above 100 per cent means the denominator
is wrong, not that we sold everything) the reader refuses and says why. Better an amber panel
than a number we would have to walk back.
"""
from __future__ import annotations

import pandas as pd

from ..errors import BprError, BprWarn
from ..paths import DERIVED_DIR

GPS_FILE = DERIVED_DIR / "gps_spu_by_distributor.csv"
WALLET_FILE = DERIVED_DIR / "wallet_waterfall.csv"
PMS_FILE = DERIVED_DIR / "pms_capture_by_db_year.csv"
MIX_FILE = DERIVED_DIR / "mix_genuine_bvp_by_family.csv"
TARGET_FLOOR = 1.02          # a capture above this is not quotable


def _read(path, what):
    if not path.is_file():
        raise BprError("E102", f"{what} is missing, so this slide cannot be built.",
                       path=path, expected=str(path.name))
    return pd.read_csv(path)


# ------------------------------------------------------------------ genuine parts share

def gps(db_code: str, year: int | None = None) -> dict:
    """This distributor's row(s). `db_code` is the code used in the GPS file (e.g. PORTUGAL)."""
    df = _read(GPS_FILE, "the parts-billed and target-spend file")
    col = "distributor_code" if "distributor_code" in df.columns else "country"
    df = df[df[col].astype(str).str.upper() == str(db_code).upper()]
    if df.empty:
        raise BprError("E401", f"{db_code} is not in the target-spend file, so genuine parts share cannot be shown.",
                       db=db_code, path=GPS_FILE,
                       found="codes present: " + ", ".join(sorted(
                           _read(GPS_FILE, "x")[col].astype(str).unique())[:40]))
    if year is not None and "year" in df.columns:
        df = df[df.year == int(year)]
        if df.empty:
            raise BprError("E301", f"{db_code} has no row for {year} in the target-spend file.",
                           db=db_code, path=GPS_FILE)
    row = df.sort_values("year").iloc[-1] if "year" in df.columns else df.iloc[0]

    billed = row.get("total_sales_eur")
    warranty = row.get("warranty_parts_eur")
    ex_warranty = row.get("sales_ex_warranty_eur")
    uio = row.get("uio_units")
    target = row.get("max_spend_eur")
    capture = row.get("gps_capture_vs_max")
    period = row.get("period_basis")
    note = row.get("coverage_note")

    if pd.isna(target) or not target:
        raise BprError("E401", f"{db_code} has no modelled target spend, so a share cannot be shown.",
                       db=db_code, path=GPS_FILE)
    if pd.notna(capture) and float(capture) > TARGET_FLOOR:
        raise BprError(
            "E401",
            f"{db_code}'s genuine parts share computes above 100 per cent, which means the "
            "target is too low rather than that we captured everything. It is not quotable.",
            db=db_code, path=GPS_FILE,
            found=f"billed {billed:,.0f} against a target of {target:,.0f}",
        )

    return {
        "db_code": db_code,
        "year": int(row.get("year")) if pd.notna(row.get("year")) else None,
        "billed_eur": float(billed) if pd.notna(billed) else None,
        "warranty_eur": float(warranty) if pd.notna(warranty) else None,
        "ex_warranty_eur": float(ex_warranty) if pd.notna(ex_warranty) else None,
        "uio_units": float(uio) if pd.notna(uio) else None,
        "target_eur": float(target),
        "capture": float(capture) if pd.notna(capture) else None,
        "period_basis": str(period) if pd.notna(period) else "",
        "coverage_note": str(note) if isinstance(note, str) else "",
        "source": GPS_FILE.name,
    }


def gps_series(db_code: str) -> pd.DataFrame:
    """Every year for this distributor, for a trend line."""
    df = _read(GPS_FILE, "the parts-billed and target-spend file")
    col = "distributor_code" if "distributor_code" in df.columns else "country"
    df = df[df[col].astype(str).str.upper() == str(db_code).upper()]
    if df.empty or "year" not in df.columns:
        return pd.DataFrame(columns=["year", "billed_eur", "target_eur", "capture"])
    out = df[["year", "total_sales_eur", "max_spend_eur", "gps_capture_vs_max"]].copy()
    out.columns = ["year", "billed_eur", "target_eur", "capture"]
    quotable = out.capture.isna() | (out.capture <= TARGET_FLOOR)
    out.loc[~quotable, "capture"] = None
    return out.sort_values("year").reset_index(drop=True)


def wallet(db_code: str, year: int | None = None) -> dict | None:
    """The modelled spend waterfall, when it covers this distributor."""
    if not WALLET_FILE.is_file():
        return None
    df = pd.read_csv(WALLET_FILE)
    df = df[df.distributor_code.astype(str).str.upper() == str(db_code).upper()]
    if df.empty:
        return None
    if year is not None:
        df = df[df.year == int(year)]
    if df.empty:
        return None
    row = df.sort_values("year").iloc[-1]
    return {
        "year": int(row.year),
        "uio_units": float(row.uio_units) if pd.notna(row.uio_units) else None,
        "theoretical_eur": float(row.theoretical_wallet_eur) if pd.notna(row.theoretical_wallet_eur) else None,
        "captured_eur": float(row.captured_total_eur) if pd.notna(row.captured_total_eur) else None,
        "uncaptured_eur": float(row.uncaptured_eur) if pd.notna(row.uncaptured_eur) else None,
        "addressable_eur": float(row.addressable_uncaptured_eur) if pd.notna(row.addressable_uncaptured_eur) else None,
        "gps_pct": float(row.gps_pct) if pd.notna(row.gps_pct) else None,
        "note": str(row.assumption_note) if isinstance(row.assumption_note, str) else "",
        "source": WALLET_FILE.name,
    }


# ------------------------------------------------------------------ service-demand cover

def pms(db_code: str, years: tuple[int, ...] = (2025, 2026)) -> pd.DataFrame:
    """Expected versus actual units by service family. Uses the total line, not genuine only."""
    df = _read(PMS_FILE, "the service-demand cover file")
    df = df[df.distributor_code.astype(str).str.upper() == str(db_code).upper()]
    if df.empty:
        raise BprError("E401", f"{db_code} is not in the service-demand file.",
                       db=db_code, path=PMS_FILE,
                       found="codes present: " + ", ".join(sorted(
                           _read(PMS_FILE, "x").distributor_code.astype(str).unique())[:40]))
    if "line_type" in df.columns:
        # 'total' is the headline. Genuine-only would hide value parts, which is a finding, not a view.
        total = df[df.line_type == "total"]
        df = total if not total.empty else df
    if "year" in df.columns:
        df = df[df.year.isin(years)]
    keep = [c for c in ("year", "pms_category", "category_label", "expected_qty", "actual_qty",
                        "capture_rate", "revenue_gap_eur", "avg_sp_eur", "uio_units")
            if c in df.columns]
    out = df[keep].copy()
    if "capture_rate" in out.columns:
        out["capture_rate"] = pd.to_numeric(out.capture_rate, errors="coerce")
    return out.sort_values(["year", "capture_rate"]) .reset_index(drop=True)


# ------------------------------------------------------------------ mix

def mix(db_code: str, years: tuple[int, ...] = (2023, 2024, 2025)) -> pd.DataFrame:
    df = _read(MIX_FILE, "the genuine and value-parts mix file")
    df = df[df.distributor_code.astype(str).str.upper() == str(db_code).upper()]
    if df.empty:
        raise BprError("E401", f"{db_code} is not in the genuine and value-parts mix file.",
                       db=db_code, path=MIX_FILE)
    if "year" in df.columns:
        df = df[df.year.isin(years)]
    keep = [c for c in ("year", "product_family", "bvp_qty", "genuine_qty", "bvp_eur",
                        "genuine_eur", "bvp_share_eur", "total_eur") if c in df.columns]
    return df[keep].sort_values(["year", "product_family"]).reset_index(drop=True)


def probes(db_code: str) -> list[BprWarn]:
    out: list[BprWarn] = []
    for name, fn in (("genuine parts share", lambda: gps(db_code)),
                     ("service-demand cover", lambda: pms(db_code))):
        try:
            fn()
            out.append(BprWarn(f"{name}: available for {db_code}"))
        except BprError as exc:
            out.append(BprWarn(f"{name}: not quotable - {exc.message}"))
    return out
