# -*- coding: utf-8 -*-
"""Temp probe 2: exact text-start geometry + what paints on top."""
import sys
from playwright.sync_api import sync_playwright

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PAGE = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\hub\ISZE_OS_Hub.html"
sys.stdout.reconfigure(encoding="utf-8")

JS = r"""
(() => {
  const out = [];
  const L = document.querySelector('.layer.l1');
  const lr = L.getBoundingClientRect();
  const bar = L.querySelector('.bar');
  const br = bar.getBoundingClientRect();
  const bcs = getComputedStyle(bar);
  out.push({what:'layer', x:+lr.left.toFixed(1), r:+lr.right.toFixed(1), ov:getComputedStyle(L).overflow});
  out.push({what:'bar', x:+br.left.toFixed(1), r:+br.right.toFixed(1), w:+br.width.toFixed(1),
            pad:bcs.padding, box:bcs.boxSizing, gc:bcs.gridColumnStart, gr:bcs.gridRowStart,
            z:bcs.zIndex, pos:bcs.position});
  // text start of first char of h3, .q, first p
  for (const sel of ['h3', '.q', 'p']) {
    const el = L.querySelector(sel);
    if (!el) continue;
    const tn = [...el.childNodes].find(n => n.nodeType === 3 && n.textContent.trim());
    let cx = null, cy = null, firstWord = null;
    if (tn) {
      const m = tn.textContent.match(/\S+/);
      const r = document.createRange();
      r.setStart(tn, m.index); r.setEnd(tn, m.index + 1);
      const rr = r.getBoundingClientRect();
      cx = +rr.left.toFixed(1); cy = +(rr.top + rr.height/2).toFixed(1);
      firstWord = m[0];
    }
    const er = el.getBoundingClientRect();
    out.push({what:sel, text:el.textContent.trim().slice(0,30), elX:+er.left.toFixed(1),
              elR:+er.right.toFixed(1), firstCharX:cx, y:cy, firstWord,
              topEl: cx===null?null:(document.elementFromPoint(cx+1, cy).className||document.elementFromPoint(cx+1,cy).tagName)});
  }
  // stacking order check: which elements overlap the bar's right edge?
  const hit = document.elementFromPoint(br.right - 4, br.top + 24);
  out.push({what:'pointInsideBarRightEdge', el:hit ? (hit.className||hit.tagName) : null});
  return out;
})()
"""

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--force-device-scale-factor=1"])
    for w in [1024, 1280, 1440]:
        pg = b.new_page(viewport={"width": w, "height": 900})
        pg.goto("file:///" + PAGE.replace("\\", "/"))
        pg.wait_for_timeout(350)
        print("=" * 60, "\nVIEWPORT", w)
        for r in pg.evaluate(JS):
            print("  ", r)
        pg.locator(".layer.l1").screenshot(path=r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\hub\_qa\_tmp_l1_%d.png" % w)
        pg.close()
    b.close()
