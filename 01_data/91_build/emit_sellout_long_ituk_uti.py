# -*- coding: utf-8 -*-
"""Emit dealer_sellout_long_*.csv for ITUK + UTI from existing prism loaders."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pandas as pd

PRISM = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism")
sys.path.insert(0, str(PRISM))

from config import DERIVED_DIR  # noqa: E402
from modules.dealer_sales_loader import (  # noqa: E402
    MONTHS,
    load_ituk_dealer_sales,
    load_uti_part_sales,
)
from modules.dealer_sales_loader import UTI_DIR  # noqa: E402

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

MONTH_NUM = {m: i for i, m in enumerate(MONTHS, start=1)}


def write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {path.name} rows={len(rows)}")


def emit_ituk(year: int = 2025) -> None:
    df = load_ituk_dealer_sales(year)
    if df.empty:
        print("ITUK empty — skip")
        return
    src = str(df["data_source"].iloc[0])
    rows: list[dict] = []
    for _, r in df.iterrows():
        base = {
            "distributor_code": "ITUK",
            "source_file": src,
            "grain": "dealer_pn",
            "year": year,
            "part_number": r["part_number"],
            "part_number_raw": r["part_number"],
            "description": "",
            "dealer_name": r.get("dealer_name", ""),
            "vehicle_scope": "",
            "flags": "",
        }
        qty_y = float(r.get("qty_year") or 0)
        if qty_y > 0:
            rows.append(
                {
                    **base,
                    "period": str(year),
                    "period_grain": "year",
                    "qty": qty_y,
                }
            )
        for m in MONTHS:
            if m not in df.columns:
                continue
            q = float(r.get(m) or 0)
            if q == 0:
                continue
            rows.append(
                {
                    **base,
                    "period": f"{year}-{MONTH_NUM[m]:02d}",
                    "period_grain": "month",
                    "qty": q,
                }
            )
    write_rows(DERIVED_DIR / f"dealer_sellout_long_ITUK_CY{year}.csv", rows)


def emit_uti() -> None:
    """Month rows from each monthly snapshot; year from Dec YTD preferred."""
    paths = sorted(UTI_DIR.glob("UTIPartSales_*.xlsx"))
    month_rows: list[dict] = []
    ytd_rows: list[dict] = []
    for path in paths:
        df, meta = load_uti_part_sales(path)
        if df.empty:
            continue
        ry = meta.get("report_year")
        rm = meta.get("report_month")
        for _, r in df.iterrows():
            pn = r["part_number"]
            base = {
                "distributor_code": "UTI",
                "source_file": path.name,
                "grain": "network_pn",
                "year": int(ry) if ry else "",
                "part_number": pn,
                "part_number_raw": pn,
                "description": "",
                "dealer_name": "",
                "vehicle_scope": "",
                "flags": "",
            }
            qm = float(r.get("qty_month") or 0)
            if ry and rm and qm > 0:
                month_rows.append(
                    {
                        **base,
                        "period": f"{int(ry)}-{int(rm):02d}",
                        "period_grain": "month",
                        "qty": qm,
                    }
                )
            if "12_YTD" in path.name or (rm == 12 and "YTD" in path.name.upper()):
                qy = float(r.get("qty_ytd") or 0)
                if qy > 0 and ry:
                    ytd_rows.append(
                        {
                            **base,
                            "period": str(int(ry)),
                            "period_grain": "year",
                            "qty": qy,
                        }
                    )
    # CY2025 long = year rows from Dec YTD + month rows for 2025
    rows_2025 = [r for r in month_rows if str(r["period"]).startswith("2025-")]
    rows_2025.extend(ytd_rows)
    if rows_2025:
        write_rows(DERIVED_DIR / "dealer_sellout_long_UTI_CY2025.csv", rows_2025)
    rows_2026 = [r for r in month_rows if str(r["period"]).startswith("2026-")]
    if rows_2026:
        write_rows(DERIVED_DIR / "dealer_sellout_long_UTI_CY2026YTD.csv", rows_2026)


if __name__ == "__main__":
    emit_ituk(2025)
    emit_uti()
