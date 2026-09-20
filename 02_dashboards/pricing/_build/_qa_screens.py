# -*- coding: utf-8 -*-
"""QA-internal: screenshot each page of the built HTML so the new pages can be read."""
import io, os, sys
from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"
HTML = os.path.join(ISZE, "02_dashboards", "pricing", "ISZE_Pricing_Policy_Paper.html")
OUT = os.path.join(ISZE, "02_dashboards", "pricing", "_qa")
os.makedirs(OUT, exist_ok=True)

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome")
    pg = b.new_page(viewport={"width": 794, "height": 1123}, device_scale_factor=1.5)
    pg.goto("file:///" + HTML.replace("\\", "/"))
    pg.wait_for_timeout(3500)
    pages = pg.query_selector_all("section.page")
    print("pages: %d" % len(pages))
    for i, el in enumerate(pages):
        # report the page's scroll height vs the A4 page height so overflow is visible
        info = el.evaluate("e => ({h: e.scrollHeight, c: e.clientHeight, "
                           "head: (e.querySelector('h1,h2')||{}).textContent||''})")
        flag = "OVERFLOW" if info["h"] > info["c"] + 8 else "ok"
        print("  p%02d  scroll %5d  client %5d  %s  %s"
              % (i + 1, info["h"], info["c"], flag, info["head"].strip()[:70]))
        el.screenshot(path=os.path.join(OUT, "p%02d.png" % (i + 1)))
    b.close()
print("screenshots ->", OUT)
