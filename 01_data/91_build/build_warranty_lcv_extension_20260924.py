"""
LCV (pickup) warranty claim extension — October 2025 to August 2026.
=====================================================================
Takes the newly uploaded network-wide LCV claim export and writes it in the
SAME schema as the canonical grain (01_data/00_derived/warranty_raw_grain.csv),
so the two can be joined without a translation layer.

Source (read-only):
  01_data/WArranty Data LCV_102025_082026.xlsx
      sheet 'WA Data 102026-082026', 30,680 claim lines, AssessMonth 202510-202608
      29 countries, no Israel rows (Israel pickup warranty has its own file).

Output:
  01_data/00_derived/warranty_lcv_extension_202510_202608.csv

Rules copied from 01_data/91_build/extract_warranty_all.py so the new rows are
comparable with the ones already in the master:
  - skip a line with no part number, or zero pieces
  - currency from `CurrencyParts`; JPY converted at the annual average, USD via
    PartsAmount_USD, everything else taken as EUR
  - value basis is `AdmitPartsCost` (claim-admitted price), the same basis the
    existing LCV rows use

Writes nothing else. Does not touch the master, the json, or the FY file.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import openpyxl

DATA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data")
SRC = DATA / "WArranty Data LCV_102025_082026.xlsx"
OUT = DATA / "00_derived" / "warranty_lcv_extension_202510_202608.csv"

# annual averages, identical to extract_warranty_all.py
JPY_EUR: dict[int, float] = {2024: 164.0, 2025: 162.0, 2026: 158.0}
USD_EUR: dict[int, float] = {2024: 1.08, 2025: 1.08, 2026: 1.10}

GRAIN_FIELDS = [
    "year", "assess_month", "segment", "db_name", "db_code",
    "country", "part_no", "part_desc", "qty", "claim_eur", "currency_raw",
]


def _to_eur(amount: float, ccy: str, year: int) -> float:
    if ccy == "EUR":
        return amount
    if ccy == "JPY":
        return amount / JPY_EUR.get(year, 162.0)
    if ccy == "USD":
        return amount / USD_EUR.get(year, 1.08)
    return amount


def extract(path: Path) -> list[dict]:
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    out: list[dict] = []
    for sname in wb.sheetnames:
        ws = wb[sname]
        it = ws.iter_rows(values_only=True)
        try:
            hdr = list(next(it))
        except StopIteration:
            continue
        I = {str(h): i for i, h in enumerate(hdr) if h is not None}
        if "AssessMonth" not in I:
            continue

        def v(r, col):
            i = I.get(col)
            return r[i] if i is not None and i < len(r) else None

        for r in it:
            assess = str(v(r, "AssessMonth") or "").strip().split(".")[0]
            if len(assess) < 6:
                continue
            year = int(assess[:4])
            month = assess[:6]

            pn = str(v(r, "PartsNo") or "").strip()
            if not pn or pn in ("None", "0", ""):
                continue
            qty_raw = v(r, "Pieces")
            qty = float(qty_raw) if isinstance(qty_raw, (int, float)) else 0.0
            if qty == 0:
                continue

            ccy = str(v(r, "CurrencyParts") or "EUR").strip()
            raw_cost = v(r, "AdmitPartsCost")
            admit_cost = float(raw_cost) if isinstance(raw_cost, (int, float)) else 0.0
            raw_usd = v(r, "PartsAmount_USD")
            admit_usd = float(raw_usd) if isinstance(raw_usd, (int, float)) else 0.0

            if ccy == "USD":
                claim_eur = admit_usd / USD_EUR.get(year, 1.08)
            else:
                claim_eur = _to_eur(admit_cost, ccy, year)

            out.append({
                "year": year,
                "assess_month": month,
                "segment": "LCV",
                "db_name": str(v(r, "DistributorName") or "").strip(),
                "db_code": str(v(r, "DistributorCode") or "").strip(),
                "country": str(v(r, "CountryName") or "").strip(),
                "part_no": pn,
                "part_desc": str(v(r, "PartsName") or "").strip(),
                "qty": qty,
                "claim_eur": round(claim_eur, 4),
                "currency_raw": ccy,
            })
    wb.close()
    return out


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"source missing: {SRC}")

    rows = extract(SRC)
    print(f"extracted {len(rows):,} LCV claim lines from {SRC.name}")

    by_month: dict[str, float] = defaultdict(float)
    by_month_n: dict[str, int] = defaultdict(int)
    by_db: dict[str, float] = defaultdict(float)
    ccy: dict[str, int] = defaultdict(int)
    for r in rows:
        by_month[r["assess_month"]] += r["claim_eur"]
        by_month_n[r["assess_month"]] += 1
        by_db[r["db_name"]] += r["claim_eur"]
        ccy[r["currency_raw"]] += 1

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=GRAIN_FIELDS)
        w.writeheader()
        w.writerows(rows)

    print(f"\nwritten -> {OUT.name}  ({OUT.stat().st_size:,} bytes)")
    print(f"  months {min(by_month)} .. {max(by_month)}")
    print("\n  by month (EUR):")
    for m in sorted(by_month):
        print(f"    {m}  {by_month[m]:>14,.0f}   {by_month_n[m]:>6} lines")
    print("\n  currency mix:", dict(ccy))
    print("\n  top 12 distributors (EUR):")
    for k, val in sorted(by_db.items(), key=lambda x: -x[1])[:12]:
        print(f"    {k:<42} {val:>14,.0f}")
    print(f"\n  network total: EUR {sum(by_db.values()):,.0f}")
    print(f"generated {datetime.now().isoformat(timespec='seconds')}")


if __name__ == "__main__":
    main()
