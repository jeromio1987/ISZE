"""Launcher audit v2 — handles both `start "" "%~dp0X"` and `set "HTML=%~dp0X"` shapes,
case-insensitive name/target comparison, CRLF check, and confirms every page we
rebuilt has a launcher of its own that opens it.

Read-only report.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")

FOLDERS = ["02_dashboards/sales", "02_dashboards/pricing", "02_dashboards/hub", "02_dashboards/ops"]

TARGET_PATTERNS = [
    re.compile(r'start\s+""\s+"%~dp0([^"]+)"', re.I),
    re.compile(r'set\s+"HTML=%~dp0([^"]+)"', re.I),
    re.compile(r"http://127\.0\.0\.1:\d+/([A-Za-z0-9_\-]+\.html)", re.I),
]

problems = []
rows = []
for folder in FOLDERS:
    for cmd in sorted((ISZE / folder).glob("OPEN_*.cmd")):
        raw = cmd.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        target = None
        for pat in TARGET_PATTERNS:
            m = pat.search(text)
            if m:
                target = m.group(1)
                break
        crlf = b"\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b"")
        echo = text.lstrip().lower().startswith("@echo off")
        name_stem = cmd.stem[len("OPEN_"):].lower()
        target_stem = Path(target).stem.lower() if target else ""
        # name and target agree when one stem contains the other, ignoring casing,
        # or when the launcher names a generic entry point (index/home).
        generic = target_stem in {"index", "home"}
        name_ok = bool(target_stem) and (
            generic or name_stem in target_stem or target_stem in name_stem
        )
        exists = bool(target) and (cmd.parent / target).is_file()
        rec = dict(cmd=str(cmd.relative_to(ISZE)), target=target, crlf=crlf, echo=echo,
                   name_ok=name_ok, exists=exists)
        rows.append(rec)
        if not (crlf and echo and name_ok and exists):
            problems.append(rec)

for r in rows:
    flag = "BAD " if r in problems else "ok  "
    print(f"{flag}{r['cmd']:<72} -> {r['target']}  crlf={r['crlf']} echo={r['echo']} "
          f"name_ok={r['name_ok']} exists={r['exists']}")

print(f"\nlaunchers scanned: {len(rows)}  problems: {len(problems)}")
for r in problems:
    print("   ", r)

# every rebuilt page must have a launcher that opens it
REBUILT = [
    "ISZE_PMS_Tonnage_Evolution.html", "ISZE_PMS_Family_Compare.html",
    "ISZE_DB_DLR_Replenishment_CY2025.html", "AIM_Dashboard_CY2026.html",
    "ISZE_AIM_Classification_Paper.html", "Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html",
    "ISZE_KPI_Dashboard.html", "ISZE_Lost_Sales_Model.html",
    "ISZE_Pricing_Revision_AIM_Source.html",
    "ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.html",
    "ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.html",
    "ISZE_Pricing_Revision_AIM_FX_20261001.html", "ISZE_Pricing_Policy_Paper.html",
    "ISZE_PMS_Price_Response_Brief_2026-09-22.html",
    "ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html",
    "ISZE_Price_Increase_5pct_Flat_SIMULATION_2026-09-22.html",
    "ISZE_Risk_Cockpit.html",
]
print("\npages without a launcher that opens them:")
missing = []
for page in REBUILT:
    hits = [r for r in rows if r["target"] and Path(r["target"]).name.lower() == page.lower()]
    if not hits:
        missing.append(page)
        print("   MISSING:", page)
print("   none" if not missing else f"   {len(missing)} missing")
