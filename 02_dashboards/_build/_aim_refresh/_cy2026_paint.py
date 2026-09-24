"""Render the AIM CY2026 page (its data file changed) and measure what paints."""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")
from playwright.sync_api import sync_playwright

P = "02_dashboards/sales/AIM_Dashboard_CY2026.html"
QA = "02_dashboards/_build/_aim_refresh/_qa"
PROBE = r"""
() => {
  const q = s => document.querySelectorAll(s).length;
  const txt = document.body.innerText;
  const canv = Array.from(document.querySelectorAll('canvas'));
  const painted = canv.filter(c => { try {
      const g = c.getContext('2d'); if (!g) return false;
      const d = g.getImageData(0,0,c.width,c.height).data;
      for (let i=3;i<d.length;i+=397) if (d[i]!==0) return true;
      return false; } catch(e){ return null; } }).length;
  return { title: document.title, textLen: txt.length,
           canvases: canv.length, canvasesPainted: painted,
           bars: q('.bar-row'), tables: q('table'),
           tableRows: Array.from(document.querySelectorAll('table')).map(t=>t.querySelectorAll('tbody tr').length),
           hasData: typeof window.__AIM_CY2026_DATA__ !== 'undefined',
           basisNote: (document.getElementById('basis-note')||{}).innerText,
           trust: (document.getElementById('trust-strip')||{}).innerText,
           l1: Array.from(document.querySelectorAll('#chart-l1 .bar-row')).map(r=>r.innerText.slice(0,60)).slice(0,3),
           visibleNaN: /NaN/.test(txt) };
}
"""
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 1000})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto("file:///" + os.path.abspath(P).replace("\\", "/"), wait_until="load")
    pg.wait_for_timeout(4000)
    r = pg.evaluate(PROBE)
    r["console_errors"] = errs
    print(json.dumps(r, indent=1))
    pg.screenshot(path=QA + "/02_dashboards__sales__AIM_Dashboard_CY2026.png")
    pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    pg.wait_for_timeout(1500)
    pg.screenshot(path=QA + "/02_dashboards__sales__AIM_Dashboard_CY2026__bottom.png")
    b.close()
