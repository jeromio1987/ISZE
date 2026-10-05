"""Reproduce the zone-click test and print what each click resolves to."""
import os

from playwright.sync_api import sync_playwright

HTML = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_AIM_Truck_Catalogue_2026-09-18.html"

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 950}, device_scale_factor=2)
    pg.goto("file:///" + HTML.replace("\\", "/"))
    pg.wait_for_function("() => window.truckPhoto && window.truckPhoto().ready",
                         timeout=30000)
    pg.wait_for_timeout(600)

    zpts = pg.evaluate("() => window.truckAllZonePoints()")
    meta = pg.evaluate("() => window.truckZoneMeta().map(z=>z.name)")
    print("zone names:", meta)
    for zp in zpts:
        z, pt = zp["zone"], zp["pt"]
        if pt is None:
            print(f"  zone {z} no point")
            continue
        hits = pg.evaluate(f"() => window.truckHit({pt[0]}, {pt[1]})")
        print(f"  zone {z} ({meta[z][:22]:24s}) pt {pt} hits {hits}")

    print()
    for zp in zpts:
        if zp["pt"] is None:
            continue
        z, pt = zp["zone"], zp["pt"]
        pg.evaluate("() => window.scrollTo(0,0)")
        pg.wait_for_timeout(120)
        box = pg.evaluate("""() => {
          const r=document.getElementById('map').getBoundingClientRect();
          return {x:r.x, y:r.y};
        }""")
        pg.mouse.click(box["x"] + pt[0], box["y"] + pt[1])
        pg.wait_for_timeout(300)
        sel = pg.evaluate("() => window.truckState.sel")
        ok = "ok " if sel == z else "MISMATCH"
        print(f"  {ok} clicked zone {z} -> sel {sel} ({meta[sel][:26]})")
    b.close()
