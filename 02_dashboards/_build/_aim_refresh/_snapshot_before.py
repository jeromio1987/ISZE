import hashlib, json, os, sys
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

TARGETS = [
    "02_dashboards/sales/ISZE_AIM_Classification_Paper.html",
    "02_dashboards/sales/AIM_Dashboard_CY2026.html",
    "02_dashboards/sales/ISZE_AIM_Comparison_ALL.html",
    "02_dashboards/sales/ISZE_AIM_Comparison_PORTUGAL.html",
    "02_dashboards/sales/ISZE_AIM_DB_DLR_Deep_Dive_ALL.html",
    "02_dashboards/sales/ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.html",
    "02_dashboards/pricing/ISZE_AIM_Repertoire_Map_2026-09-17.html",
    "02_dashboards/pricing/ISZE_AIM_Repertoire_Spider_2026-09-17.html",
    "02_dashboards/pricing/ISZE_AIM_Truck_Catalogue_2026-09-18.html",
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source.html",
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.html",
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.html",
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_FX_20261001.html",
    "02_dashboards/pricing/ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html",
    "02_dashboards/pricing/ISZE_Price_Increase_5pct_Flat_SIMULATION_2026-09-22.html",
    "02_dashboards/pricing/ISZE_PMS_Price_Response_Brief_2026-09-22.html",
    "02_dashboards/pricing/ISZE_Pricing_Policy_Paper.html",
    "02_dashboards/sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html",
    "02_dashboards/hub/ISZE_OS_Hub.html",
    "02_dashboards/ops/ISZE_OS_Console.html",
    "02_dashboards/sales/ISZE_PMS_Family_Compare.html",
]

out = {}
for f in TARGETS:
    if not os.path.exists(f):
        out[f] = {"missing": True}
        continue
    b = open(f, "rb").read()
    out[f] = {
        "bytes": len(b),
        "sha256": hashlib.sha256(b).hexdigest(),
        "mtime": __import__("datetime").datetime.fromtimestamp(os.path.getmtime(f)).isoformat(timespec="seconds"),
    }
os.makedirs("02_dashboards/_build/_aim_refresh", exist_ok=True)
json.dump(out, open("02_dashboards/_build/_aim_refresh/before_state.json", "w", encoding="utf-8"), indent=2)
for k, v in out.items():
    print(k, v.get("bytes"), (v.get("sha256") or "")[:12], v.get("mtime") or v)
