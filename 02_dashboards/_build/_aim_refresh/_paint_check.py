"""Paint check for the AIM refresh — render each page from file://, measure what paints,
and write a screenshot per page. QA-internal, not a user-facing open."""
import json, os, sys, time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
os.chdir(ISZE)
QA = ISZE / "02_dashboards" / "_build" / "_aim_refresh" / "_qa"
QA.mkdir(parents=True, exist_ok=True)

PAGES = json.loads((ISZE / "02_dashboards" / "_build" / "_aim_refresh" / "pages.json").read_text(encoding="utf-8"))

PROBE = r"""
() => {
  const q = (s) => document.querySelectorAll(s).length;
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
  const nan = /NaN/.test(txt) || /NaN/.test(document.documentElement.innerHTML.slice(0, 4000000));
  return {
    title: document.title,
    textLen: txt.length,
    canvases: canv.length,
    canvasesPainted: painted,
    bars: q('.bar-row'),
    tables: tables.length,
    tableRowsTotal: tableRows.reduce((a,b)=>a+b,0),
    tablesEmpty: tableRows.filter(n => n === 0).length,
    svgs: svgs.length,
    svgsDrawn: drawnSvg,
    hasDataUnavailable: /DATA UNAVAILABLE/i.test(txt),
    nanInPage: nan,
    bodyBg: getComputedStyle(document.body).backgroundColor,
    innerWidth: window.innerWidth,
    scrollH: document.documentElement.scrollHeight
  };
}
"""

results = {}
with sync_playwright() as pw:
    browser = pw.chromium.launch(channel="chrome", headless=True)
    for entry in PAGES:
        rel = entry["page"]
        p = ISZE / rel
        rec = {"page": rel}
        if not p.is_file():
            rec["error"] = "missing"
            results[rel] = rec
            print("MISSING", rel)
            continue
        pg = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        try:
            pg.goto(p.as_uri(), wait_until="load", timeout=90000)
            # let charts settle
            try:
                pg.wait_for_timeout(3500)
            except Exception:
                pass
            rec.update(pg.evaluate(PROBE))
            shot = QA / (rel.replace("/", "__").replace(".html", "") + ".png")
            pg.screenshot(path=str(shot), full_page=False)
            if rec.get("scrollH", 0) > 4000:
                pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                pg.wait_for_timeout(1200)
                shot2 = QA / (rel.replace("/", "__").replace(".html", "") + "__bottom.png")
                pg.screenshot(path=str(shot2), full_page=False)
                rec["shot_bottom"] = str(shot2)
            rec["shot"] = str(shot)
            rec["console_errors"] = errs[:8]
        except Exception as e:
            rec["error"] = str(e)[:300]
            try:
                pg.screenshot(path=str(QA / (rel.replace("/", "__") + ".error.png")))
            except Exception:
                pass
        finally:
            pg.close()
        results[rel] = rec
        print(json.dumps(rec)[:400])
    browser.close()

out = ISZE / "02_dashboards" / "_build" / "_aim_refresh" / "paint_report.json"
out.write_text(json.dumps(results, indent=1), encoding="utf-8")
print("\nwrote", out)
