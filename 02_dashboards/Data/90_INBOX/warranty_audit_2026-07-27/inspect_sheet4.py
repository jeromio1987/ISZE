"""Inspect Warranty_CV_2025.xlsx Sheet4 + IE/PT price gaps."""
from __future__ import annotations

import json
from pathlib import Path

import openpyxl

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\06_Warranty")
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\warranty_audit_2026-07-27")
CV = ROOT / "Warranty_CV_2025.xlsx"


def dump_sheet4():
    wb = openpyxl.load_workbook(CV, data_only=True)
    ws = wb["Sheet4"]
    print("=== Sheet4 first 100 non-empty rows ===")
    rows = []
    for r in range(1, ws.max_row + 1):
        vals = [ws.cell(r, c).value for c in range(1, 4)]
        if any(v is not None and v != "" for v in vals):
            rows.append((r, vals))
            if len(rows) <= 100:
                print(f"{r:4d} | {vals}")
    print(f"\nTotal non-empty rows: {len(rows)}")

    # Find country summary blocks — look for numeric totals near country names
    print("\n=== Rows mentioning 0 / IRELAND / PORTUGAL / TOTAL ===")
    hits = []
    for r, vals in rows:
        a = vals[0]
        if a is None:
            continue
        s = str(a).strip().upper()
        if (
            s == "0"
            or s == 0
            or "IRELAND" in s
            or "PORTUGAL" in s
            or "TOTAL" in s
            or "GRAND" in s
            or s in ("COUNTRY", "ROW LABELS")
        ):
            print(f"{r:4d} | {vals}")
            hits.append({"row": r, "vals": [str(v) if v is not None else None for v in vals]})

    # Also print last 40 rows (often grand totals)
    print("\n=== Last 40 non-empty rows ===")
    for r, vals in rows[-40:]:
        print(f"{r:4d} | {vals}")

    # Unique col A labels that look like countries / buckets
    labels = {}
    for r, vals in rows:
        a = vals[0]
        if a is None:
            continue
        key = str(a).strip()
        # keep if looks like header/country (short / uppercase-ish)
        if len(key) < 40:
            labels.setdefault(key, []).append((r, vals[1], vals[2]))

    # Print labels that appear once at start of a block (likely country headers with totals)
    print("\n=== Candidate country/bucket labels with numeric col B or C ===")
    for key, items in labels.items():
        nums = [(r, b, c) for r, b, c in items if isinstance(b, (int, float)) or isinstance(c, (int, float))]
        if nums:
            # show first and if any large amount
            big = [x for x in nums if (isinstance(x[1], (int, float)) and abs(x[1]) > 1000) or (isinstance(x[2], (int, float)) and abs(x[2]) > 1000)]
            if big or key in ("0", "IRELAND", "PORTUGAL") or "IRELAND" in key.upper() or "PORTUGAL" in key.upper():
                print(f"  [{key}] count={len(items)} sample={items[:3]} big={big[:3]}")

    out = {"hits": hits, "row_count": len(rows), "max_row": ws.max_row}
    (OUT / "_sheet4_inspect.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    wb.close()


def inspect_detail_sheets():
    wb = openpyxl.load_workbook(CV, data_only=False)
    print("\n=== Sheet names ===", wb.sheetnames)
    for name in wb.sheetnames:
        ws = wb[name]
        print(f"\n--- {name} dims={ws.dimensions} max_row={ws.max_row} max_col={ws.max_column} ---")
        # header row
        headers = [ws.cell(1, c).value for c in range(1, min(ws.max_column, 25) + 1)]
        print("row1:", headers)
        if ws.max_row >= 2:
            print("row2:", [ws.cell(2, c).value for c in range(1, min(ws.max_column, 25) + 1)])
        # formulas in first few rows for price cols
        for r in range(1, min(6, ws.max_row + 1)):
            for c in range(1, min(ws.max_column, 20) + 1):
                cell = ws.cell(r, c)
                if cell.value and isinstance(cell.value, str) and cell.value.startswith("="):
                    print(f"  formula {name}!{cell.coordinate}: {cell.value[:120]}")
    wb.close()


if __name__ == "__main__":
    dump_sheet4()
    inspect_detail_sheets()
