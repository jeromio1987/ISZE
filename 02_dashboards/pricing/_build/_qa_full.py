# -*- coding: utf-8 -*-
"""QA-internal: one full-page capture so overflow and overlap are visible in context."""
import io, os, sys
from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"
HTML = os.path.join(ISZE, "02_dashboards", "pricing", "ISZE_Pricing_Policy_Paper.html")
OUT = os.path.join(ISZE, "02_dashboards", "pricing", "_qa")

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome")
    pg = b.new_page(viewport={"width": 794, "height": 1123}, device_scale_factor=1)
    pg.goto("file:///" + HTML.replace("\\", "/"))
    pg.wait_for_timeout(3500)
    # box of each section, in document coordinates
    boxes = pg.evaluate("""() => [...document.querySelectorAll('section.page')].map((e,i) => {
      const r = e.getBoundingClientRect();
      const bg = getComputedStyle(e).backgroundColor;
      const last = e.querySelector('.pad') ? e.querySelector('.pad').lastElementChild : null;
      const lb = last ? last.getBoundingClientRect() : null;
      return {i:i+1, top: Math.round(r.top+window.scrollY), h: Math.round(r.height),
              bg, lastBottom: lb ? Math.round(lb.bottom + window.scrollY) : null};
    })""")
    for x in boxes:
        over = x["h"] - 1123
        print("p%02d h=%5d  %-6s bg=%-18s lastChildBottomOffset=%s"
              % (x["i"], x["h"], ("OVER +%d" % over) if over > 8 else "ok", x["bg"],
                 (x["lastBottom"] - x["top"]) if x["lastBottom"] else "-"))
    pg.screenshot(path=os.path.join(OUT, "full.png"), full_page=True)
    b.close()
print("full.png written")
