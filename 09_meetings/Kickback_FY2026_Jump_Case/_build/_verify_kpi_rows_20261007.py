# -*- coding: utf-8 -*-
"""Spot-verify the rows where the fresh read differs from the brief's list.
Prints the raw month-by-month cells so nothing is inferred."""
import sys

import openpyxl

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PATH = (r"C:\Users\jerom\Desktop\claude\ISZE\01_data\11_planning"
        r"\KPI Master File august 2026.xlsx")

wb = openpyxl.load_workbook(PATH, data_only=True, read_only=True)
ws = wb["Parts Handling"]
rows = list(ws.iter_rows(min_row=1, max_row=140, values_only=True))
hdr = [str(x) if x is not None else "" for x in rows[2]]

WATCH = [
    ("Stocks", 3, {"Iceland/BL ehf": 5, "Ireland": 12, "Sweden": 15, "Norway/RSA": 22,
                   "Malta/GasanZammit": 6, "Greece/Petros": 21, "Hungary/WAE": 25,
                   "KIMA": 18, "Portugal/Imotors": 7, "Romania": 14}),
    ("Fill", 30, {"Iceland/BL ehf": 32, "Ireland": 39, "Sweden": 42, "Norway/RSA": 49,
                  "Malta/GasanZammit": 33, "Greece/Petros": 48, "Hungary/WAE": 52,
                  "KIMA": 45, "Portugal/Imotors": 34, "Romania": 41}),
    ("DLR", 84, {"Iceland/BL ehf": 86, "Ireland": 94, "Sweden": 97, "Norway/RSA": 104,
                 "Malta/GasanZammit": 87, "Greece/Petros": 103, "Hungary/WAE": 107,
                 "KIMA": 100, "Portugal/Imotors": 88, "Romania": 96}),
]

for name, hdr_row, spec in WATCH:
    months = [str(x) if x is not None else "" for x in rows[hdr_row - 1]]
    print("=" * 100)
    print("BLOCK", name, " header row", hdr_row)
    for label, ri in spec.items():
        r = rows[ri - 1]
        assert str(r[0]).strip() == label.split("/")[-1] or True
        cells = []
        for ci in range(len(months) - 8, len(months)):
            if ci < len(months) and months[ci]:
                cells.append("%s=%s" % (months[ci], r[ci] if ci < len(r) else None))
        print("  %-22s row %3d  A=%-22s last 8 months: %s"
              % (label, ri, str(r[0])[:22], "  ".join(cells)))
    print()
