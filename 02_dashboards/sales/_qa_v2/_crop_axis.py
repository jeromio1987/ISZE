"""Crop tight on the decomposition chart's axis so the tick labels can actually be read."""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_v2.html"
OUT = ROOT / "02_dashboards" / "sales" / "_qa_v2" / "shots"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, args=["--headless=new", "--disable-gpu"])
    pg = b.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=3)
    pg.goto(HTML.as_uri(), wait_until="load")
    pg.wait_for_timeout(1800)
    # the whole decomposition card, at 3x, so the axis type is legible
    box = pg.locator(".grid.g3 .card:last-child").bounding_box()
    pg.screenshot(path=str(OUT / "axis_decomposition_3x.png"),
                  clip={"x": box["x"], "y": box["y"], "width": box["width"],
                        "height": box["height"]})
    print("decomposition card:", box)
    print("ticks the formatter produces:",
          pg.evaluate("() => window.__pmfe2.decTicks()"))
    # and the toolbar at 3x
    tb = pg.locator(".controls").bounding_box()
    pg.screenshot(path=str(OUT / "toolbar_3x.png"),
                  clip={"x": tb["x"], "y": tb["y"], "width": tb["width"], "height": tb["height"]})
    print("toolbar:", tb)
    b.close()
