"""Paint check for the OS Hub and the OS Console, and a read of their AIM cells.

Neither page is being changed in this pass. This renders both from file:// in headless Chrome,
measures what paints, reads back the rendered text of the AIM cell on each, and writes one
screenshot per page so the receipts for this pass can name them.

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
    "02_dashboards/hub/ISZE_OS_Hub.html",
    "02_dashboards/ops/ISZE_OS_Console.html",
]

PROBE = r"""
() => {
  const q = s => document.querySelectorAll(s).length;
  const txt = document.body ? document.body.innerText : '';
  const canv = Array.from(document.querySelectorAll('canvas'));
  const tables = Array.from(document.querySelectorAll('table'));
  const rows = tables.map(t => t.querySelectorAll('tbody tr').length);
  const svgs = Array.from(document.querySelectorAll('svg'));
  const drawn = svgs.filter(s => s.querySelectorAll('path,rect,circle,line,polyline,polygon,text').length > 2).length;
  const aimHits = (txt.match(/unclassified/gi) || []).length;
  const lines = txt.split('\n').filter(s => /unclassified|98%|1\.8%|1\.6%|93\.5/i.test(s));
  return {
    title: document.title,
    textLen: txt.length,
    canvases: canv.length,
    kpi: q('.kpi'),
    chips: q('.chip'),
    tables: tables.length,
    tableRowsTotal: rows.reduce((a,b)=>a+b,0),
    tablesEmpty: rows.filter(n => n === 0).length,
    svgs: svgs.length,
    svgsDrawn: drawn,
    nanInText: /NaN/.test(txt),
    aimMentions: aimHits,
    aimLines: lines.slice(0, 8),
    scrollH: document.documentElement.scrollHeight
  };
}
"""

results = {}
with sync_playwright() as pw:
    browser = pw.chromium.launch(channel="chrome", headless=True)
    for rel in PAGES:
        p = ISZE / rel
        rec = {"page": rel}
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
            # the AIM cell is not always in the first screen; take a full-page one as well
            shot2 = QA / (slug + "__full.png")
            pg.screenshot(path=str(shot2), full_page=True)
            rec["shot_full"] = str(shot2)
            rec["console_errors"] = errs[:6]
        except Exception as e:
            rec["error"] = str(e)[:300]
        finally:
            pg.close()
        results[rel] = rec
        print(json.dumps(rec, ensure_ascii=False, indent=1)[:1600])
        print()
    browser.close()

out = ISZE / "02_dashboards" / "_build" / "_aim_pass2" / "paint_report_hub_console.json"
out.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
print("wrote", out)
print("pages rendered:", len(results), "| screenshots:",
      sum(1 for r in results.values() if r.get("shot")) + sum(1 for r in results.values() if r.get("shot_full")))
