"""Write one SHIP_RECEIPT.json per rebuilt page via the house receipt writer."""
import json, os, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

WRITER = r"C:\Users\jerom\Desktop\claude\.cursor\skills\verify-before-done\scripts\write_receipt.mjs"
QA = "02_dashboards/_build/_aim_refresh/_qa"

SHOTS = sorted(os.listdir(QA))

# page -> the screenshots taken for it, in the order they were produced
PAGES = [
    ("02_dashboards/sales/ISZE_AIM_Classification_Paper.html",
     ["02_dashboards__sales__ISZE_AIM_Classification_Paper.png",
      "02_dashboards__sales__ISZE_AIM_Classification_Paper__bottom.png"]),
    ("02_dashboards/pricing/ISZE_AIM_Repertoire_Map_2026-09-17.html",
     ["02_dashboards__pricing__ISZE_AIM_Repertoire_Map_2026-09-17.png"]),
    ("02_dashboards/pricing/ISZE_AIM_Repertoire_Spider_2026-09-17.html",
     ["02_dashboards__pricing__ISZE_AIM_Repertoire_Spider_2026-09-17.png"]),
    ("02_dashboards/pricing/ISZE_AIM_Truck_Catalogue_2026-09-18.html",
     ["02_dashboards__pricing__ISZE_AIM_Truck_Catalogue_2026-09-18.png"]),
    ("02_dashboards/sales/ISZE_AIM_Comparison_ALL.html",
     ["02_dashboards__sales__ISZE_AIM_Comparison_ALL.png",
      "02_dashboards__sales__ISZE_AIM_Comparison_ALL__bottom.png"]),
    ("02_dashboards/sales/ISZE_AIM_Comparison_PORTUGAL.html",
     ["02_dashboards__sales__ISZE_AIM_Comparison_PORTUGAL.png",
      "02_dashboards__sales__ISZE_AIM_Comparison_PORTUGAL__bottom.png"]),
    ("02_dashboards/sales/ISZE_AIM_DB_DLR_Deep_Dive_ALL.html",
     ["02_dashboards__sales__ISZE_AIM_DB_DLR_Deep_Dive_ALL.png",
      "02_dashboards__sales__ISZE_AIM_DB_DLR_Deep_Dive_ALL__bottom.png"]),
    ("02_dashboards/sales/ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.html",
     ["02_dashboards__sales__ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.png",
      "02_dashboards__sales__ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL__bottom.png"]),
    ("02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source.html",
     ["02_dashboards__pricing__ISZE_Pricing_Revision_AIM_Source.png",
      "02_dashboards__pricing__ISZE_Pricing_Revision_AIM_Source__bottom.png"]),
    ("02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.html",
     ["02_dashboards__pricing__ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.png"]),
    ("02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.html",
     ["02_dashboards__pricing__ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.png"]),
    ("02_dashboards/pricing/ISZE_Pricing_Revision_AIM_FX_20261001.html",
     ["02_dashboards__pricing__ISZE_Pricing_Revision_AIM_FX_20261001.png"]),
    ("02_dashboards/pricing/ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html",
     ["02_dashboards__pricing__ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.png",
      "02_dashboards__pricing__ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17__bottom.png"]),
    ("02_dashboards/pricing/ISZE_Price_Increase_5pct_Flat_SIMULATION_2026-09-22.html",
     ["02_dashboards__pricing__ISZE_Price_Increase_5pct_Flat_SIMULATION_2026-09-22.png",
      "02_dashboards__pricing__ISZE_Price_Increase_5pct_Flat_SIMULATION_2026-09-22__bottom.png"]),
    ("02_dashboards/pricing/ISZE_PMS_Price_Response_Brief_2026-09-22.html",
     ["02_dashboards__pricing__ISZE_PMS_Price_Response_Brief_2026-09-22.png",
      "02_dashboards__pricing__ISZE_PMS_Price_Response_Brief_2026-09-22__bottom.png"]),
    ("02_dashboards/pricing/ISZE_Pricing_Policy_Paper.html",
     ["02_dashboards__pricing__ISZE_Pricing_Policy_Paper.png",
      "02_dashboards__pricing__ISZE_Pricing_Policy_Paper__bottom.png"]),
    ("02_dashboards/sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html",
     ["02_dashboards__sales__Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.png",
      "02_dashboards__sales__Dealer_Sellout_AIM_GPS_ITUK_UTI_2025__bottom.png"]),
    ("02_dashboards/hub/ISZE_OS_Hub.html",
     ["02_dashboards__hub__ISZE_OS_Hub.png",
      "02_dashboards__hub__ISZE_OS_Hub__bottom.png"]),
    ("02_dashboards/ops/ISZE_OS_Console.html",
     ["02_dashboards__ops__ISZE_OS_Console.png",
      "02_dashboards__ops__ISZE_OS_Console__bottom.png"]),
]

for page, shots in PAGES:
    if not os.path.exists(page):
        print("MISSING", page); continue
    args = ["node", WRITER, "--artifact", os.path.abspath(page)]
    for s in shots:
        if s in SHOTS:
            args += ["--screenshot", os.path.abspath(os.path.join(QA, s))]
    args += ["--screenshots-taken", str(len(shots)), "--screenshots-read", str(len(shots))]
    args += ["--notes", "AIM data refresh 2026-09-24: same builder, same arguments, "
                        "re-read from the refreshed AIM classification."]
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    keep = [l for l in out.splitlines() if l.strip() and ("wrote" in l.lower() or "VALID" in l
            or "INVALID" in l or "FAIL" in l or "ok" in l.lower())]
    print("=" * 5, page)
    print("   exit", r.returncode)
    for l in keep[-6:]:
        print("   ", l.strip()[:160])
