# -*- coding: utf-8 -*-
"""Temp: are KPI tooltips clipped by table overflow:hidden? Is the sticky thead covering rows?"""
import sys
from playwright.sync_api import sync_playwright

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PAGE = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\hub\ISZE_OS_Hub.html"
OUT = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\hub\_qa"
sys.stdout.reconfigure(encoding="utf-8")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--force-device-scale-factor=1"])
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.goto("file:///" + PAGE.replace("\\", "/"))
    pg.wait_for_timeout(500)

    # hover the first KPI in the market table and see whether its tooltip is clipped
    kpi = pg.locator("#market table.t .kpi").first
    kpi.scroll_into_view_if_needed()
    pg.wait_for_timeout(300)
    kpi.hover()
    pg.wait_for_timeout(400)
    info = pg.evaluate("""(() => {
      const k = document.querySelector('#market table.t .kpi');
      const tip = k.querySelector('.tip');
      const cs = getComputedStyle(tip);
      const r = tip.getBoundingClientRect();
      const tbl = k.closest('table.t').getBoundingClientRect();
      // is the tooltip's own area inside the table's clip box?
      return {display: cs.display, visible: cs.visibility,
              tipBox:[+r.left.toFixed(1),+r.top.toFixed(1),+r.right.toFixed(1),+r.bottom.toFixed(1)],
              tableBox:[+tbl.left.toFixed(1),+tbl.top.toFixed(1),+tbl.right.toFixed(1),+tbl.bottom.toFixed(1)],
              tipOutsideTableRight: r.right > tbl.right + 1,
              tipBelowTableBottom: r.bottom > tbl.bottom + 1,
              tableOverflow: getComputedStyle(k.closest('table.t')).overflow};
    })()""")
    print("tooltip geometry:", info)
    pg.screenshot(path=OUT + r"\_tmp_tip_clip.png", clip={"x": 0, "y": 0, "width": 1440, "height": 900})
    # also a KPI deep inside the market table rows (further from the top)
    kpi2 = pg.locator("#market table.t .kpi").nth(40)
    kpi2.scroll_into_view_if_needed()
    pg.wait_for_timeout(300)
    kpi2.hover()
    pg.wait_for_timeout(400)
    print("tooltip 2:", pg.evaluate("""(() => {
      const ks = document.querySelectorAll('#market table.t .kpi');
      const k = ks[40]; const tip = k.querySelector('.tip'); const r = tip.getBoundingClientRect();
      const tbl = k.closest('table.t').getBoundingClientRect();
      return {clipBoxBottom: +tbl.bottom.toFixed(1), tipBottom: +r.bottom.toFixed(1),
              clippedByTable: r.bottom > tbl.bottom + 1};
    })()"""))
    pg.screenshot(path=OUT + r"\_tmp_tip_clip2.png")
    pg.close()
    b.close()
