# -*- coding: utf-8 -*-
"""Temp: probe the 'does not repeat' section for static overlap / collision."""
import sys
from playwright.sync_api import sync_playwright

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PAGE = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\hub\ISZE_OS_Hub.html"
OUT = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\hub\_qa"
sys.stdout.reconfigure(encoding="utf-8")

JS = r"""
(() => {
  const out = [];
  const sec = document.querySelector('#carry');
  const tbl = sec.querySelector('table.t');
  out.push({what:'section #carry box', r: JSON.stringify(sec.getBoundingClientRect())});
  const th = [...tbl.querySelectorAll('thead th')];
  th.forEach((t,i) => {
    const r = t.getBoundingClientRect();
    const cs = getComputedStyle(t);
    out.push({what:'TH'+i, text:t.textContent.trim(), x:+r.left.toFixed(1), r:+r.right.toFixed(1),
              y:+r.top.toFixed(1), b:+r.bottom.toFixed(1), w:+r.width.toFixed(1),
              pos:cs.position, top:cs.top, z:cs.zIndex, bg:cs.backgroundColor, col:cs.color});
  });
  [...tbl.querySelectorAll('tbody tr')].forEach((tr,i) => {
    const r = tr.getBoundingClientRect();
    out.push({what:'TR'+i, y:+r.top.toFixed(1), b:+r.bottom.toFixed(1), h:+r.height.toFixed(1),
              cls:tr.className, txt:tr.textContent.trim().slice(0,50)});
  });
  // does the first body row sit under the sticky header (same y band)?
  const body0 = tbl.querySelector('tbody tr').getBoundingClientRect();
  const head0 = tbl.querySelector('thead').getBoundingClientRect();
  out.push({what:'header bottom vs body top', headBottom:+head0.bottom.toFixed(1), bodyTop:+body0.top.toFixed(1),
            overlap:+(head0.bottom - body0.top).toFixed(1)});
  // jcard overflow
  [...sec.querySelectorAll('.jcard')].forEach((c,i) => {
    const r = c.getBoundingClientRect();
    const cs = getComputedStyle(c);
    out.push({what:'jcard'+i, x:+r.left.toFixed(1), r:+r.right.toFixed(1), w:+r.width.toFixed(1),
              sw:c.scrollWidth, cw:c.clientWidth, h:+r.height.toFixed(1),
              childrenOverflow: [...c.children].some(k => k.getBoundingClientRect().right > r.right + 1 ||
                                                          k.getBoundingClientRect().bottom > r.bottom + 1)});
  });
  return out;
})()
"""

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--force-device-scale-factor=1"])
    for w in [1024, 1440, 390]:
        pg = b.new_page(viewport={"width": w, "height": 1000})
        pg.goto("file:///" + PAGE.replace("\\", "/"))
        pg.wait_for_timeout(400)
        print("=" * 60, "\nVIEWPORT", w)
        for r in pg.evaluate(JS):
            print("  ", r)
        pg.locator("#carry").screenshot(path=OUT + r"\_tmp_carry_%d.png" % w)
        pg.close()
    b.close()
