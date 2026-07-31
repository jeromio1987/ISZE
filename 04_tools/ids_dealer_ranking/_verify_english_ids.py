#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

import xlrd

html_path = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\ids\IDS_2026_dealer_compare.html"
)
html = html_path.read_text(encoding="utf-8")
print("size", len(html))
print("goed", len(re.findall(r"goed", html, re.I)), "slecht", len(re.findall(r"slecht", html, re.I)))
for key in [
    "MIDI_CH",
    "Switzerland",
    "UK CV",
    "UK LCV",
    "Israel LCV",
    "Luxembourg",
    "Benelux",
    "Changelog",
    "pickMaxPointHighlights",
]:
    print(key, key in html)
m = re.search(r'"countries":\[(.*?)\]', html)
print("countries", m.group(0)[:400] if m else "none")

p = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\IDS_2026\reports\evaluation_result"
)
for name in [
    "Switzerland",
    "Luxembourg",
    "Belgium",
    "UK CV",
    "UK LCV",
    "Israel LCV",
    "Norway",
    "Benelux",
]:
    fp = p / f"2026 IDS Evaluation Result Report_{name}.xls"
    sh = xlrd.open_workbook(str(fp)).sheet_by_index(0)
    print(name, "->", repr(sh.cell_value(1, 0)))
