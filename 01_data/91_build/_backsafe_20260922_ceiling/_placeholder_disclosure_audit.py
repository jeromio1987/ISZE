"""Where does the flat-placeholder disclosure live, and what does it now say?

Recomputed share for CY2025 from the rebuilt ceiling: 40.9705% -> printed 41.0%.
The euro behind it does NOT move: EUR 22,278,000, eight markets.

This lists every place the disclosure text lives on disk, and prints the number each
one now shows, so a stale 40.3% cannot be left standing beside a 41.0%.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")

TARGETS = [
    ("02_dashboards/ops/ISZE_OS_Console.html", "OS Console"),
    ("02_dashboards/hub/ISZE_OS_Hub.html", "OS Hub"),
    ("02_dashboards/sales/ISZE_KPI_Dashboard.html", "KPI dashboard"),
    ("02_dashboards/sales/ISZE_Exec_Aftersales_Paper.html", "Exec paper"),
    ("09_meetings/Business_Performance_Review_2026/_bpr_numbers.json", "BPR numbers"),
    ("09_meetings/Business_Performance_Review_2026/ISZE_Business_Performance_Review_2026.pptx",
     "BPR deck (binary - strings only)"),
    ("02_dashboards/_composable/dist/isze_cockpit.customer.html", "customer cockpit"),
    ("02_dashboards/sales/leakage_packs/ISZE_Sales_Performance_Review_ITUK.html", "leakage ITUK"),
    ("02_dashboards/sales/leakage_packs/ISZE_Sales_Performance_Review_BELGIUM.html", "leakage BE"),
    ("02_dashboards/sales/leakage_packs/ISZE_Sales_Performance_Review_SWEDEN.html", "leakage SE"),
    ("02_dashboards/_build/leakage/payload.json", "leakage payload"),
    ("02_dashboards/sales/leakage_packs/ISZE_Exec_Leakage_Summary.html", "leakage exec summary"),
]

# words that identify the disclosure wherever it appears
NEEDLE = re.compile(
    r"(flat[^.<]{0,60}250|250[^.<]{0,40}placeholder|placeholder[^.<]{0,40}ceiling|"
    r"flat_share|one flat)", re.I)


def main() -> int:
    print(f"recomputed CY2025 share: 40.9705% -> printed 41.0%;"
          f" placeholder euro EUR 22,278,000; 8 markets\n")
    for rel, tag in TARGETS:
        p = ROOT / rel
        if not p.is_file():
            print(f"{tag:28s} ABSENT  {rel}")
            continue
        raw = p.read_bytes()
        try:
            text = raw.decode("utf-8", errors="ignore")
        except Exception:
            text = ""
        found = sorted(set(m.group(0).strip() for m in NEEDLE.finditer(text)))
        has_403 = "40.3" in text
        has_410 = "41.0" in text
        has_flat_json = re.findall(r'"flat_share[^"]*":\s*-?([0-9.]+)', text)
        share_json = has_flat_json
        print(f"{tag:28s} 40.3={str(has_403):5s} 41.0={str(has_410):5s} "
              f"share_json={share_json[:2] or '-'}")
        for f in found[:3]:
            print(f"      {f[:120]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
