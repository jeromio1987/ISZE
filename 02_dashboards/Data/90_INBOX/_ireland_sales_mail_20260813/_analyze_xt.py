"""Deep-analyze John Cummins Ireland sales-to-dealer XT workbook."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import openpyxl

XT = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_ireland_sales_mail_20260813"
    r"\attachments\2026-08-13_IE_XT_-_2026-08-13T114222.149.xlsx"
)


def main() -> None:
    wb = openpyxl.load_workbook(XT, read_only=True, data_only=True)
    print("file", XT)
    print("sheets", wb.sheetnames)
    for sn in wb.sheetnames:
        ws = wb[sn]
        rows = list(ws.iter_rows(values_only=True))
        print(f"\n=== {sn!r} rows={len(rows)} ===")
        # print first 20 non-empty-ish
        shown = 0
        for i, row in enumerate(rows):
            if all(c is None or str(c).strip() == "" for c in row):
                continue
            print(i, row[:25])
            shown += 1
            if shown >= 25:
                break
        if not rows:
            continue
        # infer header row = first non-empty
        header = None
        header_i = None
        for i, row in enumerate(rows):
            vals = [c for c in row if c is not None and str(c).strip() != ""]
            if len(vals) >= 3:
                header = row
                header_i = i
                break
        if header is None:
            continue
        print("HEADER_ROW", header_i, header)
        # column non-null counts
        ncols = max(len(r) for r in rows)
        nn = [0] * ncols
        for r in rows[header_i + 1 :]:
            for j in range(min(ncols, len(r))):
                if r[j] is not None and str(r[j]).strip() != "":
                    nn[j] += 1
        print("non_null_by_col:")
        for j, h in enumerate(header):
            if j < len(nn):
                print(f"  {j}: {h!r} -> {nn[j]}")
        # sample data rows
        print("SAMPLE DATA:")
        for r in rows[header_i + 1 : header_i + 8]:
            print(r[:20])
        # try detect date/period columns
        for j, h in enumerate(header):
            hs = str(h).lower() if h is not None else ""
            if any(k in hs for k in ("date", "month", "period", "year", "qty", "qty", "part", "dealer", "customer", "value", "amount", "sales")):
                vals = []
                for r in rows[header_i + 1 :]:
                    if j < len(r) and r[j] is not None:
                        vals.append(r[j])
                    if len(vals) >= 5:
                        break
                print(f"COL_HINT {j} {h!r} samples={vals}")
    wb.close()


if __name__ == "__main__":
    main()
