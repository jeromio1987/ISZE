"""Normalize Duncan ITUK Dealer Purchases by PN → canonical long CSV.

Source sheet: 'Dealer Purchases by Part Number'
  - Pivot: Quantity Supplied × calendar year × month name columns
  - Row labels: '{PN} - {description}' (network aggregate; Customer Name filter = All)
  - No invoice-date column; no EUR; no dealer dimension on the main sheet
  - Side sheets '8982169220' / '8982447940' = dealer × calendar year (qty only)
    for two brake-pad PNs (not month grain)

Do NOT use sheet 'Part Number Extraction' as primary: duplicate PN rows
(incl. DE* exchange-surcharge lines) inflate qty (~4× on 2023).

Period definition (documented, not invented):
  Calendar months of Quantity Supplied under Product Division 40-PARTS,
  through close of trading August 2026 (Duncan mail 2026-09-04).
  Not fiscal; not line-level invoice date.

Dealer × PN × month for full catalog remains the older file:
  Sales to Dealers_ITUK_CY2025.xlsx → dealer_sellout_long_ITUK_CY2025.csv
  (this adapter does not overwrite that dealer-grain long).

Outputs under 01_data/00_derived/:
  - dealer_sellout_long_ITUK_CY2023.csv          (network_pn, month+year)
  - dealer_sellout_long_ITUK_CY2024.csv
  - dealer_sellout_long_ITUK_network_CY2025.csv  (network companion; dealer SSOT unchanged)
  - dealer_sellout_long_ITUK_CY2026YTD.csv       (Jan–Aug, partial_year)
  - dealer_sellout_ITUK_pn_month_2023_2026YTD.csv
  - dealer_sellout_ITUK_dealer_year_2pn_sample.csv
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

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
MONTH_NUM = {m: i for i, m in enumerate(MONTHS, start=1)}

MAIN_SHEET = "Dealer Purchases by Part Number"
SAMPLE_PN_SHEETS = ("8982169220", "8982447940")


def normalize_pn(raw) -> tuple[str | None, str]:
    s = str(raw).strip() if raw is not None else ""
    digits = re.sub(r"\D", "", s)
    if len(digits) < 8:
        return None, s
    return digits.zfill(10), s


def parse_row_label(label) -> tuple[str | None, str, str]:
    """Return (pn, part_number_raw_token, description)."""
    s = str(label).strip() if label is not None else ""
    if not s or s.lower().startswith("grand"):
        return None, "", ""
    if " - " in s:
        token, desc = s.split(" - ", 1)
    else:
        token, desc = s, ""
    pn, raw = normalize_pn(token)
    return pn, raw or token.strip(), desc.strip()


def _month_col_map(year_row, month_row, col_start: int, col_end_exclusive: int) -> dict[int, str]:
    cur_year = None
    out: dict[int, str] = {}
    for j in range(col_start, col_end_exclusive):
        y = year_row[j] if j < len(year_row) else None
        m = month_row[j] if j < len(month_row) else None
        if y is not None and str(y).strip().isdigit():
            cur_year = int(str(y).strip())
        mname = str(m).strip() if m is not None else ""
        if cur_year and mname in MONTH_NUM:
            out[j] = f"{cur_year}-{MONTH_NUM[mname]:02d}"
    return out


def write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {path.name} rows={len(rows)}")


def normalize_duncan(src: Path, out_dir: Path) -> dict[str, Path]:
    import openpyxl

    if not src.exists():
        raise SystemExit(f"Missing source: {src}")

    wb = openpyxl.load_workbook(src, read_only=True, data_only=True)
    if MAIN_SHEET not in wb.sheetnames:
        raise SystemExit(f"Expected sheet {MAIN_SHEET!r}: {wb.sheetnames}")

    ws = wb[MAIN_SHEET]
    header_rows = list(ws.iter_rows(min_row=1, max_row=11, values_only=True))
    year_row = header_rows[9]
    month_row = header_rows[10]
    # cols 1..44 = Jan2023..Aug2026; col 45 = Grand Total (skip)
    col_period = _month_col_map(year_row, month_row, 1, 45)
    if len(col_period) < 40:
        raise SystemExit(f"Unexpected month-col map size {len(col_period)}: {col_period}")

    # (year, period, pn) -> qty; also track desc/raw
    month_qty: dict[tuple[int, str, str], float] = defaultdict(float)
    year_qty: dict[tuple[int, str], float] = defaultdict(float)
    desc_vote: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    raw_first: dict[str, str] = {}
    rows_in = 0
    skip_label = 0
    blank_pn = 0

    for row in ws.iter_rows(min_row=12, values_only=True):
        rows_in += 1
        pn, raw, desc = parse_row_label(row[0])
        if pn is None:
            if row[0] is not None and str(row[0]).strip():
                skip_label += 1
            else:
                blank_pn += 1
            continue
        if pn not in raw_first:
            raw_first[pn] = raw
        if desc:
            desc_vote[pn][desc] += 1
        for j, period in col_period.items():
            try:
                q = float(row[j] or 0)
            except (TypeError, ValueError):
                q = 0.0
            if q == 0:
                continue
            year = int(period[:4])
            month_qty[(year, period, pn)] += q
            year_qty[(year, pn)] += q

    # --- sample dealer × year sheets (2 PNs) ---
    dealer_year_rows: list[dict] = []
    for sn in SAMPLE_PN_SHEETS:
        if sn not in wb.sheetnames:
            continue
        wsd = wb[sn]
        # year headers on row 10 (1-index), data from row 11
        hdr = list(wsd.iter_rows(min_row=1, max_row=10, values_only=True))
        year_hdr = hdr[9]
        year_cols: dict[int, int] = {}
        for j, v in enumerate(year_hdr):
            if v is None:
                continue
            s = str(v).strip()
            if s.isdigit() and len(s) == 4:
                year_cols[j] = int(s)
        pn_sheet, _ = normalize_pn(sn)
        for row in wsd.iter_rows(min_row=11, values_only=True):
            dealer = row[0]
            if dealer is None:
                continue
            dname = str(dealer).strip()
            if not dname or dname.lower().startswith("grand"):
                continue
            for j, y in year_cols.items():
                try:
                    q = float(row[j] or 0)
                except (TypeError, ValueError):
                    q = 0.0
                if q == 0:
                    continue
                dealer_year_rows.append(
                    {
                        "distributor_code": "ITUK",
                        "source_file": src.name,
                        "grain": "dealer_pn",
                        "year": y,
                        "period": str(y),
                        "period_grain": "year",
                        "part_number": pn_sheet or sn,
                        "part_number_raw": sn,
                        "description": "",
                        "qty": q,
                        "dealer_name": dname,
                        "vehicle_scope": "",
                        "flags": "qty_only|sample_pn_only|no_month_grain",
                    }
                )

    wb.close()

    def best_desc(pn: str) -> str:
        votes = desc_vote.get(pn) or {}
        if not votes:
            return ""
        return max(votes.items(), key=lambda kv: kv[1])[0]

    outs: dict[str, Path] = {}
    src_name = src.name

    # Split long facts by calendar year
    by_year_rows: dict[int, list[dict]] = defaultdict(list)
    pn_month_rows: list[dict] = []

    for (year, period, pn), qty in sorted(month_qty.items()):
        flags = "qty_only"
        if year == 2026:
            flags = "qty_only|partial_year"
        row = {
            "distributor_code": "ITUK",
            "source_file": src_name,
            "grain": "network_pn",
            "year": year,
            "period": period,
            "period_grain": "month",
            "part_number": pn,
            "part_number_raw": raw_first.get(pn, pn),
            "description": best_desc(pn),
            "qty": qty,
            "dealer_name": "",
            "vehicle_scope": "",
            "flags": flags,
        }
        by_year_rows[year].append(row)
        pn_month_rows.append(row)

    for (year, pn), qty in sorted(year_qty.items()):
        if qty == 0:
            continue
        flags = "qty_only"
        if year == 2026:
            flags = "qty_only|partial_year"
        by_year_rows[year].append(
            {
                "distributor_code": "ITUK",
                "source_file": src_name,
                "grain": "network_pn",
                "year": year,
                "period": str(year),
                "period_grain": "year" if year < 2026 else "ytd",
                "part_number": pn,
                "part_number_raw": raw_first.get(pn, pn),
                "description": best_desc(pn),
                "qty": qty,
                "dealer_name": "",
                "vehicle_scope": "",
                "flags": flags,
            }
        )

    name_map = {
        2023: "dealer_sellout_long_ITUK_CY2023.csv",
        2024: "dealer_sellout_long_ITUK_CY2024.csv",
        2025: "dealer_sellout_long_ITUK_network_CY2025.csv",  # do not overwrite dealer SSOT
        2026: "dealer_sellout_long_ITUK_CY2026YTD.csv",
    }
    for year, fname in name_map.items():
        rows = by_year_rows.get(year, [])
        if not rows:
            print(f"skip empty year {year}")
            continue
        path = out_dir / fname
        write_rows(path, rows)
        outs[fname] = path

    # PN × month rollup (all years, month grain only)
    pn_month_path = out_dir / "dealer_sellout_ITUK_pn_month_2023_2026YTD.csv"
    write_rows(pn_month_path, pn_month_rows)
    outs[pn_month_path.name] = pn_month_path

    if dealer_year_rows:
        dpath = out_dir / "dealer_sellout_ITUK_dealer_year_2pn_sample.csv"
        write_rows(dpath, dealer_year_rows)
        outs[dpath.name] = dpath

    # QA summary (counts only — no line dump)
    print("--- QA ---")
    print(f"source={src_name}")
    print(f"main_rows_scanned={rows_in} skip_label={skip_label} blank_label={blank_pn}")
    print(f"month_cols={len(col_period)} periods={min(col_period.values())}..{max(col_period.values())}")
    print(f"unique_pn_month={len({(p, pn) for (_, p, pn) in month_qty})} unique_pn={len(raw_first)}")
    for y in sorted({yy for yy, _, _ in month_qty}):
        q = sum(v for (yy, _, _), v in month_qty.items() if yy == y)
        nper = len({p for (yy, p, _) in month_qty if yy == y})
        print(f"  year={y} month_qty_sum={q:,.0f} periods={nper}")
    print(f"dealer_year_sample_rows={len(dealer_year_rows)}")
    return outs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--src",
        type=Path,
        default=Path(
            r"C:\Users\jerom\Desktop\claude\ISZE\01_data\12_raw\dealer_sales\ITUK"
            r"\ITUK_Dealer_Purchases_by_PN_2023_2026YTD_Aug.xlsx"
        ),
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"),
    )
    args = ap.parse_args()
    normalize_duncan(args.src, args.out_dir)


if __name__ == "__main__":
    main()
