#!/usr/bin/env python3
"""Rank distributors by KPI data completeness (FY Apr 2025 - Mar 2026)."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KPI_FILE = ROOT / "KPI Master File april 2026 (1).xlsx"
OUT_FILE = Path(__file__).resolve().parent / "KPI_distributor_rankings_FY2025-26.xlsx"
OUT_FILE_ALT = Path(__file__).resolve().parent / "KPI_distributor_rankings_FY2025-26_v2.xlsx"

# Fiscal year: Apr 2025 - Mar 2026 (12 months; file uses EN/DE month labels)
FY_MONTHS_RAW = [
    "Apr 25",
    "Mai 25",
    "May 25",
    "Jun 25",
    "Jul 25",
    "Aug 25",
    "Sep 25",
    "Okt 25",
    "Oct 25",
    "Nov 25",
    "Dez 25",
    "Dec 25",
    "Jan 26",
    "Feb 26",
    "Mrz 26",
    "Mar 26",
]
FY_CANON = [
    "Apr 25",
    "May 25",
    "Jun 25",
    "Jul 25",
    "Aug 25",
    "Sep 25",
    "Oct 25",
    "Nov 25",
    "Dec 25",
    "Jan 26",
    "Feb 26",
    "Mar 26",
]
FY_MONTH_COUNT = 12

MONTH_ALIASES = {
    "mai": "may",
    "mrz": "mar",
    "dez": "dec",
    "okt": "oct",
}

# User-requested trio (MOS = Days of Parts in Stock — months-of-supply proxy in master file)
TRIO_KPI = {
    "sales_to_dealer": "Parts Sales DB to DLR in €",
    "fill_rate": "First Fill Rate",
    "mos": "Days of Parts in Stock",
}

MONTHLY_SHEETS = [
    "Parts Handling",
    "Recall C. Rate& Dealer Eff.",
    "Satisfaction & Complaints",
    "Vehicles Serviced & Visits",
    "Vehicle Registration, RM, WE",
    "After Sales Campaigns",
]

PLACEHOLDERS = frozenset({"N/A", "N/D", "NA", "-", "NAN", "?", ""})


def norm_month(header) -> str | None:
    if pd.isna(header):
        return None
    s = str(header).strip()
    if not s:
        return None
    parts = s.split()
    if len(parts) != 2:
        return None
    mon, yr = parts[0].lower(), parts[1]
    mon = MONTH_ALIASES.get(mon, mon)
    mon = mon[:3].capitalize() + mon[3:] if len(mon) > 3 else mon.capitalize()
    if len(mon) == 3:
        mon = mon.capitalize()
    # Apr, May, Jun, ...
    mon_map = {
        "apr": "Apr",
        "may": "May",
        "jun": "Jun",
        "jul": "Jul",
        "aug": "Aug",
        "sep": "Sep",
        "oct": "Oct",
        "nov": "Nov",
        "dec": "Dec",
        "jan": "Jan",
        "feb": "Feb",
        "mar": "Mar",
    }
    key = mon[:3].lower()
    if key not in mon_map:
        return None
    return f"{mon_map[key]} {yr}"


def is_filled(val) -> bool:
    if pd.isna(val):
        return False
    if isinstance(val, (int, float)) and not (isinstance(val, float) and np.isnan(val)):
        return True
    s = str(val).strip()
    if not s:
        return False
    if s.upper() in PLACEHOLDERS:
        return False
    return True


def parse_blocks(df: pd.DataFrame) -> list[dict]:
    blocks: list[dict] = []
    i = 0
    n = len(df)
    while i < n:
        title = df.iloc[i, 0]
        if pd.isna(title):
            i += 1
            continue
        title = str(title).strip()
        hdr = i + 2
        if hdr >= n or str(df.iloc[hdr, 0]).strip() != "Distributor":
            i += 1
            continue
        col_idx: dict[str, int] = {}
        for j, raw in enumerate(df.iloc[hdr, 1:].tolist()):
            m = norm_month(raw)
            if m in FY_CANON:
                col_idx[m] = j + 1
        dist_rows: list[tuple[str, int]] = []
        r = hdr + 1
        while r < n:
            name = df.iloc[r, 0]
            if pd.isna(name) or str(name).strip() == "":
                break
            dist_rows.append((str(name).strip(), r))
            r += 1
        blocks.append({"title": title, "col_idx": col_idx, "dist_rows": dist_rows})
        i = r
    return blocks


def count_fy_cells(df: pd.DataFrame, row: int, col_idx: dict[str, int]) -> int:
    return sum(1 for m in FY_CANON if m in col_idx and is_filled(df.iloc[row, col_idx[m]]))


def main() -> None:
    if not KPI_FILE.exists():
        raise SystemExit(f"Missing KPI file: {KPI_FILE}")

    overall: dict[str, dict] = {}
    trio_detail: dict[str, dict[str, int]] = {}

    for sheet in MONTHLY_SHEETS:
        df = pd.read_excel(KPI_FILE, sheet_name=sheet, header=None)
        for block in parse_blocks(df):
            kpi = block["title"]
            for dist, row in block["dist_rows"]:
                n = count_fy_cells(df, row, block["col_idx"])
                if dist not in overall:
                    overall[dist] = {
                        "filled_cells": 0,
                        "kpi_month_slots": 0,
                        "sheets_with_data": set(),
                    }
                overall[dist]["filled_cells"] += n
                overall[dist]["kpi_month_slots"] += len(block["col_idx"])
                if n > 0:
                    overall[dist]["sheets_with_data"].add(sheet)

                if sheet == "Parts Handling" and kpi in TRIO_KPI.values():
                    key = next(k for k, v in TRIO_KPI.items() if v == kpi)
                    trio_detail.setdefault(dist, {})
                    trio_detail[dist][key] = n

    # Ranking 1 — overall completeness
    rows1 = []
    for dist, d in overall.items():
        slots = d["kpi_month_slots"] or 1
        pct = round(100.0 * d["filled_cells"] / slots, 1)
        rows1.append(
            {
                "Distributor": dist,
                "FY filled cells": d["filled_cells"],
                "FY possible cells": slots,
                "Completeness %": pct,
                "Sheets with any FY data": len(d["sheets_with_data"]),
            }
        )
    rank1 = (
        pd.DataFrame(rows1)
        .sort_values(["FY filled cells", "Completeness %"], ascending=[False, False])
        .reset_index(drop=True)
    )
    rank1.insert(0, "Rank", rank1.index + 1)

    # Ranking 2 — sales to dealer, MOS (days of stock), fill rate
    rows2 = []
    for dist in sorted(set(overall) | set(trio_detail)):
        td = trio_detail.get(dist, {})
        sales_m = td.get("sales_to_dealer", 0)
        mos_m = td.get("mos", 0)
        fill_m = td.get("fill_rate", 0)
        trio_total = sales_m + mos_m + fill_m
        all_three_10 = (
            sales_m >= 10 and mos_m >= 10 and fill_m >= 10
        )
        rows2.append(
            {
                "Distributor": dist,
                "Sales to dealer (months)": sales_m,
                "MOS — Days of parts in stock (months)": mos_m,
                "Fill rate (months)": fill_m,
                "Trio total filled months": trio_total,
                "10/12 on all 3 KPIs": "Yes" if all_three_10 else "No",
            }
        )
    rank2 = (
        pd.DataFrame(rows2)
        .sort_values(
            ["Trio total filled months", "Sales to dealer (months)", "Fill rate (months)"],
            ascending=[False, False, False],
        )
        .reset_index(drop=True)
    )
    rank2.insert(0, "Rank", rank2.index + 1)

    notes = pd.DataFrame(
        [
            {
                "Item": "Period",
                "Detail": "Fiscal year Apr 2025 – Mar 2026 (12 months)",
            },
            {
                "Item": "Source",
                "Detail": str(KPI_FILE.name),
            },
            {
                "Item": "Filled cell",
                "Detail": "Numeric value or non-empty text; excludes N/A, N/D, ?, blank",
            },
            {
                "Item": "Ranking 1",
                "Detail": "Sum of filled FY month cells across all KPI blocks on monthly sheets",
            },
            {
                "Item": "Sales to dealer",
                "Detail": TRIO_KPI["sales_to_dealer"],
            },
            {
                "Item": "Fill rate",
                "Detail": TRIO_KPI["fill_rate"],
            },
            {
                "Item": "MOS",
                "Detail": f"{TRIO_KPI['mos']} (inventory metric in master file; no separate MOS row)",
            },
            {
                "Item": "10/12 on all 3 KPIs",
                "Detail": "Yes if each of the three KPIs has data for ≥10 of 12 FY months",
            },
        ]
    )

    def write_workbook(path: Path) -> None:
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            notes.to_excel(writer, sheet_name="Notes", index=False)
            rank1.to_excel(writer, sheet_name="Ranking_all_KPIs", index=False)
            rank2.to_excel(writer, sheet_name="Ranking_trio_KPIs", index=False)

    out = OUT_FILE
    try:
        write_workbook(out)
    except PermissionError:
        out = OUT_FILE_ALT
        write_workbook(out)

    print(f"Wrote {out}")
    print("\nTop 10 — all KPIs:")
    print(rank1.head(10).to_string(index=False))
    print("\nTop 10 — trio KPIs:")
    print(rank2.head(10).to_string(index=False))
    print(f"\n10/12 on all 3: {(rank2['10/12 on all 3 KPIs']=='Yes').sum()} distributors")


if __name__ == "__main__":
    main()
