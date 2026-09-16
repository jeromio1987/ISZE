"""Verify P8 Action Ledger HTML — SSR tables, no NaN, no banned attribution."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ISZE = Path(__file__).resolve().parents[2]
HTML = ISZE / "02_dashboards" / "ops" / "ISZE_Action_Ledger.html"
CMD = ISZE / "02_dashboards" / "ops" / "OPEN_ACTION_LEDGER.cmd"

BANNED = ["delivered by", "caused", "drove", "thanks to", "attributable to"]


def main() -> int:
    ok = True
    if not HTML.is_file():
        print(f"FAIL missing {HTML}")
        return 1
    if not CMD.is_file():
        print(f"FAIL missing {CMD}")
        ok = False

    text = HTML.read_text(encoding="utf-8")
    if "NaN" in text:
        print("FAIL NaN in HTML")
        ok = False
    for phrase in BANNED:
        if phrase in text.lower():
            print(f"FAIL banned phrase {phrase!r}")
            ok = False

    for tab in ("Open by", "Trajectory", "Closed", "Rejects"):
        if tab.lower() not in text.lower():
            print(f"FAIL missing tab/section marker {tab!r}")
            ok = False

    bars = len(re.findall(r'class="bar-row"', text))
    rows = len(re.findall(r"<tbody", text))
    if bars < 1 and rows < 1:
        print(f"FAIL no SSR bars or tables (bars={bars} tbodys={rows})")
        ok = False
    else:
        print(f"ISZE_Action_Ledger.html: OK (SSR bars={bars}, table sections={rows})")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
