"""Read-only: the headline numbers on the rebuilt pages, and file sizes before/after."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")

PAGES = [
    "02_dashboards/sales/ISZE_PMS_Tonnage_Evolution.html",
    "02_dashboards/sales/ISZE_PMS_Family_Compare.html",
    "02_dashboards/sales/ISZE_DB_DLR_Replenishment_CY2025.html",
    "02_dashboards/sales/AIM_Dashboard_CY2026.html",
    "02_dashboards/sales/ISZE_AIM_Classification_Paper.html",
    "02_dashboards/sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html",
    "02_dashboards/sales/ISZE_KPI_Dashboard.html",
    "02_dashboards/sales/ISZE_Lost_Sales_Model.html",
    "02_dashboards/sales/ISZE_Risk_Cockpit.html",
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source.html",
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.html",
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.html",
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_FX_20261001.html",
    "02_dashboards/pricing/ISZE_Pricing_Policy_Paper.html",
    "02_dashboards/pricing/ISZE_PMS_Price_Response_Brief_2026-09-22.html",
    "02_dashboards/pricing/ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html",
    "02_dashboards/pricing/ISZE_Price_Increase_5pct_Flat_SIMULATION_2026-09-22.html",
]

print("page / size now / size at the last push / receipt ok")
for rel in PAGES:
    p = ISZE / rel
    now = p.stat().st_size
    old = subprocess.run(["git", "show", f"77edae82:{rel}"], cwd=ISZE,
                         capture_output=True)
    old_len = len(old.stdout) if old.returncode == 0 else None
    r = json.loads(p.with_suffix(".SHIP_RECEIPT.json").read_text(encoding="utf-8"))
    print(f"  {rel.split('/')[-1]:<58} {now:>9,}  {old_len if old_len is not None else '-':>9}  ok={r['ok']}")

print("\nAIM CY2026 payload headlines")
js = (ISZE / "02_dashboards/sales/aim_cy2026.data.js").read_text(encoding="utf-8")
m = re.search(r"window\.__AIM_CY2026_DATA__\s*=\s*(\{.*\});\s*$", js, re.S)
d = json.loads(m.group(1))
k = d["kpis"]
print("  clean revenue", k["ytd_clean_eur"], "| coverage", k["coverage_pct"],
      "| open/review euro", k["open_review_eur"], "| high-risk share", k["high_risk_pct_of_matched"])

print("\nTonnage evolution payload")
html = (ISZE / "02_dashboards/sales/ISZE_PMS_Tonnage_Evolution.html").read_text(encoding="utf-8")
for pat in [r"network gap 2025", r"EUR [\d,]+"]:
    pass
m = re.search(r'"network_gap_2025_eur":\s*([\d.]+)', html)
if m:
    print("  network gap 2025 EUR", m.group(1))
print("  page bytes", len(html))
