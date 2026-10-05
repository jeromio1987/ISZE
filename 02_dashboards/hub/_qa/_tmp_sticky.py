# -*- coding: utf-8 -*-
"""Temp: capture the sticky-thead mid-scroll state for both tables."""
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
    # market table: put thead in stuck state with rows underneath
    y = pg.evaluate("""(() => {
      const t = document.querySelector('#market table.t');
      const r = t.getBoundingClientRect();
      return window.scrollY + r.top + 120;   // header + a few rows scrolled past
    })()""")
    pg.evaluate("window.scrollTo(0, %f)" % y)
    pg.wait_for_timeout(400)
    print("market table stuck frame, scrollY =", y)
    pg.screenshot(path=OUT + r"\_tmp_sticky_market.png")
    # carry table
    y2 = pg.evaluate("""(() => {
      const t = document.querySelector('#carry table.t');
      const r = t.getBoundingClientRect();
      return window.scrollY + r.top + 40;
    })()""")
    pg.evaluate("window.scrollTo(0, %f)" % y2)
    pg.wait_for_timeout(400)
    print("carry table stuck frame, scrollY =", y2)
    pg.screenshot(path=OUT + r"\_tmp_sticky_carry.png")
    print(pg.evaluate("""(() => {
      const t = document.querySelector('#carry table.t');
      const th = t.querySelector('thead th').getBoundingClientRect();
      const tr0 = t.querySelector('tbody tr').getBoundingClientRect();
      return {theadY:[th.top, th.bottom], row0Y:[tr0.top, tr0.bottom], covered: th.bottom > tr0.top};
    })()"""))
    pg.close()
    b.close()
