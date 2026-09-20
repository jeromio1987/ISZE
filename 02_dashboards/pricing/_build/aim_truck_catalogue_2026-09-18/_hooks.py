import os

from playwright.sync_api import sync_playwright

HTML = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_AIM_Truck_Catalogue_2026-09-18.html"

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 950})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("file:///" + HTML.replace("\\", "/"))
    pg.wait_for_timeout(3000)
    for fn in ("truckVehicleRect", "truckZoneScreenPolys", "truckZoneRects",
               "truckPhoto", "truckFit", "truckHit", "truckLabelRects",
               "truckAllZonePoints", "truckZoneInterior", "truckOnTruck",
               "truckAnchors", "truckZonePolys", "truckHull", "truckPageSize"):
        print(fn.ljust(24), pg.evaluate(f"() => typeof window.{fn}"))
    print("errors:", errs[:3])
    b.close()
