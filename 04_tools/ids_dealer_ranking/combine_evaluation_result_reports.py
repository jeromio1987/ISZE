#!/usr/bin/env python3
"""Combine per-country IDS Evaluation Result Report .xls files into one multi-tab workbook.

Opens each country's .xls report via Excel COM (win32com) so formula cells
(Score %, Ave. % — written as live formulas with no cached value in the raw
.xls) are actually calculated, then copies the resolved values into a single
.xlsx with one tab per country plus an Index tab. Percentage rows/columns get
a "0.0%" number format and are left unlocked.

Requires Excel + pywin32 (win32com) — Windows only.
"""

from __future__ import annotations

import sys
from pathlib import Path

import win32com.client.dynamic as win32
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.styles import Protection as XlsxProtection
from openpyxl.utils import get_column_letter

from ids_paths import IDS_RESULT_REPORTS_DIR, RANKINGS_DIR

# Must match build_ids_result_report.py layout constants.
COL_FIRST_DEALER = 3  # 0-based; column D
ROW_SCORE_PCT = 13  # 0-based; DK row 14 — dealer "Score (One hundred perfect score conversion)"
PCT_FORMAT = "0.0%"

OUTPUT = RANKINGS_DIR / "IDS_2026_Evaluation_Result_Reports_COMBINED.xlsx"

COUNTRIES = (
    "Belgium",
    "Netherlands",
    "Luxembourg",
    "Benelux",
    "Denmark",
    "Poland",
    "Greece",
    "Norway",
    "UK CV",
    "UK LCV",
    "Israel LCV",
    "Malta",
    "Cyprus",
    "Romania",
    "Portugal",
    "Hungary",
    "France",
    "Italy",
    "Switzerland",
    "Spain",
)


def _find_main_sheet(wb, country: str):
    wanted = f"{country}26".lower()
    for ws in wb.Worksheets:
        if ws.Name.lower() == wanted:
            return ws
    for ws in wb.Worksheets:
        if ws.Name.lower().endswith("26"):
            return ws
    return wb.Worksheets(1)


def _copy_sheet(values: list[list], tgt_ws) -> None:
    nrows = len(values)
    ncols = max((len(row) for row in values), default=0)
    avg_pct_col_0idx = ncols - 1  # last column — "Ave. %" (see build_ids_result_report.py)
    for r in range(nrows):
        row = values[r]
        for c in range(len(row)):
            value = row[c]
            if value is None or value == "":
                continue
            out_cell = tgt_ws.cell(row=r + 1, column=c + 1, value=value)
            is_pct = (r == ROW_SCORE_PCT and c >= COL_FIRST_DEALER) or (
                c == avg_pct_col_0idx and isinstance(value, (int, float))
            )
            if is_pct:
                out_cell.number_format = PCT_FORMAT
            out_cell.protection = XlsxProtection(locked=False)
    for c in range(ncols):
        tgt_ws.column_dimensions[get_column_letter(c + 1)].width = 18
    tgt_ws.column_dimensions["B"].width = 46
    tgt_ws.freeze_panes = "A2"


def main() -> int:
    RANKINGS_DIR.mkdir(parents=True, exist_ok=True)
    out_wb = Workbook()
    out_wb.remove(out_wb.active)

    summary: list[tuple[str, str, int]] = []
    missing: list[str] = []

    excel = win32.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    try:
        for country in COUNTRIES:
            path = IDS_RESULT_REPORTS_DIR / f"2026 IDS Evaluation Result Report_{country}.xls"
            if not path.is_file():
                missing.append(country)
                continue

            wb = excel.Workbooks.Open(str(path), 0, True)  # read-only
            try:
                excel.CalculateFullRebuild()
                src = _find_main_sheet(wb, country)
                used = src.UsedRange
                raw = used.Value2  # tuple of tuples, formulas resolved
                values = [list(r) for r in raw] if isinstance(raw[0], tuple) else [list(raw)]

                tab_name = country[:31]
                if tab_name in out_wb.sheetnames:
                    del out_wb[tab_name]
                tgt_ws = out_wb.create_sheet(tab_name)
                _copy_sheet(values, tgt_ws)

                dealers = 0
                if len(values) >= 3:
                    row3 = values[2]
                    for c in range(COL_FIRST_DEALER, len(row3)):
                        if row3[c]:
                            dealers += 1
                summary.append((tab_name, path.name, dealers))
            finally:
                wb.Close(False)
    finally:
        excel.Quit()

    if not summary:
        print("No evaluation result reports found.", file=sys.stderr)
        return 1

    idx = out_wb.create_sheet("Index", 0)
    idx.append(["Country", "Source file", "Dealers"])
    for c in range(1, 4):
        cell = idx.cell(1, c)
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="DDDDDD")
    total = 0
    for tab, src_name, n in summary:
        idx.append([tab, src_name, n])
        total += n
    idx.append([])
    idx.append(["TOTAL", "", total])
    idx.cell(idx.max_row, 1).font = Font(bold=True)
    idx.cell(idx.max_row, 3).font = Font(bold=True)
    idx.column_dimensions["A"].width = 14
    idx.column_dimensions["B"].width = 46
    idx.column_dimensions["C"].width = 12

    out_wb.save(OUTPUT)
    print(f"Wrote {OUTPUT}")
    print(f"  tabs: Index + {', '.join(t for t, _, _ in summary)}")
    print(f"  total dealers: {total}")
    if missing:
        print("  missing:", ", ".join(missing), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
