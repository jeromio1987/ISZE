#!/usr/bin/env python3
"""Universal Excel pre-delivery checks — merges, wrap, column width, freeze panes.

See 00_docs/EXCEL_PRE_DELIVERY_CHECK.md for the full checklist.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

# Columns that typically hold long text (0-based for logic; openpyxl is 1-based)
DESCRIPTION_COLS = {2, 4}  # B, D
MIN_NAME_WIDTH = 12.0
MIN_DESC_WIDTH = 28.0


@dataclass
class Issue:
    sheet: str
    check: str
    detail: str


@dataclass
class SheetResult:
    name: str
    merges: int
    issues: list[Issue] = field(default_factory=list)


def _col_width(ws: Worksheet, col: int) -> float:
    letter = get_column_letter(col)
    dim = ws.column_dimensions.get(letter)
    if dim is None or dim.width is None:
        return 8.43
    return float(dim.width)


def _cell_has_wrap(ws: Worksheet, row: int, col: int) -> bool:
    cell = ws.cell(row, col)
    if cell.alignment is None:
        return False
    return bool(cell.alignment.wrap_text)


def _long_text_cells(ws: Worksheet, max_scan_row: int = 200) -> list[tuple[int, int, str]]:
    out: list[tuple[int, int, str]] = []
    for r in range(1, min(ws.max_row, max_scan_row) + 1):
        for c in DESCRIPTION_COLS:
            v = ws.cell(r, c).value
            if isinstance(v, str) and len(v) > 40:
                out.append((r, c, v[:60]))
    return out


def check_sheet(ws: Worksheet, *, template_ws: Worksheet | None = None) -> SheetResult:
    res = SheetResult(name=ws.title, merges=len(list(ws.merged_cells.ranges)))
    t_merges = len(list(template_ws.merged_cells.ranges)) if template_ws else None

    if template_ws is not None and res.merges != t_merges:
        res.issues.append(
            Issue(
                ws.title,
                "merge_count",
                f"merges {res.merges} != template {t_merges}",
            )
        )

    if ws.freeze_panes is None and (template_ws is None or template_ws.freeze_panes):
        res.issues.append(
            Issue(ws.title, "freeze_panes", "freeze_panes not set (template may require it)")
        )

    for c in range(1, min(ws.max_column, 30) + 1):
        w = _col_width(ws, c)
        header = str(ws.cell(1, c).value or ws.cell(2, c).value or "")
        if c == 2 and w < MIN_DESC_WIDTH:
            res.issues.append(
                Issue(ws.title, "column_width", f"col B width {w:.1f} < {MIN_DESC_WIDTH}")
            )
        if "dealer" in header.lower() or "name" in header.lower():
            if w < MIN_NAME_WIDTH:
                res.issues.append(
                    Issue(ws.title, "column_width", f"col {c} ({header[:20]!r}) width {w:.1f} too narrow")
                )

    long_cells = _long_text_cells(ws)
    unwrapped = [
        (r, c, txt)
        for r, c, txt in long_cells
        if not _cell_has_wrap(ws, r, c)
    ]
    if len(unwrapped) > 5:
        res.issues.append(
            Issue(
                ws.title,
                "wrap_text",
                f"{len(unwrapped)} long-text cells without wrap_text (e.g. row {unwrapped[0][0]} col {unwrapped[0][1]})",
            )
        )

    # Merged cell: non-top-left should be empty
    for mrange in ws.merged_cells.ranges:
        min_row, min_col = mrange.min_row, mrange.min_col
        for r in range(mrange.min_row, mrange.max_row + 1):
            for c in range(mrange.min_col, mrange.max_col + 1):
                if r == min_row and c == min_col:
                    continue
                val = ws.cell(r, c).value
                if val not in (None, ""):
                    res.issues.append(
                        Issue(
                            ws.title,
                            "merge_anchor",
                            f"non-anchor value in merge {mrange.coord} at {r},{c}: {val!r}",
                        )
                    )
                    break

    return res


def check_workbook(path: Path, template: Path | None = None) -> dict:
    wb = load_workbook(path, data_only=False)
    twb = load_workbook(template, data_only=False) if template else None
    sheets: list[SheetResult] = []

    for name in wb.sheetnames:
        tws = twb[name] if twb and name in twb.sheetnames else (twb.worksheets[0] if twb else None)
        sheets.append(check_sheet(wb[name], template_ws=tws))

    if twb:
        twb.close()
    wb.close()

    issues = [i for s in sheets for i in s.issues]
    return {
        "path": str(path),
        "ok": not issues,
        "sheets": [
            {
                "name": s.name,
                "merges": s.merges,
                "issues": [{"check": i.check, "detail": i.detail} for i in s.issues],
            }
            for s in sheets
        ],
        "issue_count": len(issues),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path, nargs="+", help="Excel file(s) to check (.xlsx)")
    parser.add_argument("--template", type=Path, help="Template workbook for merge/freeze comparison")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results = []
    for p in args.workbook:
        if not p.is_file():
            print(f"Not found: {p}", file=sys.stderr)
            return 2
        if p.suffix.lower() not in {".xlsx", ".xlsm"}:
            print(f"Skip (use ids_logic_check for .xls): {p}", file=sys.stderr)
            continue
        results.append(check_workbook(p, args.template))

    if not results:
        return 2

    failed = [r for r in results if not r["ok"]]
    if args.json:
        print(json.dumps({"ok": not failed, "results": results}, indent=2))
    else:
        for r in results:
            status = "OK" if r["ok"] else "FAIL"
            print(f"{Path(r['path']).name:40} {status}  issues={r['issue_count']}")
            for sh in r["sheets"]:
                for i in sh["issues"]:
                    print(f"  [{sh['name']}] {i['check']}: {i['detail']}")
        print(f"\nSummary: {len(results) - len(failed)}/{len(results)} passed")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
