"""Normalize IUK Monthly Demand → canonical dealer-sellout long CSV.

Native shape (per sheet):
  Part Number | Desc | JAN…DEC | Average|Monthly Average | Total|Yearly Total

Sheets:
  - '2025 - Complete' → full CY2025
  - '2026 - To July end' → CY2026 YTD (Jan–Jul; Aug–Dec zero)

Target schema: 01_data/12_raw/dealer_sales/DEALER_SELL_OUT.md
IUK = UK LCV (D-Max) — distinct from ITUK (UK CV trucks).
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

MONTH_COLS = [
    ("JAN", "01"),
    ("FEB", "02"),
    ("MAR", "03"),
    ("APR", "04"),
    ("MAY", "05"),
    ("JUN", "06"),
    ("JULY", "07"),
    ("AUG", "08"),
    ("SEP", "09"),
    ("OCT", "10"),
    ("NOV", "11"),
    ("DEC", "12"),
]

FIELDS = [
    "distributor_code",
    "source_file",
    "grain",
    "year",
    "period",
    "period_grain",
    "part_number",
    "part_number_raw",
    "description",
    "qty",
    "dealer_name",
    "vehicle_scope",
    "flags",
]

SHEET_SPECS = {
    "2025 - Complete": {
        "year": 2025,
        "active_months": 12,
        "flags": "qty_only|lcv_dmax",
        "out_name": "dealer_sellout_long_IUK_CY2025.csv",
    },
    "2026 - To July end": {
        "year": 2026,
        "active_months": 7,
        "flags": "qty_only|lcv_dmax|partial_year",
        "out_name": "dealer_sellout_long_IUK_CY2026YTD.csv",
    },
}


def normalize_pn(raw) -> tuple[str | None, str]:
    s = str(raw).strip() if raw is not None else ""
    digits = re.sub(r"\D", "", s)
    if len(digits) < 8:
        return None, s
    return digits.zfill(10), s


def _header_map(header_row) -> dict[str, int]:
    out: dict[str, int] = {}
    for i, h in enumerate(header_row):
        if h is None:
            continue
        key = str(h).strip().upper()
        out[key] = i
    return out


def normalize_sheet(
    ws,
    *,
    source_file: str,
    year: int,
    active_months: int,
    flags: str,
    distributor_code: str = "IUK",
    vehicle_scope: str = "D-MAX",
) -> list[dict]:
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise SystemExit(f"Empty sheet for year {year}")
    idx = _header_map(rows[0])
    if "PART NUMBER" not in idx:
        raise SystemExit(f"Missing Part Number column: {list(idx)}")

    month_idx: list[tuple[str, int]] = []
    for name, mm in MONTH_COLS:
        if name not in idx:
            raise SystemExit(f"Missing month column {name}: {list(idx)}")
        month_idx.append((f"{year}-{mm}", idx[name]))

    # Total column (ignore Average / Monthly Average)
    total_i = None
    for key in idx:
        if "TOTAL" in key and "AVERAGE" not in key:
            total_i = idx[key]
            break
    if total_i is None:
        raise SystemExit(f"Missing Total column: {list(idx)}")

    out_rows: list[dict] = []
    for r in rows[1:]:
        pn, raw = normalize_pn(r[idx["PART NUMBER"]])
        if not pn:
            continue
        desc = ""
        if "DESC" in idx:
            d = r[idx["DESC"]]
            desc = "" if d is None else str(d).strip()

        months = [(period, float(r[i] or 0)) for period, i in month_idx]
        # Year / YTD total from source Total column (verified = sum of active months)
        year_qty = float(r[total_i] or 0)
        # For partial year, only emit non-future months (zeros after cutoff stay omitted)
        active = months[:active_months]

        base = dict(
            distributor_code=distributor_code,
            source_file=source_file,
            grain="network_pn",
            year=year,
            part_number=pn,
            part_number_raw=raw,
            description=desc,
            dealer_name="",
            vehicle_scope=vehicle_scope,
            flags=flags,
        )
        out_rows.append(
            {
                **base,
                "period": str(year) if active_months == 12 else f"{year}-YTD",
                "period_grain": "year" if active_months == 12 else "ytd",
                "qty": year_qty,
            }
        )
        for period, q in active:
            if q == 0:
                continue
            out_rows.append({**base, "period": period, "period_grain": "month", "qty": q})
    return out_rows


def normalize_iuk(src: Path, out_dir: Path) -> dict[str, tuple[int, int, Path]]:
    import openpyxl

    wb = openpyxl.load_workbook(src, read_only=True, data_only=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, tuple[int, int, Path]] = {}
    for sheet_name, spec in SHEET_SPECS.items():
        if sheet_name not in wb.sheetnames:
            raise SystemExit(f"Missing sheet {sheet_name!r} in {src.name}: {wb.sheetnames}")
        rows = normalize_sheet(
            wb[sheet_name],
            source_file=src.name,
            year=spec["year"],
            active_months=spec["active_months"],
            flags=spec["flags"],
        )
        out = out_dir / spec["out_name"]
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        n_year = sum(1 for r in rows if r["period_grain"] in ("year", "ytd"))
        n_month = sum(1 for r in rows if r["period_grain"] == "month")
        summary[sheet_name] = (n_year, n_month, out)
    wb.close()
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--src",
        type=Path,
        default=Path("01_data/12_raw/dealer_sales/IUK/IUK_Monthly_Demand_2025_2026YTD_July.xlsx"),
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("01_data/00_derived"),
    )
    args = ap.parse_args()
    summary = normalize_iuk(args.src, args.out_dir)
    for sheet, (n_y, n_m, path) in summary.items():
        print(f"{sheet}: wrote {path}  year/ytd_rows={n_y} month_rows={n_m}")


if __name__ == "__main__":
    main()
