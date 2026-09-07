"""Normalize Portugal (Imotors / Astara) sales-to-dealer → canonical long CSV.

Native shape (sheets '2025' and '2026', one row per invoice-date × PN):
  Data da Fatura | Referencia | Sum of Quantidade

Rules:
  - distributor_code = PORTUGAL (Imotors LDA / Astara Portugal) — not billing
  - PN = Referencia
  - qty = Sum of Quantidade (skip zero)
  - period from Data da Fatura (YYYY-MM)
  - grain = network_pn (no dealer dimension in source)
  - qty_only (no EUR in source)
  - 2025 = full CY; 2026 = YTD through Aug (as filed 2026-09-03)

Outputs:
  - dealer_sellout_long_PORTUGAL_CY2025.csv
  - dealer_sellout_long_PORTUGAL_CY2026YTD.csv

Target schema: 01_data/12_raw/dealer_sales/DEALER_SELL_OUT.md
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from datetime import date, datetime
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

SHEETS = {
    "2025": {"year": 2025, "flags": "qty_only", "out_name": "dealer_sellout_long_PORTUGAL_CY2025.csv"},
    "2026": {
        "year": 2026,
        "flags": "qty_only|partial_year",
        "out_name": "dealer_sellout_long_PORTUGAL_CY2026YTD.csv",
    },
}


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


def normalize_portugal(src: Path, out_dir: Path) -> dict[int, Path]:
    import openpyxl

    wb = openpyxl.load_workbook(src, read_only=True, data_only=True)
    for sheet_name in SHEETS:
        if sheet_name not in wb.sheetnames:
            raise SystemExit(f"Expected sheet {sheet_name!r} in {src.name}: {wb.sheetnames}")

    by_year: dict[int, list[dict]] = {2025: [], 2026: []}
    outs: dict[int, Path] = {}

    for sheet_name, spec in SHEETS.items():
        ws = wb[sheet_name]
        it = ws.iter_rows(values_only=True)
        header = next(it)
        idx = {str(h).strip(): i for i, h in enumerate(header) if h is not None}
        required = ["Data da Fatura", "Referencia", "Sum of Quantidade"]
        for col in required:
            if col not in idx:
                raise SystemExit(f"Missing column {col!r} on {sheet_name}: {list(idx)}")

        agg: dict[tuple[str, str], float] = defaultdict(float)
        raw_first: dict[str, str] = {}
        lines_kept = 0
        year = spec["year"]
        flags = spec["flags"]

        for r in it:
            d = parse_date(r[idx["Data da Fatura"]])
            if d is None:
                continue
            if d.year != year:
                continue
            qty = float(r[idx["Sum of Quantidade"]] or 0)
            if qty == 0:
                continue
            pn, raw = normalize_pn(r[idx["Referencia"]])
            if not pn:
                continue
            period = d.strftime("%Y-%m")
            agg[(period, pn)] += qty
            if pn not in raw_first:
                raw_first[pn] = raw
            lines_kept += 1

        year_totals: dict[str, float] = defaultdict(float)
        rows: list[dict] = []
        for (period, pn), q in sorted(agg.items()):
            year_totals[pn] += q
            rows.append(
                dict(
                    distributor_code="PORTUGAL",
                    source_file=src.name,
                    grain="network_pn",
                    year=year,
                    period=period,
                    period_grain="month",
                    part_number=pn,
                    part_number_raw=raw_first.get(pn, pn),
                    description="",
                    qty=q,
                    dealer_name="",
                    vehicle_scope="unknown",
                    flags=flags,
                )
            )
        for pn, q in sorted(year_totals.items()):
            rows.append(
                dict(
                    distributor_code="PORTUGAL",
                    source_file=src.name,
                    grain="network_pn",
                    year=year,
                    period=str(year) if year == 2025 else f"{year}-YTD",
                    period_grain="year" if year == 2025 else "ytd",
                    part_number=pn,
                    part_number_raw=raw_first.get(pn, pn),
                    description="",
                    qty=q,
                    dealer_name="",
                    vehicle_scope="unknown",
                    flags=flags,
                )
            )

        by_year[year] = rows
        print(
            f"sheet {sheet_name}: lines_kept={lines_kept} "
            f"month_keys={len(agg)} distinct_pn={len(year_totals)} "
            f"rollup_qty={sum(year_totals.values()):.0f}"
        )

    wb.close()
    out_dir.mkdir(parents=True, exist_ok=True)
    for sheet_name, spec in SHEETS.items():
        year = spec["year"]
        path = out_dir / spec["out_name"]
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
            f"rollup_qty={qty_roll:.0f}"
        )
        outs[year] = path
    return outs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--src",
        type=Path,
        default=Path(
            "01_data/12_raw/dealer_sales/PORTUGAL/PORTUGAL_Sales_to_Dealer_2025_2026YTD_Aug.xlsx"
        ),
    )
    ap.add_argument("--out-dir", type=Path, default=Path("01_data/00_derived"))
    args = ap.parse_args()
    src = args.src
    out_dir = args.out_dir
    if not src.is_absolute():
        root = Path(__file__).resolve().parents[2]
        src = root / src
        out_dir = root / out_dir
    normalize_portugal(src, out_dir)


if __name__ == "__main__":
    main()
