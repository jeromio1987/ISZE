"""Paint check for the second AIM refresh pass.

Renders every rebuilt page from file:// in headless Chrome at 1440x1000, measures what
actually paints (canvases with ink, .bar-row rows, drawn SVG, tbody rows, headline text,
NaN, console errors) and writes one screenshot per page.

QA-internal, not a user-facing open.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright  # noqa: E402

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
QA = ISZE / "02_dashboards" / "_build" / "_aim_refresh2" / "_qa"
QA.mkdir(parents=True, exist_ok=True)

PAGES = [
    "02_dashboards/sales/ISZE_PMS_Tonnage_Evolution.html",
    "02_dashboards/sales/ISZE_PMS_Family_Compare.html",
    "02_dashboards/sales/ISZE_DB_DLR_Replenishment_CY2025.html",
    "02_dashboards/sales/AIM_Dashboard_CY2026.html",
    "02_dashboards/sales/ISZE_AIM_Classification_Paper.html",
    "02_dashboards/sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html",
    "02_dashboards/sales/ISZE_KPI_Dashboard.html",
    "02_dashboards/sales/ISZE_Lost_Sales_Model.html",
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source.html",
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.html",
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.html",
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_FX_20261001.html",
    "02_dashboards/pricing/ISZE_Pricing_Policy_Paper.html",
    "02_dashboards/pricing/ISZE_PMS_Price_Response_Brief_2026-09-22.html",
    "02_dashboards/pricing/ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html",
    "02_dashboards/pricing/ISZE_Price_Increase_5pct_Flat_SIMULATION_2026-09-22.html",
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
        print(json.dumps({k: v for k, v in rec.items() if k != "firstLines"}, ensure_ascii=False)[:420])
    browser.close()

out = ISZE / "02_dashboards" / "_build" / "_aim_refresh2" / "paint_report.json"
out.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
print("\nwrote", out)
print("pages rendered:", len(results),
      "| screenshots:", sum(1 for r in results.values() if r.get("shot")) + sum(1 for r in results.values() if r.get("shot_bottom")))
