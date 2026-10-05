#!/usr/bin/env python3
"""Verify Aftermarket BI suite index HTML after build — retirement + link checks."""

from __future__ import annotations

import sys
from pathlib import Path

ISZE = Path(__file__).resolve().parents[2]
HTML = ISZE / "02_dashboards" / "sales" / "ISZE_Aftermarket_BI_Command_Center.html"

REQUIRED_LINKS = (
    "ISZE_Lost_Sales_Model.html",
    "ISZE_PMS_Family_Evolution_v2.html",
    "ISZE_PMS_Tonnage_Evolution.html",
    "ISZE_DB_DLR_Replenishment_CY2025.html",
    "ISZE_DB_Leakage_Review_CY2025.html",
)

RETIREMENT_MARKERS = (
    "retirement-notice",
    "Retired as a single mega-dashboard",
    "Command center retired",
)

BASIS_MARKERS = (
    "basis-strip",
    "Non-additive",
    "five distributors",
)

FORBIDDEN = (
    "ssr-radar",
    "radar-toggle",
    "Roughly half the register",
    "GREECE leakage column is blank",
    "Monday pricing calls",
    "sell-through",
    'id="panel-network"',
    'id="networkTbl"',
    "DB comparison radar",
)

MAX_KB = 512


def main() -> int:
    if not HTML.is_file():
        print(f"MISSING {HTML}")
        return 1

    html = HTML.read_text(encoding="utf-8")
    size_kb = len(html) / 1024
    print(f"HTML size: {size_kb:.1f} KB")
    if size_kb > MAX_KB:
        print(f"WARN: HTML exceeds {MAX_KB} KB — expected thin suite index")

    fails = 0

    title_ok = "suite map" in html.lower() or "command center retired" in html.lower()
    if not title_ok:
        print("FAIL: title does not state suite map / retired command center")
        fails += 1
    else:
        print("OK: title / retirement wording")

    for marker in RETIREMENT_MARKERS:
        if marker not in html:
            print(f"FAIL: missing retirement marker ({marker})")
            fails += 1
        else:
            print(f"OK: retirement — {marker}")

    for marker in BASIS_MARKERS:
        if marker not in html:
            print(f"FAIL: missing basis strip marker ({marker})")
            fails += 1
        else:
            print(f"OK: basis — {marker}")

    for href in REQUIRED_LINKS:
        if f'href="{href}"' not in html:
            print(f"FAIL: missing suite link {href}")
            fails += 1
        else:
            print(f"OK: link {href}")

    suite_cards = html.count('class="suite-card suite-link"')
    if suite_cards < len(REQUIRED_LINKS):
        print(f"FAIL: expected {len(REQUIRED_LINKS)} suite cards, got {suite_cards}")
        fails += 1
    else:
        print(f"OK: {suite_cards} suite cards")

    for needle in FORBIDDEN:
        if needle in html:
            print(f"FAIL: forbidden legacy content present ({needle})")
            fails += 1
        else:
            print(f"OK: absent — {needle}")

    if 'class="bar-row"' in html or "ssr-radar" in html:
        print("FAIL: legacy SSR chart content still present")
        fails += 1
    else:
        print("OK: no legacy bar-row / radar SSR")

    cmd = HTML.parent / "OPEN_Aftermarket_BI_Command_Center.cmd"
    if not cmd.is_file():
        print(f"FAIL: missing launcher {cmd.name}")
        fails += 1
    elif "ISZE_Aftermarket_BI_Command_Center.html" not in cmd.read_text(encoding="utf-8"):
        print("FAIL: launcher does not point at command center HTML")
        fails += 1
    else:
        print(f"OK: launcher {cmd.name}")

    if fails:
        print(f"\n{fails} hard failure(s)")
        return 1

    print("\nOK — suite index checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
