#!/usr/bin/env python3
"""Probe: does the IDS dealer-compare dashboard carry per-dealer section scores?"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
p = ROOT / "01_data/08_Distributor/IDS_2026/reports/dashboard/IDS_2026_dealer_compare.html"
print(p.exists(), p.stat().st_size if p.exists() else None)
t = p.read_text(encoding="utf-8", errors="replace")
print(len(t))

# embedded json payloads
for m in re.finditer(r'<script[^>]*type="application/json"[^>]*id="([^"]*)"', t):
    print("json block:", m.group(1))

for n in ["ROLMAX", "AUTO INDUSTRIAL LEIRIA"]:
    i = t.find(n)
    print("---", n, "idx", i)
    if i > 0:
        print(t[max(0, i - 700): i + 700])
