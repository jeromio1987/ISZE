"""Answer the pre-delivery checker's wrap/width flags honestly.

The checker (`04_tools/excel_pre_delivery_check.py`) is written for the IDS template,
where column B holds a question and column D a description. Here column B holds a
short label or a live formula, and the long text sits in other columns, so its
"long text without wrap" rule misfires. This script proves that per case instead of
assuming it, and reports any real clipping risk (a text column narrower than its
longest value).

Run: python 02_dashboards/pricing/_build/audit_wrap_and_missing.py
"""
from __future__ import annotations

from pathlib import Path

import openpyxl

XLSX = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing"
            r"\Pricing_Revision_AIM_Source_Analysis.xlsx")

wb = openpyxl.load_workbook(XLSX)
print(f"sheets: {len(wb.sheetnames)}\n")

real = []
for name in wb.sheetnames:
    ws = wb[name]
    widths = {}
    for col, dim in ws.column_dimensions.items():
        if dim.width:
            widths[col] = dim.width

    # A merged cell shows its text across the whole merged span, so its effective
    # width is the sum of the merged columns. Treat those separately or the audit
    # reports the title and subtitle rows as clipping when they render fine.
    merged_width = {}
    for rng in ws.merged_cells.ranges:
        total = sum(widths.get(openpyxl.utils.get_column_letter(c), 8.43)
                    for c in range(rng.min_col, rng.max_col + 1))
        for r in range(rng.min_row, rng.max_row + 1):
            for c in range(rng.min_col, rng.max_col + 1):
                merged_width[(r, c)] = total

    print(f"--- {name}  ({ws.max_row} rows x {ws.max_column} cols), "
          f"freeze={ws.freeze_panes}")

    for col in range(1, ws.max_column + 1):
        letter = openpyxl.utils.get_column_letter(col)
        longest, n_long, wrapped, sample, merged_ok = 0, 0, 0, None, 0
        for r in range(1, min(ws.max_row, 400) + 1):
            c = ws.cell(row=r, column=col)
            v = c.value
            if not isinstance(v, str) or v.startswith("="):
                continue
            eff = merged_width.get((r, col))
            if eff is not None:
                # in a merge the text has the span, so it cannot clip the column
                if eff >= len(v):
                    merged_ok += 1
                continue
            if len(v) > longest:
                longest = len(v)
                sample = v[:48]
            if len(v) > 28:
                n_long += 1
                if c.alignment and c.alignment.wrap_text:
                    wrapped += 1
        if n_long == 0 and merged_ok == 0:
            continue
        w = widths.get(letter, 8.43)
        status = "ok"
        if longest > w and wrapped < n_long:
            status = "CLIP RISK"
            real.append((name, letter, longest, w, n_long, wrapped, sample))
        extra = f", {merged_ok} in merged spans" if merged_ok else ""
        print(f"    {letter}: {n_long:5} long unmerged cells, {wrapped:5} wrapped, "
              f"longest {longest:3} chars, width {w:5.1f}{extra}  {status}")
        if status != "ok":
            print(f"        e.g. {sample!r}")

print()
if real:
    print("REAL ISSUES (a text column longer than its width, not wrapped):")
    for name, letter, longest, w, n_long, wrapped, sample in real:
        print(f"  {name}!{letter}: longest {longest} > width {w:.1f}, "
              f"{n_long - wrapped} unwrapped  e.g. {sample!r}")
else:
    print("No real clipping risk found: every column holding text longer than its "
          "width is wrapped, or the flag was raised on a formula cell.")

print()
print("freeze panes per sheet:")
for name in wb.sheetnames:
    print(f"  {name:14} {wb[name].freeze_panes}")
