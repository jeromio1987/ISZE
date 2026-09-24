"""Read-only: for the three target pages, pull a couple of headline numbers out of the
old version (git, at the last push) and the new one, so the report can show what moved.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OLD = "77edae82"

TARGETS = {
    "02_dashboards/sales/ISZE_PMS_Tonnage_Evolution.html": [
        (r"network gap 2025 = EUR ([\d,]+)", "network gap 2025 (printed at build)"),
        (r'"aim":1', "aim rows marked"),
    ],
    "02_dashboards/sales/ISZE_PMS_Family_Compare.html": [
        (r'"bvp_expose"', "bvp expose block"),
        (r"Questions: (\d+)", "questions"),
    ],
    "02_dashboards/sales/ISZE_DB_DLR_Replenishment_CY2025.html": [
        (r'"rows":\s*\[', "rows array"),
    ],
}


def old_text(rel: str) -> str:
    r = subprocess.run(["git", "show", f"{OLD}:{rel}"], cwd=ISZE, capture_output=True)
    return r.stdout.decode("utf-8", errors="replace") if r.returncode == 0 else ""


for rel, pats in TARGETS.items():
    new = (ISZE / rel).read_text(encoding="utf-8", errors="replace")
    old = old_text(rel)
    print("==", rel.split("/")[-1], f"({len(old):,} -> {len(new):,} bytes)")
    for pat, label in pats:
        o = len(re.findall(pat, old))
        n = len(re.findall(pat, new))
        print(f"   {label:<42} before {o:>6}  after {n:>6}")
