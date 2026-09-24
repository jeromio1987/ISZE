import sys, os
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")
from playwright.sync_api import sync_playwright

CASES = [("02_dashboards/sales/ISZE_AIM_DB_DLR_Deep_Dive_ALL.html", "dealer-card"),
         ("02_dashboards/sales/ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.html", "dealer-card"),
         ("02_dashboards/sales/ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.html", "s6")]
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", headless=True)
    for rel, cid in CASES:
        pg = b.new_page(viewport={"width": 1440, "height": 1000})
        pg.goto("file:///" + os.path.abspath(rel).replace("\\", "/"), wait_until="load")
        pg.wait_for_timeout(3500)
        txt = pg.evaluate("""(id) => {
            const c = document.getElementById(id);
            if (!c) return 'NO SUCH CARD ' + id;
            return c.innerText.replace(/\\s+/g,' ').slice(0, 600);
        }""", cid)
        print("=" * 6, rel, "#" + cid)
        print("   ", txt)
        pg.close()
    b.close()
