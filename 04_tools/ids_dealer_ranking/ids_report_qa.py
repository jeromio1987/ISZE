#!/usr/bin/env python3
"""QA: compare generated IDS result report layout to DK master template."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import xlrd

from ids_paths import resolve_dk_template

# 0-based column indices (A=0, B=1, C=2, D=3)
COL_LABEL = 0
COL_TEXT = 1
COL_MAX = 2
COL_FIRST_DEALER = 3
ROW_AVG_LABEL = 11
AVG_HEADER_SCORE = "Total Average"
AVG_HEADER_PCT = "Ave. %"

META_LABELS = (
    "Dealer Name (*Write official company name for IDS certification)",
    "Evaluation Date",
    "Address",
    "Evaluator",
    "Contact Person of the Dealer and his position",
    "Available Models",
    "Other Vehicle Brand",
    "Opening Hours",
    "The number of Servicing Vehicle  per month",
)


def _load_sheet(path: Path, sheet_index: int = 0):
    rb = xlrd.open_workbook(str(path), formatting_info=True)
    return rb, rb.sheet_by_index(sheet_index)


def compare_to_dk(
    generated: Path,
    template: Path | None = None,
    *,
    min_dealers: int = 1,
) -> dict:
  if template is None:
      template = resolve_dk_template()
  issues: list[str] = []
  rb_t, sh_t = _load_sheet(template)
  rb_g, sh_g = _load_sheet(generated)

  # Sheet names (main tab is {CC}26, others match DK)
  exp_tail = rb_t.sheet_names()[1:4]
  got_tail = rb_g.sheet_names()[1:4]
  if got_tail != exp_tail:
      issues.append(f"aux sheet names {got_tail} != DK {exp_tail}")
  main_t = rb_t.sheet_names()[0]
  main_g = rb_g.sheet_names()[0]
  if not main_g.endswith("26"):
      issues.append(f"main sheet name {main_g!r} should end with 26")

  # Row count on main sheet
  if sh_g.nrows != sh_t.nrows:
      issues.append(f"main sheet rows {sh_g.nrows} != DK {sh_t.nrows}")

  # Merged cells count
  if len(sh_g.merged_cells) != len(sh_t.merged_cells):
      issues.append(
          f"merged cells {len(sh_g.merged_cells)} != DK {len(sh_t.merged_cells)}"
      )

  # Title row
  if sh_g.cell_value(0, COL_LABEL) != sh_t.cell_value(0, COL_LABEL):
      issues.append("A1 title mismatch")

  # Column C must never contain dealer names / dealer scores on meta rows
  for r in range(2, 11):
      val = sh_g.cell_value(r, COL_MAX)
      if val not in ("", None):
          issues.append(f"row {r+1} col C must be empty (found {val!r})")

  # Row 13 col C = 280
  if sh_g.cell_value(12, COL_MAX) != 280.0:
      issues.append(f"row 13 col C must be 280 (found {sh_g.cell_value(12, COL_MAX)!r})")

  # Row 14 col C must be empty
  if sh_g.cell_value(13, COL_MAX) not in ("", None):
      issues.append(f"row 14 col C must be empty (found {sh_g.cell_value(13, COL_MAX)!r})")

  # No custom avg headers in row 2 (DK leaves avg cols blank there)
  for c in range(sh_g.ncols):
      v = sh_g.cell_value(1, c)
      if isinstance(v, str) and "avg" in v.lower():
          issues.append(f"row 2 col {c+1} must not contain avg label ({v!r})")

  # Dealer numbers start at D (col index 3)
  dealer_cols = []
  for c in range(COL_FIRST_DEALER, sh_g.ncols):
      v = sh_g.cell_value(1, c)
      if v == "" or v is None:
          break
      if isinstance(v, (int, float)):
          dealer_cols.append(c)
  if len(dealer_cols) < min_dealers:
      issues.append(f"too few dealer columns ({len(dealer_cols)})")

  avg_col = COL_FIRST_DEALER + len(dealer_cols)
  avg_pct_col = avg_col + 1

  # Row 12 (Excel): DK average headers above score rows
  if sh_g.cell_value(ROW_AVG_LABEL, avg_col) != AVG_HEADER_SCORE:
      issues.append(
          f"row {ROW_AVG_LABEL + 1} avg col must be {AVG_HEADER_SCORE!r} "
          f"(found {sh_g.cell_value(ROW_AVG_LABEL, avg_col)!r})"
      )
  if sh_g.cell_value(ROW_AVG_LABEL, avg_pct_col) != AVG_HEADER_PCT:
      issues.append(
          f"row {ROW_AVG_LABEL + 1} avg % col must be {AVG_HEADER_PCT!r} "
          f"(found {sh_g.cell_value(ROW_AVG_LABEL, avg_pct_col)!r})"
      )

  # First dealer col must be index 3
  if dealer_cols and dealer_cols[0] != COL_FIRST_DEALER:
      issues.append(f"first dealer col is {dealer_cols[0]+1}, expected D (4)")

  # Meta labels in col A
  for i, label in enumerate(META_LABELS):
      r = 2 + i
      if sh_g.cell_value(r, COL_LABEL) != label:
          issues.append(f"row {r+1} A label mismatch: {sh_g.cell_value(r, COL_LABEL)!r}")

  # Question refs col A must match DK for rows 15+
  for r in range(14, min(sh_g.nrows, sh_t.nrows)):
      ref_t = sh_t.cell_value(r, COL_LABEL)
      ref_g = sh_g.cell_value(r, COL_LABEL)
      if ref_t != ref_g:
          issues.append(f"row {r+1} ref mismatch: {ref_g!r} vs DK {ref_t!r}")
          if len(issues) > 25:
              break

  # Max points col C must match DK on score rows
  for r in range(14, min(sh_g.nrows, sh_t.nrows)):
      mx_t = sh_t.cell_value(r, COL_MAX)
      mx_g = sh_g.cell_value(r, COL_MAX)
      if mx_t != mx_g:
          issues.append(f"row {r+1} col C max mismatch: {mx_g!r} vs DK {mx_t!r}")
          if len(issues) > 30:
              break

  # Category row background (sample A15)
  xf_t = rb_t.xf_list[sh_t.cell_xf_index(14, COL_LABEL)]
  xf_g = rb_g.xf_list[sh_g.cell_xf_index(14, COL_LABEL)]
  if xf_t.background.pattern_colour_index != xf_g.background.pattern_colour_index:
      issues.append("row 15 col A background colour differs from DK")

  # Dealer columns must inherit same row background as DK (cols A–C)
  for r in (14, 15, 16, 50, 100):
      if r >= min(sh_g.nrows, sh_t.nrows):
          continue
      bg_t = rb_t.xf_list[sh_t.cell_xf_index(r, COL_FIRST_DEALER)].background.pattern_colour_index
      bg_g = rb_g.xf_list[sh_g.cell_xf_index(r, COL_FIRST_DEALER)].background.pattern_colour_index
      if bg_t != bg_g:
          issues.append(
              f"row {r+1} col D background {bg_g} != DK {bg_t}"
          )
          break

  return {
      "ok": len(issues) == 0,
      "issues": issues,
      "dealers": len(dealer_cols),
      "cols": sh_g.ncols,
      "rows": sh_g.nrows,
  }


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: ids_report_qa.py <generated.xls>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"Not found: {path}", file=sys.stderr)
        return 2
    result = compare_to_dk(path)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
