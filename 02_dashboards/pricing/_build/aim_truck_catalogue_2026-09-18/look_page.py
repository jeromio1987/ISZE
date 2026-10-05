"""Look at the page in real Chrome and photograph what it actually shows.

This is the quick visual loop: load the page, wait for the vehicle picture,
screenshot the stage, and report where the picture and each zone landed. Reading
the screenshot is what tells me whether the hotspot fit is right.
"""
import json
import os
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_AIM_Truck_Catalogue_2026-09-18.html"
OUT = os.path.join(HERE, "_qa")
os.makedirs(OUT, exist_ok=True)

which = sys.argv[1] if len(sys.argv) > 1 else "all"

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 1000},
                    device_scale_factor=1)
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("file:///" + HTML.replace("\\", "/"))
    pg.wait_for_function("window.__truckReady === true", timeout=30000)
    pg.wait_for_function("window.truckPhoto && window.truckPhoto().ready",
                         timeout=30000)

    n = pg.evaluate("() => window.truckZones.length")
    print("zones:", n)
    print("photo:", json.dumps(pg.evaluate("() => window.truckPhoto()"),
                               indent=1)[:400])

    for i in range(n):
        key = pg.evaluate(f"""() => {{
          window.truckSelect({i});
          return window.truckState.veh;
        }}""")
        info = pg.evaluate("() => ({veh:window.truckState.veh,"
                           "rects:window.truckZoneRects(),"
                           "fit:window.truckFit()})")
        name = pg.evaluate("() => document.getElementById('vname').textContent")
        print(f"  zone {i}: {name}")

    # per vehicle: screenshot with no selection, and with the chassis selected
    for v in range(4):
        pg.evaluate(f"() => {{ window.truckState.veh={v}; window.truckSelect(-1);"
                    f" window.switchVehicle ? null : null; }}")
        pg.evaluate("() => { window.truckState.sel=-1; }")
        # switch vehicle through the tabs, the way a person does
        pg.evaluate(f"() => {{ var t=document.querySelectorAll('#tabs button');"
                    f" if(t[{v}]) t[{v}].click(); }}")
        pg.wait_for_timeout(700)
        vn = pg.evaluate("() => document.getElementById('vname').textContent")
        fit = pg.evaluate("() => window.truckFit()")
        print(f"veh {v} {vn}: fit {fit}")
        pg.locator(".stage").screenshot(path=os.path.join(OUT, f"veh{v}_load.png"))

        pg.evaluate("() => window.truckSelect(3)")   # chassis
        pg.wait_for_timeout(250)
        pg.locator(".stage").screenshot(path=os.path.join(OUT, f"veh{v}_chassis.png"))
        pg.evaluate("() => window.truckSelect(-1)")

    pg.evaluate("() => window.truckSelect(1)")
    pg.wait_for_timeout(200)
    pg.screenshot(path=os.path.join(OUT, "page_full.png"), full_page=True)
    print("console errors:", errs[:5] if errs else "none")
    b.close()
print("screenshots in", OUT)
