import json, os, sys
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")
from playwright.sync_api import sync_playwright

QA = "02_dashboards/_build/_aim_refresh/_qa"
PAGES = [
    "02_dashboards/sales/ISZE_AIM_DB_DLR_Deep_Dive_ALL.html",
    "02_dashboards/sales/ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.html",
    "02_dashboards/sales/ISZE_AIM_Comparison_ALL.html",
    "02_dashboards/sales/ISZE_AIM_Comparison_PORTUGAL.html",
]
PROBE = r"""
() => {
  const q = s => document.querySelectorAll(s).length;
  const txt = document.body.innerText;
  const canv = Array.from(document.querySelectorAll('canvas'));
  const painted = canv.filter(c => { try {
      const g=c.getContext('2d'); if(!g) return false;
      const d=g.getImageData(0,0,c.width,c.height).data;
      for(let i=3;i<d.length;i+=397) if(d[i]!==0) return true;
      return false; } catch(e){ return null; } }).length;
  return { title: document.title, textLen: txt.length,
           canvases: canv.length, canvasesPainted: painted, bars: q('.bar-row'),
           tables: q('table'),
           tableRows: Array.from(document.querySelectorAll('table')).map(t=>t.querySelectorAll('tbody tr').length),
           visibleNaN: /NaN/.test(txt), scrollH: document.documentElement.scrollHeight };
}
"""
res = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", headless=True)
    for rel in PAGES:
        pg = b.new_page(viewport={"width": 1440, "height": 1000})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.goto("file:///" + os.path.abspath(rel).replace("\\", "/"), wait_until="load")
        pg.wait_for_timeout(4000)
        r = pg.evaluate(PROBE)
        r["console_errors"] = errs
        name = rel.replace("/", "__").replace(".html", "")
        pg.screenshot(path=f"{QA}/{name}.png")
        pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        pg.wait_for_timeout(1500)
        pg.screenshot(path=f"{QA}/{name}__bottom.png")
        res[rel] = r
        pg.close()
        print(rel, json.dumps({k: v for k, v in r.items() if k != "tableRows"}))
        print("    tableRows", r["tableRows"])
    b.close()
json.dump(res, open("02_dashboards/_build/_aim_refresh/paint_report_rerun.json", "w", encoding="utf-8"), indent=1)
