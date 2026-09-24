import os, sys, hashlib, datetime, json
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

REL = [
    "sales/ISZE_AIM_Classification_Paper.html",
    "sales/ISZE_AIM_Comparison_ALL.html",
    "sales/ISZE_AIM_Comparison_PORTUGAL.html",
    "sales/ISZE_AIM_DB_DLR_Deep_Dive_ALL.html",
    "sales/ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.html",
    "pricing/ISZE_AIM_Repertoire_Map_2026-09-17.html",
    "pricing/ISZE_AIM_Repertoire_Spider_2026-09-17.html",
    "pricing/ISZE_AIM_Truck_Catalogue_2026-09-18.html",
    "pricing/ISZE_Pricing_Revision_AIM_Source.html",
    "pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.html",
    "pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.html",
    "pricing/ISZE_Pricing_Revision_AIM_FX_20261001.html",
    "pricing/ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html",
    "pricing/ISZE_Price_Increase_5pct_Flat_SIMULATION_2026-09-22.html",
    "pricing/ISZE_PMS_Price_Response_Brief_2026-09-22.html",
    "pricing/ISZE_Pricing_Policy_Paper.html",
    "sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html",
    "hub/ISZE_OS_Hub.html",
    "ops/ISZE_OS_Console.html",
]
B = "02_dashboards/_build/_aim_refresh/before/"
print(f'{"page":56} {"identical?":10} mtime')
for rel in REL:
    a = "02_dashboards/" + rel
    b = B + rel.replace("/", "__")
    if not (os.path.exists(a) and os.path.exists(b)):
        print(rel, "missing"); continue
    ha = hashlib.sha256(open(a, "rb").read()).hexdigest()
    hb = hashlib.sha256(open(b, "rb").read()).hexdigest()
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(a)).strftime("%H:%M:%S")
    print(f"{rel:56} {'SAME' if ha==hb else 'CHANGED':10} {mt}")
