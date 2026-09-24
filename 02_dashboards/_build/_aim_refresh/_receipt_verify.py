import glob, json, os, sys
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

WANT = [
    "02_dashboards/sales/ISZE_AIM_Classification_Paper",
    "02_dashboards/pricing/ISZE_AIM_Repertoire_Map_2026-09-17",
    "02_dashboards/pricing/ISZE_AIM_Repertoire_Spider_2026-09-17",
    "02_dashboards/pricing/ISZE_AIM_Truck_Catalogue_2026-09-18",
    "02_dashboards/sales/ISZE_AIM_Comparison_ALL",
    "02_dashboards/sales/ISZE_AIM_Comparison_PORTUGAL",
    "02_dashboards/sales/ISZE_AIM_DB_DLR_Deep_Dive_ALL",
    "02_dashboards/sales/ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL",
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source",
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB",
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust",
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_FX_20261001",
    "02_dashboards/pricing/ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17",
    "02_dashboards/pricing/ISZE_Price_Increase_5pct_Flat_SIMULATION_2026-09-22",
    "02_dashboards/pricing/ISZE_PMS_Price_Response_Brief_2026-09-22",
    "02_dashboards/pricing/ISZE_Pricing_Policy_Paper",
    "02_dashboards/sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025",
    "02_dashboards/hub/ISZE_OS_Hub",
    "02_dashboards/ops/ISZE_OS_Console",
]

rows = []
for stem in WANT:
    f = stem + ".SHIP_RECEIPT.json"
    if not os.path.exists(f):
        print("NO RECEIPT", stem); continue
    d = json.loads(open(f, encoding="utf-8-sig").read())
    art = d.get("artifact", "")
    mtime = os.path.getmtime(art) if os.path.exists(art) else 0
    ms = d.get("artifact_mtime_ms", 0) / 1000.0
    cov = ms >= mtime - 2
    c = {x["id"]: x for x in d.get("checks", [])}
    sc = c.get("screenshots", {})
    rows.append((os.path.basename(stem), d.get("ok"), d.get("schema"), cov,
                 sc.get("detail", ""), ms, mtime))
print(f'{"page":56} {"ok":5} {"covers mtime":13} screenshots')
for n, ok, sch, cov, scd, ms, mt in rows:
    print(f"{n:56} {str(ok):5} {str(cov):13} {scd[:70]}")
print()
print("all ok and mtime-covered:", all(r[1] and r[3] for r in rows), f"({len(rows)} pages)")
