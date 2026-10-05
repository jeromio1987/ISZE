"""Pull every '40.3' and every flat-placeholder sentence out of the four rebuilt pages,
with context, so a stale share cannot hide behind a corrected one.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PAGES = [
    ("02_dashboards/ops/ISZE_OS_Console.html", "OS Console"),
    ("02_dashboards/hub/ISZE_OS_Hub.html", "OS Hub"),
    ("02_dashboards/sales/ISZE_KPI_Dashboard.html", "KPI dashboard"),
    ("02_dashboards/sales/ISZE_Exec_Aftersales_Paper.html", "Exec paper"),
    ("02_dashboards/sales/leakage_packs/ISZE_Sales_Performance_Review_ITUK.html", "leakage ITUK"),
    ("02_dashboards/_composable/dist/isze_cockpit.customer.html", "customer cockpit"),
]


def main() -> int:
    for rel, tag in PAGES:
        p = ROOT / rel
        if not p.is_file():
            print(f"== {tag}: ABSENT")
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        print(f"\n===== {tag}  ({len(t):,} bytes)")
        for pat in ("40.3", "40.32", "40%", "41.0", "41%", "40.97"):
            n = t.count(pat)
            if n:
                print(f"  literal {pat!r}: {n}")
                for m in list(re.finditer(re.escape(pat), t))[:4]:
                    s, e = max(0, m.start() - 150), min(len(t), m.end() + 150)
                    print("      ...", " ".join(t[s:e].split()), "...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
