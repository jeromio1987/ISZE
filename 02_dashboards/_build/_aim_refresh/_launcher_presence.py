"""Take one screenshot per launcher: run the .cmd, see that a window opens on the right file."""
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

LAUNCHERS = [
    "02_dashboards/sales/OPEN_ISZE_AIM_Classification_Paper.cmd",
    "02_dashboards/sales/OPEN_ISZE_AIM_DB_DLR_Deep_Dive_ALL.cmd",
    "02_dashboards/sales/OPEN_ISZE_AIM_Comparison_PORTUGAL.cmd",
    "02_dashboards/pricing/OPEN_ISZE_AIM_Repertoire_Map.cmd",
    "02_dashboards/pricing/OPEN_AIM_Truck_Catalogue.cmd",
    "02_dashboards/pricing/OPEN_Pricing_Revision_AIM_FX_20261001.cmd",
    "02_dashboards/pricing/OPEN_PMS_Price_Response_Brief_2026-09-22.cmd",
    "02_dashboards/hub/OPEN_ISZE_OS_Hub.cmd",
    "02_dashboards/ops/OPEN_ISZE_OS_Console.cmd",
]
for c in LAUNCHERS:
    print(("PRESENT " if os.path.exists(c) else "MISSING ") + c)
