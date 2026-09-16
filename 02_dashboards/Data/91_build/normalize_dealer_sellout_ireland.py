"""Normalize Isuzu Ireland (Harris) sales-to-dealer XT → canonical long CSV.

Native shape (Sheet1, one line per despatch/invoice line):
  Item ordered | Item supplied | Description | Orig qty | Qty ordrd | Qty suppld
  | InvoiceDate | OrderDate | DespatchDate

Rules:
  - distributor_code = IRELAND (Harris / Isuzu Ireland) — NOT IUK, NOT IMIE
  - PN = Item supplied (what left the warehouse; ordered may differ on supersession)
  - qty = Qty suppld (skip zero-supplied lines)
  - period from InvoiceDate (YYYY-MM)
  - grain = network_pn (no dealer dimension in source)
  - qty_only (no EUR in source)

Outputs:
  - dealer_sellout_long_IRELAND_CY2025.csv
  - dealer_sellout_long_IRELAND_CY2026YTD.csv

Target schema: 01_data/12_raw/dealer_sales/DEALER_SELL_OUT.md
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from datetime import datetime, date
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


def normalize_pn(raw) -> tuple[str | None, str]:
    s = str(raw).strip() if raw is not None else ""
    digits = re.sub(r"\D", "", s)
    if len(digits) < 8:
        return None, s
    return digits.zfill(10), s


def parse_date(v) -> date | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    s = str(v).strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except ValueError:
            continue
    return None


def normalize_ireland(src: Path, out_dir: Path) -> dict[str, Path]:
    import openpyxl

    wb = openpyxl.load_workbook(src, read_only=True, data_only=True)
    if "Sheet1" not in wb.sheetnames:
        raise SystemExit(f"Expected Sheet1 in {src.name}: {wb.sheetnames}")
    ws = wb["Sheet1"]
    it = ws.iter_rows(values_only=True)
    header = next(it)
    idx = {str(h).strip(): i for i, h in enumerate(header) if h is not None}
    required = ["Item supplied", "Description", "Qty suppld", "InvoiceDate"]
    for col in required:
        if col not in idx:
            raise SystemExit(f"Missing column {col!r}: {list(idx)}")

    # key: (year, period_yyyy_mm, pn) -> qty, raw, desc
    agg: dict[tuple[int, str, str], dict] = {}
    desc_vote: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    raw_first: dict[str, str] = {}
    supersession_lines = 0
    lines_kept = 0

    ord_i = idx.get("Item ordered")
    for r in it:
        d = parse_date(r[idx["InvoiceDate"]])
        if d is None:
            continue
        qty = float(r[idx["Qty suppld"]] or 0)
        if qty == 0:
            continue
        pn, raw = normalize_pn(r[idx["Item supplied"]])
        if not pn:
            continue
        if ord_i is not None and str(r[ord_i] or "").strip() != str(r[idx["Item supplied"]] or "").strip():
            supersession_lines += 1
        period = d.strftime("%Y-%m")
        year = d.year
        key = (year, period, pn)
        if key not in agg:
            agg[key] = {"qty": 0.0}
            if pn not in raw_first:
                raw_first[pn] = raw
        agg[key]["qty"] += qty
        desc = "" if r[idx["Description"]] is None else str(r[idx["Description"]]).strip()
        if desc:
            desc_vote[pn][desc] += 1
        lines_kept += 1
    wb.close()

    def best_desc(pn: str) -> str:
        votes = desc_vote.get(pn) or {}
        if not votes:
            return ""
        return max(votes.items(), key=lambda kv: kv[1])[0]

    flags_2025 = "qty_only|pn_item_supplied"
    flags_2026 = "qty_only|pn_item_supplied|partial_year"

    by_year: dict[int, list[dict]] = {2025: [], 2026: []}
    # month rows
    year_totals: dict[tuple[int, str], float] = defaultdict(float)
    for (year, period, pn), payload in sorted(agg.items()):
        if year not in by_year:
            continue
        flags = flags_2025 if year == 2025 else flags_2026
        q = payload["qty"]
        year_totals[(year, pn)] += q
        by_year[year].append(
            dict(
                distributor_code="IRELAND",
                source_file=src.name,
                grain="network_pn",
                year=year,
                period=period,
                period_grain="month",
                part_number=pn,
                part_number_raw=raw_first.get(pn, pn),
                description=best_desc(pn),
                qty=q,
                dealer_name="",
                vehicle_scope="unknown",
                flags=flags,
            )
        )

    # year / ytd rollups
    for (year, pn), q in sorted(year_totals.items()):
        if year not in by_year:
            continue
        flags = flags_2025 if year == 2025 else flags_2026
        by_year[year].append(
            dict(
                distributor_code="IRELAND",
                source_file=src.name,
                grain="network_pn",
                year=year,
                period=str(year) if year == 2025 else f"{year}-YTD",
                period_grain="year" if year == 2025 else "ytd",
                part_number=pn,
                part_number_raw=raw_first.get(pn, pn),
                description=best_desc(pn),
                qty=q,
                dealer_name="",
                vehicle_scope="unknown",
                flags=flags,
            )
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    outs = {
        2025: out_dir / "dealer_sellout_long_IRELAND_CY2025.csv",
        2026: out_dir / "dealer_sellout_long_IRELAND_CY2026YTD.csv",
    }
    for year, path in outs.items():
        rows = by_year.get(year, [])
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        n_month = sum(1 for r in rows if r["period_grain"] == "month")
        n_roll = sum(1 for r in rows if r["period_grain"] in ("year", "ytd"))
        qty_roll = sum(r["qty"] for r in rows if r["period_grain"] in ("year", "ytd"))
        print(
            f"{path.name}: rows={len(rows)} month={n_month} rollup={n_roll} "
            f"rollup_qty={qty_roll:.0f} supersession_lines_in_source={supersession_lines} "
            f"lines_kept={lines_kept}"
        )
    return outs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--src",
        type=Path,
        default=Path(
            "01_data/12_raw/dealer_sales/IRELAND/IRELAND_Sales_to_Dealer_2025_2026YTD_Jul.xlsx"
        ),
    )
    ap.add_argument("--out-dir", type=Path, default=Path("01_data/00_derived"))
    args = ap.parse_args()
    # Resolve relative to ISZE root if needed
    src = args.src
    out_dir = args.out_dir
    if not src.is_absolute():
        root = Path(__file__).resolve().parents[2]
        src = root / src
        out_dir = root / out_dir
    normalize_ireland(src, out_dir)


if __name__ == "__main__":
    main()
