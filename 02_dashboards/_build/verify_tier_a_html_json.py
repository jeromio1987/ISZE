import json
import re
import sys
from pathlib import Path

ISZE = Path(__file__).resolve().parents[2]
paths = [
    ISZE / "02_dashboards/sales/ISZE_Aftermarket_BI_Command_Center.html",
    ISZE / "02_dashboards/sales/ISZE_DB_DLR_Replenishment_CY2025.html",
    ISZE / "01_data/01_Pricing/BOOK_B_REVISION_REVIEW_20260819.html",
]

ok = True
for p in paths:
    text = p.read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" id="payload">(.*?)</script>', text, re.S)
    if m:
        raw = m.group(1)
        if "NaN" in raw:
            print(f"{p.name}: FAIL (NaN in payload)")
            ok = False
            continue
        data = json.loads(raw)
        if "revision_rows" in data:
            n = len(data["revision_rows"])
        elif "rows" in data:
            n = len(data["rows"])
        else:
            n = len(data) if isinstance(data, list) else 0
        print(f"{p.name}: OK (JSON payload, {n} records)")
        continue
    bars = len(re.findall(r'class="bar-row"', text))
    tbody = len(re.findall(r"<tbody[^>]*>.*?<tr", text, re.S))
    if p.name == "ISZE_Aftermarket_BI_Command_Center.html":
        hero = text.split('<nav class="tabs"')[0]
        if not re.search(r"Network € leakage", hero) or not re.search(r"€[\d,]+", hero):
            print(f"{p.name}: FAIL (hero € leakage missing)")
            ok = False
            continue
        if bars < 20:
            print(f"{p.name}: FAIL (only {bars} SSR bar-rows)")
            ok = False
            continue
    elif bars < 1 and tbody < 1:
        print(f"{p.name}: FAIL (no SSR bars or table rows)")
        ok = False
        continue
    print(f"{p.name}: OK (SSR, {bars} bar-rows, ~{tbody} table sections)")

sys.exit(0 if ok else 1)
