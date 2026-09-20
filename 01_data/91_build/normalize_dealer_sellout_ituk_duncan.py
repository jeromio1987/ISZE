"""Duncan ITUK Dealer Purchases by PN → network long CSVs.

Does not replace dealer×PN SSOT (`dealer_sellout_long_ITUK_CY2025.csv`).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "01_data" / "12_raw" / "dealer_sales" / "ITUK" / "ITUK_Dealer_Purchases_by_PN_2023_2026YTD_Aug.xlsx"
OUT_DIR = ROOT / "01_data" / "00_derived"
SHEET = "Dealer Purchases by Part Number"
MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}


def normalize_pn(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    token = str(value).strip().split()[0].split("-")[0]
    digits = re.sub(r"\D", "", token)
    if len(digits) < 8:
        return None
    return digits.zfill(10)


def col_map(raw: pd.DataFrame) -> list[tuple[int, int, int]]:
    year_row = raw.iloc[9]
    month_row = raw.iloc[10]
    current_year = None
    out = []
    for j in range(1, raw.shape[1]):
        y = year_row.iloc[j]
        if pd.notna(y):
            try:
                current_year = int(float(y))
            except (TypeError, ValueError):
                pass
        m = month_row.iloc[j]
        if m is None or (isinstance(m, float) and pd.isna(m)):
            continue
        name = str(m).strip()
        if name not in MONTHS or current_year is None:
            continue
        if isinstance(current_year, str):
            continue
        out.append((j, current_year, MONTHS[name]))
    return out


def parse(path: Path) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name=SHEET, header=None)
    cols = col_map(raw)
    rows = []
    for i in range(11, len(raw)):
        cell = raw.iloc[i, 0]
        pn = normalize_pn(cell)
        if not pn:
            continue
        desc = str(cell).split(" - ", 1)[1].strip() if isinstance(cell, str) and " - " in cell else ""
        for j, year, month in cols:
            qty = pd.to_numeric(raw.iloc[i, j], errors="coerce")
            if pd.isna(qty) or float(qty) == 0:
                continue
            rows.append(
                {
                    "distributor_code": "ITUK",
                    "source_file": path.name,
                    "grain": "network_pn",
                    "year": year,
                    "period": f"{year}-{month:02d}",
                    "period_grain": "month",
                    "part_number": pn,
                    "part_number_raw": str(cell).split(" - ", 1)[0].strip() if isinstance(cell, str) else pn,
                    "description": desc,
                    "qty": float(qty),
                    "dealer_name": "All",
                    "vehicle_scope": "CV",
                    "flags": "duncan_network_companion",
                }
            )
    return pd.DataFrame(rows)


def year_rows(month_df: pd.DataFrame) -> pd.DataFrame:
    keys = [
        "distributor_code",
        "source_file",
        "grain",
        "year",
        "part_number",
        "part_number_raw",
        "description",
        "dealer_name",
        "vehicle_scope",
        "flags",
    ]
    g = month_df.groupby(keys, as_index=False)["qty"].sum()
    g["period"] = g["year"].astype(str)
    g["period_grain"] = "year"
    return g


def write_year(df: pd.DataFrame, year: int, name: str) -> Path:
    sub = df[df["year"] == year]
    out = pd.concat([year_rows(sub), sub], ignore_index=True)
    path = OUT_DIR / name
    out.to_csv(path, index=False)
    print(f"ok {path.name} rows={len(out)} qty_year={sub['qty'].sum():,.0f}")
    return path


def main() -> int:
    if not SRC.exists():
        print(f"MISSING {SRC}", file=sys.stderr)
        return 1
    df = parse(SRC)
    if df.empty:
        print("no qty rows", file=sys.stderr)
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_year(df, 2023, "dealer_sellout_long_ITUK_CY2023.csv")
    write_year(df, 2024, "dealer_sellout_long_ITUK_CY2024.csv")
    write_year(df, 2025, "dealer_sellout_long_ITUK_network_CY2025.csv")
    ytd = df[df["year"] == 2026]
    write_year(ytd, 2026, "dealer_sellout_long_ITUK_CY2026YTD.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
