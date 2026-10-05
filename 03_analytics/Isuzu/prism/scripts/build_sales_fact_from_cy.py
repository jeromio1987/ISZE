#!/usr/bin/env python3
"""
Build ISZE/Data/derived/sales_fact.parquet from raw CY billing exports.

Run from prism folder:
  python scripts/build_sales_fact_from_cy.py

Requires: pandas, openpyxl, pyarrow
Sources: 12_raw/sales/CY2023-2024.XLSX, CY2024-2025.XLSX,
         sales_2026tillApril.XLSX (2026 Jan–Mar), Q1FY2027.XLSX (2026 Apr–Jun).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Union

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DERIVED_DIR, RAW_SALES_DIR, SALES_FACT_PARQUET  # noqa: E402

# Each source file "owns" the years listed. Where two exports cover the same
# year (verified 2026-07-03: CY2024-2025.XLSX's 2024 rows are identical to
# CY2023-2024.XLSX's — 154,519 rows, full Bill.Doc. overlap; its 2025 rows are
# a more complete re-export, 148,778 vs the old CY2025.XLSX's 147,409), the
# later file wins and the older file's rows for that year are dropped so we
# never double-count. CY2025.XLSX is kept on disk but no longer loaded.
#
# 2026 split (audit 2026-08-25): sales_2026tillApril = Jan–Mar;
# Q1FY2027.XLSX = Apr–Jun (Isuzu FY2027 Q1). Month filter below prevents overlap.
CY_FILE_YEARS: dict[str, set[int]] = {
    "CY2023-2024.XLSX": {2023},
    "CY2024-2025.XLSX": {2024, 2025},
    "sales_2026tillApril.XLSX": {2026},
    "Q1FY2027.XLSX": {2026},
    # Covers Jan-2025 to Aug-2026, but owns 2026 ONLY. All twelve months of 2025
    # are already loaded from CY2024-2025.XLSX (verified 2026-09-20: 148,778 rows,
    # 2025-01..2025-12, including a complete 2025-07 at 13,667 and 2025-08 at
    # 13,061 — identical to this file's counts), so 2025 must be excluded HERE.
    #
    # It cannot be excluded by the month allow-list: CY_FILE_MONTHS is year-blind,
    # so {7, 8} selects Jul/Aug of *both* years and re-adds 2025-07 + 2025-08.
    # Setting {2025, 2026} returned 565,074 rows against an expected 538,346; the
    # 26,728-row excess was exactly 2025-07 + 2025-08. Keep this year set at
    # {2026} or that duplication returns.
    "CY2025till31082026.XLSX": {2026},
}
# Optional (year, month) allow-list per file. None = all months in owned years.
CY_FILE_MONTHS: dict[str, Optional[set[int]]] = {
    "sales_2026tillApril.XLSX": {1, 2, 3},
    "Q1FY2027.XLSX": {4, 5, 6},
    # Months 7-8 = Jul/Aug, the only two 2026 months missing from the files above.
    # Read together with the {2026} year set on the line above: month {7, 8} with
    # year {2025, 2026} double-counts Jul/Aug 2025. Both must hold.
    "CY2025till31082026.XLSX": {7, 8},
}
CY_FILES = [RAW_SALES_DIR / name for name in CY_FILE_YEARS]

# SAP/PBI fig-key column in the CY export (gps_v2_fig_key.md backlog #2) —
# ingested directly when the export carries it; otherwise fig_key comes from
# the parts_catalog_dimension join in _enrich_fig_key().
SAP_FIG_KEY_COLUMNS = ("FIG KEY CLASSIFICATION", "Fig Key Classification", "FIG KEY")

def _pick_billing_sheet(path: Path) -> Union[str, int]:
    xl = pd.ExcelFile(path, engine="openpyxl")
    for name in xl.sheet_names:
        header = pd.read_excel(path, sheet_name=name, nrows=0, engine="openpyxl")
        if "Billing Date" in header.columns:
            return name
    return 0


def load_cy_file(path: Path) -> pd.DataFrame:
    sheet = _pick_billing_sheet(path)
    df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]

    out = pd.DataFrame()
    if "Billing Date" in df.columns:
        out["billing_date"] = df["Billing Date"]
    if "DB" in df.columns:
        db = df["DB"].astype(str).str.strip()
        out["sold_to"] = db.where(db.str.lower().isin(["nan", "none", ""]), pd.NA)
    if "Sold-to pt" in df.columns:
        out["sold_to_sap"] = pd.to_numeric(df["Sold-to pt"], errors="coerce")
    if "Payer" in df.columns:
        payer = df["Payer"].astype(str).str.strip()
        payer = payer.where(~payer.str.lower().isin(["nan", "none", ""]), pd.NA)
        if "sold_to" not in out.columns:
            out["sold_to"] = payer
        else:
            out["sold_to"] = out["sold_to"].fillna(payer)
    # ISZE CY exports: column "Material" = PN (numeric); "Material Number" = description text
    if "Material" in df.columns:
        out["part_number"] = df["Material"]
    elif "Material Number" in df.columns:
        out["part_number"] = df["Material Number"]
    for desc_col in ("Material Number", "Material Description", "Material description"):
        if desc_col in df.columns:
            out["description"] = df[desc_col]
            break
    if "Billed Quantity" in df.columns:
        out["billed_qty"] = df["Billed Quantity"]
    elif "QUANTITY" in df.columns:
        # Q1FY2027-style extract
        out["billed_qty"] = df["QUANTITY"]
    if "Net value" in df.columns:
        out["net_sales_value"] = df["Net value"]
    elif "EUR Amount" in df.columns:
        out["net_sales_value"] = df["EUR Amount"]
    elif "Net price" in df.columns:
        out["net_sales_value"] = df["Net price"]
    if "SaTy" in df.columns:
        out["saty"] = df["SaTy"].astype(str).str.strip().str.upper()
        out.loc[out["saty"].str.lower().isin(["nan", "none", ""]), "saty"] = pd.NA
    for fig_col in SAP_FIG_KEY_COLUMNS:
        if fig_col in df.columns:
            fig = df[fig_col].astype(str).str.strip()
            out["fig_key"] = fig.where(~fig.str.lower().isin(["nan", "none", ""]), pd.NA)
            out["fig_key_source"] = "sap"
            break

    return out


def _enrich_fig_key(out: pd.DataFrame) -> pd.DataFrame:
    """Fill fig_key from parts_catalog_dimension where the SAP export had none.

    Catalog PNs carry leading zeros; sales_fact PNs are already stripped, so
    normalise the catalog side before joining. Rows the catalog does not cover
    keep fig_key = NA (checked by verify_derived_pipeline sales_fact.fig_key).
    """
    catalog_parquet = DERIVED_DIR / "parts_catalog_dimension.parquet"
    catalog_csv = DERIVED_DIR / "parts_catalog_dimension.csv"
    if catalog_parquet.exists():
        cat = pd.read_parquet(catalog_parquet, columns=["part_number", "fig_key"])
    elif catalog_csv.exists():
        cat = pd.read_csv(catalog_csv, usecols=["part_number", "fig_key"], dtype=str)
    else:
        print("WARN: parts_catalog_dimension missing — fig_key left empty where no SAP column")
        if "fig_key" not in out.columns:
            out["fig_key"] = pd.NA
            out["fig_key_source"] = pd.NA
        return out

    cat = cat.dropna(subset=["fig_key"]).copy()
    cat["_pn_norm"] = cat["part_number"].astype(str).str.strip().str.lstrip("0")
    cat = cat.drop_duplicates(subset="_pn_norm", keep="first")
    fig_map = cat.set_index("_pn_norm")["fig_key"]

    pn_norm = out["part_number"].astype(str).str.strip().str.lstrip("0")
    catalog_fig = pn_norm.map(fig_map)

    if "fig_key" not in out.columns:
        out["fig_key"] = catalog_fig
        out["fig_key_source"] = pd.NA
    else:
        out["fig_key"] = out["fig_key"].fillna(catalog_fig)
    out.loc[out["fig_key"].notna() & out["fig_key_source"].isna(), "fig_key_source"] = "catalog"

    covered = out["fig_key"].notna().sum()
    print(f"  fig_key coverage: {covered:,}/{len(out):,} rows ({covered / len(out) * 100:.1f}%)")
    return out


def main() -> int:
    frames = []
    for path in CY_FILES:
        if not path.exists():
            print(f"SKIP (missing): {path}")
            continue
        print(f"Loading {path.name} …", flush=True)
        chunk = load_cy_file(path)
        owned_years = CY_FILE_YEARS.get(path.name)
        owned_months = CY_FILE_MONTHS.get(path.name)
        if owned_years and "billing_date" in chunk.columns:
            bd = pd.to_datetime(chunk["billing_date"], dayfirst=True, errors="coerce")
            chunk_year = bd.dt.year
            before = len(chunk)
            mask = chunk_year.isin(owned_years)
            if owned_months is not None:
                mask = mask & bd.dt.month.isin(owned_months)
            chunk = chunk[mask].reset_index(drop=True)
            dropped = before - len(chunk)
            if dropped:
                month_note = f", months {sorted(owned_months)}" if owned_months else ""
                print(
                    f"  -> {len(chunk):,} rows (dropped {dropped:,} outside owned years "
                    f"{sorted(owned_years)}{month_note})",
                    flush=True,
                )
            else:
                print(f"  -> {len(chunk):,} rows", flush=True)
        else:
            print(f"  -> {len(chunk):,} rows", flush=True)
        frames.append(chunk)

    if not frames:
        print("No CY files found under", RAW_SALES_DIR)
        return 1

    out = pd.concat(frames, ignore_index=True)
    if "sold_to" in out.columns:
        out["sold_to"] = out["sold_to"].astype(str).str.strip()
        out.loc[out["sold_to"].str.lower().isin(["nan", "none", ""]), "sold_to"] = pd.NA
    if "sold_to_sap" in out.columns:
        out["sold_to_sap"] = pd.to_numeric(out["sold_to_sap"], errors="coerce")
    out["billing_date"] = pd.to_datetime(out["billing_date"], dayfirst=True, errors="coerce")
    out["year"] = out["billing_date"].dt.year.astype("Int64")
    # Drop aggregate / footer rows from the source Excels — they have no date
    # and show up as "UNMAPPED" downstream. Confirmed 2026-05-22: row 287451 was
    # the exact 2023+2024 grand total (2,462,342 qty / €65,121,781).
    pre = len(out)
    out = out[out["year"].notna()].reset_index(drop=True)
    dropped = pre - len(out)
    if dropped:
        print(f"  Dropped {dropped} aggregate/footer row(s) with no billing_date")
    out["net_sales_value"] = pd.to_numeric(out["net_sales_value"], errors="coerce").fillna(0)
    out["billed_qty"] = pd.to_numeric(out["billed_qty"], errors="coerce").fillna(0)
    if "part_number" not in out.columns:
        print("ERROR: no part_number column — check CY export has 'Material' (PN)")
        return 1
    pn_num = pd.to_numeric(out["part_number"], errors="coerce")

    def _pn_to_str(v, raw):
        if pd.notna(v):
            try:
                return str(int(v))
            except (ValueError, OverflowError):
                pass
        s = str(raw).strip() if pd.notna(raw) else ""
        return s if s.lower() not in ("nan", "none") else ""

    out["part_number"] = [
        _pn_to_str(pn_num.iloc[i], out["part_number"].iloc[i]) for i in range(len(out))
    ]
    # Legacy alias for loaders that still read `material`
    out["material"] = out["part_number"]
    if "description" in out.columns:
        out["description"] = out["description"].astype(str).where(
            out["description"].notna(), None
        )
    out = _enrich_fig_key(out)

    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    out.to_parquet(SALES_FACT_PARQUET, index=False)
    print(f"Wrote {len(out):,} rows -> {SALES_FACT_PARQUET}")
    print("Next: streamlit run app.py  (PRISM will prefer this file)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
