#!/usr/bin/env python3
"""Probe: Portugal visit dealers — section scores from dealer feedback HTML."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FB = ROOT / "01_data/08_Distributor/IDS_2026/reports/dealer_feedback/PORTUGAL"

names = ["ROLMAX", "AUTO_RENO_PA\u00c7OS_FERREIRA", "AUTO_INDUSTRIAL_LEIRIA"]

for n in names:
    p = FB / f"{n}.html"
    if not p.exists():
        print(n, "MISSING")
        continue
    t = p.read_text(encoding="utf-8", errors="replace")
    print("=====", n, len(t))
    for pat in [
        r'"ids_total_pct"\s*:\s*[0-9.]+',
        r'"sections"\s*:\s*\{[^}]*\}',
        r'"weakest_section"\s*:\s*"[A-E]"',
        r'"ids_country_rank_total"\s*:\s*[0-9]+',
        r'"ids_global_rank"\s*:\s*[0-9]+',
        r'"b1_country_rank"\s*:\s*[0-9]+',
        r'"b1_pct"\s*:\s*[0-9.]+',
    ]:
        for m in re.finditer(pat, t):
            print("  ", m.group(0)[:300])
    m = re.search(r'"gaps"\s*:\s*\[(.*?)\]\s*[,}]', t, re.S)
    if m:
        refs = re.findall(r'"ref"\s*:\s*"([^"]+)"', m.group(1))
        print("   gap refs:", refs[:12], "n=", len(refs))
