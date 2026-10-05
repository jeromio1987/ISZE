"""Check the 390px legend rule: size, overlap, and whether it sits over a bar."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

HTML = Path(__file__).resolve().parent.parent / "ISZE_OS_Console.html"

JS = r"""
() => {
  const rows = [...document.querySelectorAll('.bar-row')];
  let worst = null;
  const overlaps = [];
  for (const r of rows) {
    const w = r.querySelector('.legend-rule');
    if (!w) continue;
    const wr = w.getBoundingClientRect();
    const s = w.querySelector('.rule-txt');
    const sr = s ? s.getBoundingClientRect() : null;
    const fill = r.querySelector('.fill').getBoundingClientRect();
    const bad = [];
    if (s && sr) {
      if (sr.right > wr.right - 8) bad.push('legend text hits right edge');
      for (const b of 'volume,price,mix'.split(',')) {
        const sp = r.querySelector('.sw.' + b);
        if (!sp) continue;
        const br = sp.getBoundingClientRect();
        if (sr && !(sr.bottom <= br.top || sr.top >= br.bottom ||
                    sr.right <= br.left || sr.left >= br.right)) bad.push('touches ' + b);
      }
    }
    const info = {label: (r.querySelector('.bl')||{}).innerText||'', rule: [Math.round(wr.left), Math.round(wr.top), Math.round(wr.width), Math.round(wr.height)],
                  txt: s ? s.innerText : '', fillRight: Math.round(fill.right), issues: bad};
    overlaps.push(info);
    if (bad.length && !worst) worst = info;
  }
  return {count: overlaps.length, rows: overlaps, worst: worst,
          docW: document.documentElement.scrollWidth, innerW: window.innerWidth};
}
"""

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True, args=["--disable-gpu"])
    for w in (390, 768, 1024):
        pg = b.new_context(viewport={"width": w, "height": 900}).new_page()
        pg.goto(HTML.as_uri(), wait_until="load")
        pg.wait_for_timeout(500)
        r = pg.evaluate(JS)
        print(w, "docW", r["docW"], "innerW", r["innerW"], "rows with legend", r["count"])
        for info in r["rows"][:6]:
            print("   ", info["label"][:26], "rule", info["rule"], "|", info["txt"][:44],
                  "| fillRight", info["fillRight"], "| issues", info["issues"])
        print("    worst:", r["worst"])
    b.close()
