import json
import sys

import openpyxl

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

wb = openpyxl.load_workbook("isuzu_tenders_v3.xlsx", read_only=True)
for name in ["Germany National", "Germany OV", "Italy PNCP", "France BOAMP"]:
    rows = list(wb[name].iter_rows(values_only=True))
    print("===", name, "n=", len(rows) - 1)
    if rows:
        h = rows[0]
        ti = h.index("Title") if "Title" in h else 0
        for r in rows[1:4]:
            print(" ", ((r[ti] or "")[:80] if r else None))

d = json.loads(open("isze_dashboard_v4_data.json", encoding="utf-8").read())
stats = d["meta"]["stats"]
veh = stats.get("vehicles_by_country", {})
print("vehicles_by_country Germany", veh.get("Germany"))
print("vehicles_pickup_truck", stats.get("vehicles_pickup_truck"))
print("raw_notices", stats.get("raw_notices"), "opps", stats.get("opportunities"))

opps = d["opportunities"]
de = [o for o in opps if o.get("country") == "Germany"]
print("Germany opps", len(de))
for o in de[:10]:
    print(
        " -",
        (o.get("title") or o.get("title_raw") or "")[:70],
        "fleet",
        o.get("fleet_size"),
        "seg",
        o.get("product_segment"),
        "src",
        o.get("source_label") or o.get("_source") or o.get("source"),
    )

h = json.loads(open("_source_health.json", encoding="utf-8").read())
for k in [
    "Germany oeffentlichevergabe",
    "Germany service.bund",
    "Italy PNCP",
    "Spain PLACSP",
]:
    print(k, h.get(k))

html = open("isze_dashboard_v4_opportunity.html", encoding="utf-8").read()
needles = [
    "Stated fleet in captured notices",
    "tab-btn",
    "Aftersales",
    "ids_dealer",
    "Italy PNCP",
    "Germany oeffentlichevergabe",
    "filterCv",
    "CV only",
]
for needle in needles:
    print(repr(needle), html.count(needle))
