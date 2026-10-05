"""Boot the page and print whatever the browser complains about, and the error
bar the page itself shows."""
import os

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_AIM_Truck_Catalogue_2026-09-18.html"

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": 1500, "height": 950})
    msgs = []
    pg.on("console", lambda m: msgs.append(f"[{m.type}] {m.text}"))
    pg.on("pageerror", lambda e: msgs.append(f"[pageerror] {e}"))
    pg.goto("file:///" + HTML.replace("\\", "/"))
    pg.wait_for_timeout(4000)
    print("ready flag:", pg.evaluate("() => window.__truckReady"))
    print("has truckPhoto:", pg.evaluate("() => typeof window.truckPhoto"))
    print("errbar:", pg.evaluate(
        "() => { var e=document.getElementById('errbar');"
        " return e ? [e.style.display, e.textContent.slice(0,300)] : null; }"))
    print("--- console ---")
    for m in msgs[:25]:
        print(" ", m[:300])
    b.close()
