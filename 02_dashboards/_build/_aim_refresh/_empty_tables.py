import json, sys, os
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")
from playwright.sync_api import sync_playwright

PAGES = ["02_dashboards/sales/ISZE_AIM_DB_DLR_Deep_Dive_ALL.html",
         "02_dashboards/sales/ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.html"]
PROBE = r"""
() => {
  return Array.from(document.querySelectorAll('table')).map(t => ({
    id: t.id || t.closest('[id]') ? (t.closest('[id]')||{}).id : '',
    caption: (t.closest('section')||{}).querySelector ? ((t.closest('section').querySelector('h2,h3')||{}).innerText||'') : '',
    rows: t.querySelectorAll('tbody tr').length,
    text: (t.innerText||'').replace(/\s+/g,' ').slice(0,150),
    parentText: (t.parentElement.innerText||'').replace(/\s+/g,' ').slice(0,220)
  }));
}
"""
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", headless=True)
    for rel in PAGES:
        pg = b.new_page(viewport={"width": 1440, "height": 1000})
        pg.goto("file:///" + os.path.abspath(rel).replace("\\", "/"), wait_until="load")
        pg.wait_for_timeout(4000)
        print("=" * 6, rel)
        for r in pg.evaluate(PROBE):
            flag = "  <-- EMPTY" if r["rows"] == 0 else ""
            print(f"   rows={r['rows']:4} id={r['id'][:20]:20} {r['caption'][:60]}{flag}")
            if r["rows"] == 0:
                print("        table text :", r["text"])
                print("        parent     :", r["parentText"])
        pg.close()
    b.close()
