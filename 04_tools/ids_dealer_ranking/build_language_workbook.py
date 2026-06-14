#!/usr/bin/env python3
"""Create Dutch-language evaluation workbook from EN master + NL reference."""

from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from ids_paths import BE_TEMPLATE, DATA_ROOT, NL_OUTPUT, RSA_TEMPLATE

SOURCE_EN = RSA_TEMPLATE
SOURCE_NL = BE_TEMPLATE
OUTPUT = NL_OUTPUT

# Text-only columns on the evaluation sheet (1-based); column G (points) excluded.
LANG_COLS = (2, 3, 4, 6, 8, 9, 10, 11)  # B,C,D,F,H,I,J,K


def _cols_for_row(row: int) -> tuple[int, ...]:
    if row == 4:
        return tuple(range(2, 14))  # header row incl. Prioriteit / Punt labels
    return LANG_COLS


def _copy_language_cells(ws_en, ws_nl, max_row: int) -> int:
    changed = 0
    for r in range(1, max_row + 1):
        for c in _cols_for_row(r):
            new_val = ws_nl.cell(r, c).value
            old_val = ws_en.cell(r, c).value
            if new_val is not None and new_val != old_val:
                ws_en.cell(r, c).value = new_val
                changed += 1
    return changed


def _harmonise_duplicate_wording(ws) -> list[str]:
    """Align near-duplicate EN pairs that share structure; return log lines."""
    logs: list[str] = []
    # Corporate symbol on letterhead vs business cards — ensure distinct Dutch labels
    pairs = {
        "A.2-1": "Is het ISUZU-huisstijlsymbool op het briefpapier conform I.VIS / I.BIS?",
        "A.2-2": "Zijn de visitekaartjes voorzien van het ISUZU-huisstijlsymbool conform I.VIS / I.BIS?",
    }
    for r in range(5, ws.max_row + 1):
        no = ws.cell(r, 2).value
        if no in pairs:
            ws.cell(r, 4).value = pairs[no]
            logs.append(f"{no}: onderscheid briefpapier vs. visitekaartjes")
    return logs


def _add_changelog(wb, notes: list[tuple[str, str, str]]) -> None:
    if "Changelog" in wb.sheetnames:
        del wb["Changelog"]
    ws = wb.create_sheet("Changelog", 0)
    headers = ["#", "Date", "Sheet / scope", "What changed"]
    ws.append(headers)
    today = date.today().isoformat()
    for i, (scope, detail) in enumerate(notes, start=1):
        ws.append([i, today, scope, detail])

    header_fill = PatternFill("solid", fgColor="C00000")
    header_font = Font(bold=True, color="FFFFFF")
    for c in range(1, 5):
        cell = ws.cell(1, c)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 12
    ws.column_dimensions["C"].width = 28
    ws.column_dimensions["D"].width = 72
    for r in range(2, ws.max_row + 1):
        ws.cell(r, 4).alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"


def main() -> None:
    if not SOURCE_EN.is_file():
        raise FileNotFoundError(SOURCE_EN)
    if not SOURCE_NL.is_file():
        raise FileNotFoundError(SOURCE_NL)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_EN, OUTPUT)

    wb = load_workbook(OUTPUT)
    ws_en = wb["Evaluation Sheet_English"]
    wb_nl = load_workbook(SOURCE_NL, data_only=True, read_only=True)
    ws_nl = wb_nl["Evaluatieformulier"]

    max_row = ws_en.max_row
    cells_changed = _copy_language_cells(ws_en, ws_nl, max_row)
    wb_nl.close()

    harmonise_log = _harmonise_duplicate_wording(ws_en)

    # Rename questionnaire tab
    ws_en.title = "Evaluatieformulier"

    changelog_entries = [
        (
            "Evaluatieformulier (was Evaluation Sheet_English)",
            f"Full Dutch (NL) text for headers, questions, scoring rubrics (columns B–D, F, H–K). "
            f"{cells_changed} cells updated from reference template De Corte. "
            "Point values (column G) and priority numbers (column E) unchanged.",
        ),
        (
            "Evaluatieformulier - duplicate / paired items",
            "Items that appear twice with the same intent now use consistent Dutch wording; "
            "paired controls differentiated where needed: "
            + "; ".join(harmonise_log)
            + ". Category point totals unchanged.",
        ),
        (
            "Workbook structure",
            "Cover Page, Score Card, and 2023-2025 Comparison tabs left as in the English master. "
            "Only the questionnaire tab language was changed. Self Evaluation column left blank for dealer input.",
        ),
    ]
    _add_changelog(wb, changelog_entries)

    wb.save(OUTPUT)
    print(f"Wrote {OUTPUT}")
    print(f"  cells localised: {cells_changed}")
    print(f"  harmonised items: {len(harmonise_log)}")


if __name__ == "__main__":
    main()
