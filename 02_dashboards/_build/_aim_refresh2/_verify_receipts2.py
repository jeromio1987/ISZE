"""Verify the 17 receipts for this pass: schema v2, ok true, read == taken, mtime covered."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")

PAGES = [
    "sales/ISZE_PMS_Tonnage_Evolution", "sales/ISZE_PMS_Family_Compare",
    "sales/ISZE_DB_DLR_Replenishment_CY2025", "sales/AIM_Dashboard_CY2026",
    "sales/ISZE_AIM_Classification_Paper", "sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025",
    "sales/ISZE_KPI_Dashboard", "sales/ISZE_Lost_Sales_Model", "sales/ISZE_Risk_Cockpit",
    "pricing/ISZE_Pricing_Revision_AIM_Source",
    "pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB",
    "pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust",
    "pricing/ISZE_Pricing_Revision_AIM_FX_20261001", "pricing/ISZE_Pricing_Policy_Paper",
    "pricing/ISZE_PMS_Price_Response_Brief_2026-09-22",
    "pricing/ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17",
    "pricing/ISZE_Price_Increase_5pct_Flat_SIMULATION_2026-09-22",
]

ok = 0
for rel in PAGES:
    h = ISZE / "02_dashboards" / (rel + ".html")
    r = h.with_suffix(".SHIP_RECEIPT.json")
    if not h.is_file():
        print("MISSING PAGE", rel)
        continue
    if not r.is_file():
        print("MISSING RECEIPT", rel)
        continue
    d = json.loads(r.read_text(encoding="utf-8"))
    covers = d.get("artifact_mtime_ms", 0) >= h.stat().st_mtime * 1000 - 1
    good = (d.get("schema") == "ship_receipt/v2" and bool(d.get("ok"))
            and d.get("screenshots_read") == d.get("screenshots_taken") and covers)
    ok += 1 if good else 0
    print(("OK  " if good else "BAD "),
          rel.ljust(56), "schema", d.get("schema"), "ok", d.get("ok"),
          "taken/read", d.get("screenshots_taken"), d.get("screenshots_read"),
          "covers", covers,
          "failed checks", [c["id"] for c in d.get("checks", []) if not c.get("ok")])
print(f"\ngood receipts: {ok} of {len(PAGES)}")
