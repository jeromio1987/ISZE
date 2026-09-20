# -*- coding: utf-8 -*-
"""QA render of the revision 3 pricing paper. QA-internal, not a user open."""
import os
import sys
from playwright.sync_api import sync_playwright

HTML = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Pricing_Policy_Paper_REV3.html"
QA = os.path.join(os.path.dirname(HTML), "_qa_rev3")
os.makedirs(QA, exist_ok=True)
uri = "file:///" + HTML.replace("\\", "/")

with sync_playwright() as pw:
    b = pw.chromium.launch(
        executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    pg = b.new_page(viewport={"width": 1000, "height": 1400},
                    device_scale_factor=1)
    errs = []
    pg.on("console", lambda m: errs.append(m.type + ": " + m.text)
          if m.type in ("error", "warning") else None)
    pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    pg.goto(uri, wait_until="load")
    pg.wait_for_timeout(4500)

    # ---- structural checks on the rendered DOM, not the source
    info = pg.evaluate("""() => {
      const out = {canvases: [], painted: [], rows: 0, tables: 0, nanos: 0};
      document.querySelectorAll('canvas').forEach(c => {
        const ctx = c.getContext('2d');
        out.canvases.push(c.id || '(no id)');
        let n = 0;
        if (ctx && c.width && c.height) {
          const d = ctx.getImageData(0,0,c.width,c.height).data;
          for (let i=3;i<d.length;i+=4000) { if (d[i] !== 0) { n++; } }
        }
        out.painted.push({id: c.id, w: c.width, h: c.height, nonblank: n});
      });
      out.tables = document.querySelectorAll('table').length;
      out.rows = document.querySelectorAll('tbody tr, table tr').length;
      const t = document.body.innerText;
      out.nanos = (t.match(/NaN/g)||[]).length;
      out.undefineds = (t.match(/undefined/g)||[]).length;
      out.charts = document.querySelectorAll('canvas').length;
      out.pages = document.querySelectorAll('section.page').length;
      return out;
    }""")
    print("canvases rendered :", len(info["canvases"]))
    blank = [p for p in info["painted"] if p["nonblank"] == 0]
    print("blank canvases    :", blank if blank else "none")
    print("tables / rows     :", info["tables"], "/", info["rows"])
    print("section pages     :", info["pages"])
    print("NaN in text       :", info["nanos"], "| undefined:", info["undefineds"])
    print("console errors    :", errs if errs else "none")

    # ---- per-page screenshots
    pages = pg.query_selector_all("section.page")
    print("sections found    :", len(pages))
    for i, el in enumerate(pages, 1):
        el.screenshot(path=os.path.join(QA, f"p{i:02d}.png"))
    b.close()
print("QA_DIR", QA)
