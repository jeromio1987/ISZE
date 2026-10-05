#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
files = [
    ROOT / "02_dashboards/sales/ISZE_Exec_Aftersales_Paper.html",
    ROOT / "02_dashboards/sales/ISZE_Leakage_Cockpit.html",
    ROOT / "02_dashboards/sales/Warranty_Commercial_Review.html",
    ROOT / "02_dashboards/sales/ISZE_AIM_Classification_Paper.html",
    ROOT / "02_dashboards/sales/ISZE_AIM_vs_Price_Class_Case.html",
    ROOT / "02_dashboards/pricing/ISZE_Pricing_Policy_Paper_REV3.html",
    ROOT / "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source.html",
    ROOT / "02_dashboards/pricing/ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html",
    ROOT / "02_dashboards/sales/ISZE_Competitiveness_Dashboard.html",
    ROOT / "02_dashboards/sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html",
]
for f in files:
    t = f.read_text(encoding="utf-8", errors="replace")
    if "const __LEAK__" in t:
        shell = t.split("const __LEAK__")[0]
    elif "application/json" in t.lower():
        i = t.lower().find("application/json")
        shell = t[:i]
    elif "window.__WARRANTY__" in t:
        shell = t.split("window.__WARRANTY__")[0]
    else:
        shell = t
    low = shell.lower()
    issues = []
    for bad in ["sell-out", "sell-through", "book b", r"\bstreet\b", r"\bwallet\b", r"\bparc\b"]:
        c = len(re.findall(bad if bad.startswith("\\") else r"\b" + re.escape(bad) + r"\b", low))
        label = bad.replace(r"\b", "")
        if c:
            issues.append(f"{label}x{c}")
    print(f.name, "basis" if "basis-strip" in t else "NO_BASIS", issues or "clean")
