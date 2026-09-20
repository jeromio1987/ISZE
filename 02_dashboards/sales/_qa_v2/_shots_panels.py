"""Render the page and photograph the two panels the change was about: the decomposition axis and
the drilled part-number level, at full size so the axis labels can be read."""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_v2.html"
OUT = ROOT / "02_dashboards" / "sales" / "_qa_v2" / "shots"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, args=["--headless=new", "--disable-gpu"])
    pg = b.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=2)
    pg.goto(HTML.as_uri(), wait_until="load")
    pg.wait_for_timeout(1800)

    def clip(sel: str, name: str) -> None:
        box = pg.locator(sel).bounding_box()
        pg.screenshot(path=str(OUT / name),
                      clip={"x": box["x"] - 6, "y": box["y"] - 6,
                            "width": box["width"] + 12, "height": box["height"] + 12})
        print(f"  {name}: {box['width']:.0f}x{box['height']:.0f} px at "
              f"({box['x']:.0f},{box['y']:.0f})")

    print("panels at full size:")
    clip(".grid.g3 .card:first-child", "panel_main.png")
    clip(".grid.g3 .card:last-child", "panel_decomposition.png")
    clip(".controls", "panel_toolbar.png")

    pg.evaluate("""() => { const ch = window.Chart.getChart('c_main');
        const i = ch.data.labels.indexOf('N-series truck');
        const el = ch.getDatasetMeta(0).data[i];
        const r = ch.canvas.getBoundingClientRect();
        ch.canvas.dispatchEvent(new MouseEvent('click',
          {clientX: r.left + (el.x + el.base)/2, clientY: r.top + el.y,
           bubbles: true, cancelable: true, view: window})); }""")
    pg.wait_for_timeout(500)
    pg.evaluate("""() => { const ch = window.Chart.getChart('c_main');
        const i = ch.data.labels.indexOf('3.5 t');
        if (i < 0) return;
        const el = ch.getDatasetMeta(0).data[i];
        const r = ch.canvas.getBoundingClientRect();
        ch.canvas.dispatchEvent(new MouseEvent('click',
          {clientX: r.left + (el.x + el.base)/2, clientY: r.top + el.y,
           bubbles: true, cancelable: true, view: window})); }""")
    pg.wait_for_timeout(500)
    pg.evaluate("""() => { const ch = window.Chart.getChart('c_main');
        for (let i = 0; i < ch.data.labels.length; i++) {
          if (ch.data.datasets[0].data[i] === null) continue;
          const el = ch.getDatasetMeta(0).data[i];
          const r = ch.canvas.getBoundingClientRect();
          ch.canvas.dispatchEvent(new MouseEvent('click',
            {clientX: r.left + (el.x + el.base)/2, clientY: r.top + el.y,
             bubbles: true, cancelable: true, view: window}));
          return; } }""")
    pg.wait_for_timeout(700)
    print("level:", pg.evaluate("() => window.__pmfe2.level()"))
    clip(".grid.g3 .card:first-child", "panel_drilled_main.png")
    clip(".grid.g3 .card:last-child", "panel_drilled_decomposition.png")
    pg.screenshot(path=str(OUT / "drilled_wide.png"))
    b.close()
