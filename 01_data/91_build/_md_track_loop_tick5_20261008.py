# -*- coding: utf-8 -*-
"""Loop catch-up tick: sync HTML from builder; log tick 5; do not invent Jerome decisions."""
from __future__ import annotations

import json
import runpy
from pathlib import Path

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\01_Strategy")
BUILDER = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_build_md_track_business_plan_20261008.py"
)
MD = OUT / "ISZE_MD_TRACK_BUSINESS_PLAN_2026-10-08.md"
HTML = OUT / "ISZE_MD_TRACK_BUSINESS_PLAN_2026-10-08.html"

# Preserve MD (newer loop prose); rebuild HTML from builder SSOT
runpy.run_path(str(BUILDER), run_name="__main__")

md = MD.read_text(encoding="utf-8")
if "| 5 |" not in md.split("## Loop tick log")[-1]:
    md = md.rstrip() + (
        "\n| 5 | 2026-10-08 (catch-up after loop shell died) | "
        "HTML rebuilt from builder to clear MD/HTML drift; "
        "loop process had exited — awaiting Jerome Japan rung (A vs A+B) before inventing more ask text |\n"
    )
    MD.write_text(md, encoding="utf-8")

html = HTML.read_text(encoding="utf-8")
checks = {
    "floor": "Floor" in html,
    "stretch": "Stretch" in html,
    "bar_rows": html.count("bar-row"),
    "no_script_src": "<script src=" not in html.lower(),
    "payload": 'id="payload"' in html,
}
print(json.dumps(checks))
if not all([checks["floor"], checks["stretch"], checks["bar_rows"] >= 5, checks["payload"]]):
    raise SystemExit("tick5 sync incomplete")
print("TICK5_OK")
