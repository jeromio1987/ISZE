"""Focused hub paint probe — the hub draws bars as .brow/.mixbar, not .bar-row."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
import os
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")
from playwright.sync_api import sync_playwright

P = "02_dashboards/hub/ISZE_OS_Hub.html"
PROBE = r"""
() => {
  const q = s => document.querySelectorAll(s).length;
  const txt = document.body.innerText;
  return {
    kpis: q('.kpi'),
    chips: q('.chip'),
    brow: q('.brow'),
    mixbar: q('.mixbar'),
    btrack: q('.btrack'),
    nodes: q('.node'),
    tableRows: Array.from(document.querySelectorAll('table')).map(t=>t.querySelectorAll('tbody tr').length),
    tips: q('.tip'),
    textLen: txt.length,
    aimsentence: (txt.match(/[^.]*AIM[^.]*\./g) || []).slice(0, 4),
  };
}
"""
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 1000})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(("file:///" + os.path.abspath(P).replace("\\", "/")), wait_until="load")
    pg.wait_for_timeout(1200)
    r = pg.evaluate(PROBE)
    r["console_errors"] = errs
    print(json.dumps(r, indent=1)[:2000])
    pg.screenshot(path="02_dashboards/_build/_aim_refresh/_qa/hub_final.png")
    b.close()
