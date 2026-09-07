#!/usr/bin/env python3
"""Verify Aftermarket BI Command Center HTML after build — SSR checks."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ISZE = Path(__file__).resolve().parents[2]
HTML = ISZE / "02_dashboards" / "sales" / "ISZE_Aftermarket_BI_Command_Center.html"

REQUIRED_PANELS = ["panel-network", "panel-db", "panel-pricing", "panel-gpsv2"]
MIN_BAR_ROWS = 20
MIN_NETWORK_ROWS = 50
MAX_MB = 3.5

# Genius SSR markers (must paint without JS)
GENIUS_MARKERS = [
    ("ssr-waterfall", "wf-step"),
    ("heatmap", 'class="hot"'),
    ("ssr-sparkline", "spark-strip"),
    ("ssr-money-cards", "money-card"),
    ("ssr-scatter", "ssr-scatter"),
    ("ssr-radar", "ssr-radar"),
    ("radar-toggle", "radar-toggle"),
    ("bullet-chart", "bullet-track"),
    ("treemap-wrap", "treemap-cell"),
    ("ssr-leaderboard", "leaderboard"),
    ("ituk-dealer-top10", "ITUK dealer top 10"),
    ("so-what", "so-what"),
    ("section-nav", "section-nav"),
    ("ssr-donut", "ssr-donut"),
    ("ssr-db-compare", "ssr-db-compare"),
]


def main() -> int:
    if not HTML.is_file():
        print(f"MISSING {HTML}")
        return 1

    html = HTML.read_text(encoding="utf-8")
    size_mb = len(html) / 1024 / 1024
    print(f"HTML size: {size_mb:.2f} MB")
    if size_mb > MAX_MB:
        print(f"WARN: HTML exceeds {MAX_MB} MB target")

    fails = 0

    hero_block = html.split('<nav class="tabs"')[0]
    if "€" not in hero_block:
        print("FAIL: hero section has no € — KPIs not baked at build time")
        fails += 1
    else:
        print("OK: hero contains € in static HTML")

    bar_rows = html.count('class="bar-row"')
    svg_charts = html.count("ssr-svg")
    bar_count = bar_rows + svg_charts
    print(f"SSR elements: {bar_rows} bar-rows + {svg_charts} svg = {bar_count}")
    if bar_count < MIN_BAR_ROWS:
        print(f"FAIL: expected >={MIN_BAR_ROWS} bar-row/svg elements, got {bar_count}")
        fails += 1

    for name, needle in GENIUS_MARKERS:
        if needle not in html:
            print(f"FAIL: missing genius SSR marker {name} ({needle})")
            fails += 1
        else:
            print(f"OK: {name}")

    net_m = re.search(r'id="networkTbl".*?<tbody>(.*?)</tbody>', html, re.DOTALL)
    if net_m:
        tr_count = net_m.group(1).count("<tr")
        print(f"networkTbl static rows: {tr_count}")
        if tr_count < MIN_NETWORK_ROWS:
            print(f"FAIL: network table needs >={MIN_NETWORK_ROWS} rows, got {tr_count}")
            fails += 1
    else:
        print("FAIL: networkTbl tbody not found")
        fails += 1

    drill_m = re.search(r'id="tbl".*?<tbody>(.*?)</tbody>', html, re.DOTALL)
    if drill_m:
        drill_tr = drill_m.group(1).count("<tr")
        print(f"drill tbl static rows: {drill_tr}")
        if drill_tr < 100:
            print(f"WARN: drill table only {drill_tr} rows (expected ~500)")
    else:
        print("FAIL: drill tbl tbody not found")
        fails += 1

    if 'id="panel-pricing" class="panel active"' not in html:
        print("FAIL: panel-pricing not active on load (Monday = Pricing)")
        fails += 1
    if 'id="panel-network" class="panel active"' in html:
        print("FAIL: panel-network must not be default (archive only)")
        fails += 1
    if "Pricing &amp; revision — Monday actions" not in html and "Pricing & revision — Monday actions" not in html:
        print("FAIL: hero must say Pricing & revision — Monday actions")
        fails += 1
    if "Car park is not fully fixed" not in html:
        print("FAIL: V2 tab missing V19 truth banner")
        fails += 1
    if "44,926" not in html:
        print("FAIL: V2 tab missing IUK GPS lock 44,926")
        fails += 1
    if "Monday Command" in html:
        print("FAIL: killed Monday Command / leakage mega framing still present")
        fails += 1

    for pid in REQUIRED_PANELS:
        if f'id="{pid}"' not in html:
            print(f"FAIL: missing {pid}")
            fails += 1

    let_sort = len(re.findall(r"\blet sortKey\b", html))
    if let_sort > 1:
        print(f"FAIL: duplicate let sortKey ({let_sort}x) — script will not parse")
        fails += 1

    if '<script type="application/json" id="payload">' in html:
        print("WARN: legacy JSON payload still embedded (optional)")

    if fails:
        print(f"\n{fails} hard failure(s)")
        return 1

    print("\nOK — SSR smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
