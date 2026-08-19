"""Load distributor sales-to-dealer files (UTI PartSales, ITUK pivot export)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

from config import ISZE_ROOT, RAW_DEALER_SALES_DIR

UTI_DIR = RAW_DEALER_SALES_DIR / "UTI"
ITUK_DIR = RAW_DEALER_SALES_DIR / "ITUK"
ITUK_LEGACY_DIR = ISZE_ROOT / "Isuzu"

MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def normalize_pn(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    if not s or s.lower() == "nan":
        return None
    token = s.split()[0].split("-")[0]
    digits = re.sub(r"\D", "", token)
    if len(digits) < 8:
        return None
    return digits.zfill(10)


def _uti_source_paths() -> list[Path]:
    """Canonical paths only (avoid duplicate legacy Data/ copies in reports)."""
    return [p for p in (UTI_DIR / "UTIPartSales_2025-01.xlsx", UTI_DIR / "UTIPartSales_2025-12_YTD.xlsx") if p.exists()]


def load_uti_part_sales(path: Path | None = None) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Parse UTI UTIPartSales sheet → part_number, qty_month, qty_ytd + report metadata."""
    if path is None:
        paths = _uti_source_paths()
        if not paths:
            return pd.DataFrame(), {}
        path = paths[-1] if "CY2025" in paths[-1].name or "12" in paths[-1].name else paths[0]

    meta_raw = pd.read_excel(path, sheet_name=0, header=None, nrows=4)
    report_month = meta_raw.iloc[2, 4]
    report_year = meta_raw.iloc[2, 7]
    try:
        report_month = int(float(report_month))
    except (TypeError, ValueError):
        report_month = None
    try:
        report_year = int(float(report_year))
    except (TypeError, ValueError):
        report_year = None

    raw = pd.read_excel(path, sheet_name=0, header=5)
    df = raw.iloc[:, :3].copy()
    df.columns = ["part_number", "qty_month", "qty_ytd"]
    df["part_number"] = df["part_number"].map(normalize_pn)
    df = df.dropna(subset=["part_number"])
    for c in ("qty_month", "qty_ytd"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df.loc[df["qty_month"] > 100_000, "qty_month"] = 0
    df.loc[df["qty_ytd"] > 500_000, "qty_ytd"] = 0

    meta = {
        "source_file": path.name,
        "report_month": report_month,
        "report_year": report_year,
        "distributor_code": "UTI",
        "row_count": len(df),
        "unique_pn": int(df["part_number"].nunique()),
    }
    return df, meta


def load_ituk_dealer_sales(year: int = 2025, path: Path | None = None) -> pd.DataFrame:
    """ITUK dealer×PN pivot → long format with optional month breakdown."""
    if path is None:
        candidates = [
            ITUK_DIR / f"Sales to Dealers_ITUK_CY{year}.xlsx",
            ITUK_LEGACY_DIR / f"Sales to Dealers_ITUK_CY{year}.xlsx",
        ]
        path = next((p for p in candidates if p.exists()), candidates[0])
    if not path.exists():
        return pd.DataFrame()

    probe = pd.read_excel(path, sheet_name=0, header=None)
    header_row = None
    for i in range(min(20, len(probe))):
        row = [str(x).strip() if pd.notna(x) else "" for x in probe.iloc[i]]
        if row[0] == "Customer Name" and "Item Number" in row:
            header_row = i
            break
    if header_row is None:
        return pd.DataFrame()

    df = pd.read_excel(path, sheet_name=0, header=header_row)
    if "Item Number" not in df.columns:
        return pd.DataFrame()

    month_cols = [c for c in df.columns if c in MONTHS]
    for c in month_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    df["part_number"] = df["Item Number"].map(normalize_pn)
    df = df.dropna(subset=["part_number"])
    dealer_col = "Customer Name" if "Customer Name" in df.columns else df.columns[0]
    df["dealer_name"] = df[dealer_col].astype(str).str.strip()
    if month_cols:
        df["qty_year"] = df[month_cols].sum(axis=1)
    else:
        df["qty_year"] = 0
    df.loc[df["qty_year"] > 100_000, "qty_year"] = pd.NA
    df["qty_year"] = df["qty_year"].fillna(0)

    out = df[
        ["dealer_name", "part_number", "qty_year", *month_cols]
    ].copy()
    out["distributor_code"] = "ITUK"
    out["year"] = year
    out["data_source"] = path.name
    return out


def aggregate_pn(df: pd.DataFrame, qty_col: str) -> pd.DataFrame:
    if df.empty or qty_col not in df.columns:
        return pd.DataFrame(columns=["part_number", "qty"])
    g = df.groupby("part_number", as_index=False)[qty_col].sum()
    g = g.rename(columns={qty_col: "qty"})
    return g


def sellout_long_path(derived_dir: Path, distributor_code: str, year: int) -> Path | None:
    """Resolve canonical long CSV for a DB×year (CY full year preferred over YTD name)."""
    code = str(distributor_code).strip().upper()
    candidates = [
        derived_dir / f"dealer_sellout_long_{code}_CY{year}.csv",
        derived_dir / f"dealer_sellout_long_{code}_CY{year}YTD.csv",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def discover_sellout_long_dists(derived_dir: Path, year: int) -> list[str]:
    """Distributor codes that have a normalized long file for the calendar year."""
    found: list[str] = []
    for p in sorted(derived_dir.glob(f"dealer_sellout_long_*_CY{year}.csv")):
        # dealer_sellout_long_IRELAND_CY2025.csv
        stem = p.stem  # dealer_sellout_long_IRELAND_CY2025
        mid = stem.removeprefix("dealer_sellout_long_").removesuffix(f"_CY{year}")
        if mid and mid not in found:
            found.append(mid)
    return found


def load_sellout_long_pn(
    distributor_code: str,
    year: int,
    derived_dir: Path,
) -> pd.DataFrame:
    """Load canonical long sell-out → PN × qty_year (network aggregate)."""
    path = sellout_long_path(derived_dir, distributor_code, year)
    if path is None:
        return pd.DataFrame(columns=["part_number", "qty_year"])
    df = pd.read_csv(path, dtype={"part_number": str}, low_memory=False)
    if df.empty or "part_number" not in df.columns or "qty" not in df.columns:
        return pd.DataFrame(columns=["part_number", "qty_year"])
    if "year" in df.columns:
        df = df[pd.to_numeric(df["year"], errors="coerce") == year]
    df = df.copy()
    df["part_number"] = df["part_number"].map(normalize_pn)
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0)
    df = df.dropna(subset=["part_number"])
    return (
        df.groupby("part_number", as_index=False)["qty"]
        .sum()
        .rename(columns={"qty": "qty_year"})
    )


def load_all_uti_snapshots() -> list[tuple[pd.DataFrame, dict[str, Any]]]:
    """Load every UTI file found (canonical + legacy Data/ names)."""
    seen: set[str] = set()
    out: list[tuple[pd.DataFrame, dict[str, Any]]] = []
    for p in _uti_source_paths():
        key = p.resolve().as_posix()
        if key in seen:
            continue
        seen.add(key)
        df, meta = load_uti_part_sales(p)
        if not df.empty:
            out.append((df, meta))
    return out
