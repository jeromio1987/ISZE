"""Paint check for the second publish pass, 24 September 2026.

Renders the four rebuilt AIM pages from file:// in headless Chrome at 1440x1000, measures what
actually paints (canvas ink, bar rows, drawn SVG, tbody rows, headline text, NaN, console errors)
and writes the screenshots. One screenshot per page, plus a bottom-of-page shot for any page taller
than 4,000 px.

QA-internal, not a user-facing open.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright  # noqa: E402

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
QA = ISZE / "02_dashboards" / "_build" / "_aim_pass2" / "_qa"
QA.mkdir(parents=True, exist_ok=True)

PAGES = [
    "02_dashboards/sales/ISZE_AIM_DB_DLR_Deep_Dive_ALL.html",
    "02_dashboards/sales/ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.html",
    "02_dashboards/sales/ISZE_AIM_Comparison_ALL.html",
    "02_dashboards/sales/ISZE_AIM_Comparison_PORTUGAL.html",
]

PROBE = r"""
() => {
  const q = s => document.querySelectorAll(s).length;
  const txt = document.body ? document.body.innerText : '';
  const canv = Array.from(document.querySelectorAll('canvas'));
  const painted = canv.filter(c => {
    try {
      const g = c.getContext('2d');
      if (!g) return false;
      const d = g.getImageData(0, 0, c.width, c.height).data;
      for (let i = 3; i < d.length; i += 397) { if (d[i] !== 0) return true; }
      return false;
    } catch (e) { return null; }
  }).length;
  const tables = Array.from(document.querySelectorAll('table'));
  const tableRows = tables.map(t => t.querySelectorAll('tbody tr').length);
  const svgs = Array.from(document.querySelectorAll('svg'));
  const drawnSvg = svgs.filter(s => s.querySelectorAll('path,rect,circle,line,polyline,polygon,text').length > 2).length;
  const nan = /NaN/.test(txt);
  const euroHits = (txt.match(/EUR|€|\$|�/g) || []).length;
  return {
    title: document.title,
    textLen: txt.length,
    canvases: canv.length,
    canvasesPainted: painted,
    barRows: q('.bar-row'),
    brow: q('.brow'),
    kpi: q('.kpi'),
    chips: q('.chip'),
    tables: tables.length,
    tableRowsTotal: tableRows.reduce((a,b)=>a+b,0),
    tablesEmpty: tableRows.filter(n => n === 0).length,
    svgs: svgs.length,
    svgsDrawn: drawnSvg,
    hasDataUnavailable: /DATA UNAVAILABLE/i.test(txt),
    nanInText: nan,
    eurosInText: euroHits,
    scrollH: document.documentElement.scrollHeight,
    firstLines: txt.split('\n').filter(s => s.trim()).slice(0, 14)
  };
}
"""

results = {}
with sync_playwright() as pw:
    browser = pw.chromium.launch(channel="chrome", headless=True)
    for rel in PAGES:
        p = ISZE / rel
        rec = {"page": rel}
        if not p.is_file():
            rec["error"] = "missing"
            results[rel] = rec
            print("MISSING", rel)
            continue
        pg = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        errs = []
        pg.on("console", lambda m: errs.append(m.text[:200]) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)[:200]))
        try:
            pg.goto(p.as_uri(), wait_until="load", timeout=120000)
            pg.wait_for_timeout(4000)
            rec.update(pg.evaluate(PROBE))
            slug = rel.replace("/", "__").replace(".html", "")
            shot = QA / (slug + ".png")
            pg.screenshot(path=str(shot))
            rec["shot"] = str(shot)
            if rec.get("scrollH", 0) > 4000:
                pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                pg.wait_for_timeout(1500)
                shot2 = QA / (slug + "__bottom.png")
                pg.screenshot(path=str(shot2))
                rec["shot_bottom"] = str(shot2)
            rec["console_errors"] = errs[:6]
        except Exception as e:
            rec["error"] = str(e)[:300]
        finally:
            pg.close()
        results[rel] = rec
        print(json.dumps({k: v for k, v in rec.items() if k != "firstLines"},
                         ensure_ascii=False)[:420])
    browser.close()

out = ISZE / "02_dashboards" / "_build" / "_aim_pass2" / "paint_report.json"
out.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
print("\nwrote", out)
print("pages rendered:", len(results),
      "| screenshots:", sum(1 for r in results.values() if r.get("shot"))
      + sum(1 for r in results.values() if r.get("shot_bottom")))
