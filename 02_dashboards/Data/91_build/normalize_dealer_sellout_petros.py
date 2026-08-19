"""Normalize Petros-style qty exports → canonical dealer-sellout long CSV.

Native shape: P/No | Description | SUM | YYYY-Mon … (newest month first)
Target schema: see 01_data/12_raw/dealer_sales/DEALER_SELL_OUT.md
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

MONTH_ABBR = {
    "Jan": "01",
    "Feb": "02",
    "Mar": "03",
    "Apr": "04",
    "May": "05",
    "Jun": "06",
    "Jul": "07",
    "Aug": "08",
    "Sep": "09",
    "Oct": "10",
    "Nov": "11",
    "Dec": "12",
}

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


def normalize_pn(raw) -> tuple[str | None, str]:
    s = str(raw).strip() if raw is not None else ""
    digits = re.sub(r"\D", "", s)
    if len(digits) < 8:
        return None, s
    return digits.zfill(10), s


def parse_month_header(h: str) -> str | None:
    # e.g. 2025-Dec
    m = re.fullmatch(r"(\d{4})-([A-Za-z]{3})", h.strip())
    if not m:
        return None
    year, abbr = m.group(1), m.group(2).title()
    mm = MONTH_ABBR.get(abbr)
    if not mm:
        return None
    return f"{year}-{mm}"


def normalize_petros(
    src: Path,
    out: Path,
    *,
    distributor_code: str = "GREECE",
    vehicle_scope: str = "D-MAX",
    flags: str = "pn_newest_rollup|qty_only",
) -> tuple[int, int]:
    import openpyxl

    wb = openpyxl.load_workbook(src, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    header = [str(h).strip() if h is not None else "" for h in rows[0]]
    idx = {h: i for i, h in enumerate(header)}
    if "P/No" not in idx or "SUM" not in idx:
        raise SystemExit(f"Unexpected header in {src}: {header}")

    month_cols = [(h, parse_month_header(h)) for h in header]
    month_cols = [(h, p) for h, p in month_cols if p]

    years = {int(p[:4]) for _, p in month_cols}
    year = max(years) if years else None

    n_year = n_month = 0
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows[1:]:
            pn, raw = normalize_pn(r[idx["P/No"]])
            if not pn:
                continue
            desc = r[idx["Description"]] if "Description" in idx else ""
            desc = "" if desc is None else str(desc).strip()
            y = year or 0
            base = dict(
                distributor_code=distributor_code,
                source_file=src.name,
                grain="network_pn",
                year=y,
                part_number=pn,
                part_number_raw=raw,
                description=desc,
                dealer_name="",
                vehicle_scope=vehicle_scope,
                flags=flags,
            )
            w.writerow(
                {
                    **base,
                    "period": str(y),
                    "period_grain": "year",
                    "qty": float(r[idx["SUM"]] or 0),
                }
            )
            n_year += 1
            for h, period in month_cols:
                q = float(r[idx[h]] or 0)
                if q == 0:
                    continue
                w.writerow({**base, "period": period, "period_grain": "month", "qty": q})
                n_month += 1
    wb.close()
    return n_year, n_month


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--src",
        type=Path,
        default=Path("01_data/12_raw/dealer_sales/GREECE/Petros_Parts_Sold_Qties_2025.xlsx"),
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("01_data/00_derived/dealer_sellout_long_GREECE_CY2025.csv"),
    )
    ap.add_argument("--distributor-code", default="GREECE")
    ap.add_argument("--vehicle-scope", default="D-MAX")
    args = ap.parse_args()
    n_y, n_m = normalize_petros(
        args.src,
        args.out,
        distributor_code=args.distributor_code,
        vehicle_scope=args.vehicle_scope,
    )
    print(f"wrote {args.out}  year_rows={n_y} month_rows={n_m}")


if __name__ == "__main__":
    main()
