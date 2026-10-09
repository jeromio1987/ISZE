# -*- coding: utf-8 -*-
"""Fresh extraction of the three reporting measures per market from
01_data/11_planning/KPI Master File august 2026.xlsx, sheet 'Parts Handling'.

Blocks (1-based rows in the sheet):
  Stocks                 header row   3, data rows   4-25
  First Fill Rate        header row  30, data rows  31-52
  Parts Sales DB to DLR  header row  84, data rows  85-108

A month counts as reported when the cell holds a number.  'N/D' (no report sent),
'N/A' (not tracked), 'ISZE', 'IBX', blanks and None are all NOT a report.
"""
import sys

import openpyxl

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PATH = (r"C:\Users\jerom\Desktop\claude\ISZE\01_data\11_planning"
        r"\KPI Master File august 2026.xlsx")

BLOCKS = [("Stocks", 3, 4, 25), ("Fill", 30, 31, 52), ("DLR", 84, 85, 108)]


def num(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return None


wb = openpyxl.load_workbook(PATH, data_only=True, read_only=True)
ws = wb["Parts Handling"]
rows = list(ws.iter_rows(min_row=1, max_row=140, values_only=True))


def months(hdr_row):
    r = rows[hdr_row - 1]
    return [str(x) if x is not None else "" for x in r]


data = {}
for name, hdr, r0, r1 in BLOCKS:
    months_row = months(hdr)
    for ri in range(r0, r1 + 1):
        r = rows[ri - 1]
        who = r[0]
        if who is None:
            continue
        who = str(who).strip()
        seen = []
        for ci in range(1, len(r)):
            if ci >= len(months_row) or not months_row[ci]:
                continue
            if num(r[ci]) is not None:
                seen.append((ci, months_row[ci], num(r[ci]), r[ci]))
        data.setdefault(who, {})[name] = seen

print("sheet months after Aug 25 present in the header:",
      [m for m in months(3) if m][:40])
print()
hdr = "%-20s %-30s %-30s %-30s" % ("market", "Stocks", "First Fill Rate",
                                   "Parts Sales DB to DLR in EUR")
print(hdr)
print("-" * len(hdr))
for who in sorted(data.keys()):
    cells = []
    for name, _, _, _ in BLOCKS:
        seen = data[who].get(name, [])
        if not seen:
            cells.append("NONE")
        else:
            cells.append("%s -> %s" % (seen[0][1], seen[-1][1]))
    print("%-20s %-30s %-30s %-30s" % (who, cells[0], cells[1], cells[2]))

print()
print("=== detail per market (first and last reported month, count) ===")
for who in sorted(data.keys()):
    print(who)
    for name, _, _, _ in BLOCKS:
        seen = data[who].get(name, [])
        if not seen:
            print("   %-5s none" % name)
        else:
            print("   %-5s %3d months  %s .. %s   (first %s last %s)"
                  % (name, len(seen), seen[0][1], seen[-1][1], seen[0][2], seen[-1][2]))
