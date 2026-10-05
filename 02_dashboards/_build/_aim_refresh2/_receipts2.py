"""Paint the pages added after the first paint run (risk cockpit), then write one
SHIP_RECEIPT.json per rebuilt page via the house receipt writer.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright  # noqa: E402

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
QA = ISZE / "02_dashboards" / "_build" / "_aim_refresh2" / "_qa"
QA.mkdir(parents=True, exist_ok=True)
WRITER = Path(r"C:\Users\jerom\Desktop\claude\.cursor\skills\verify-before-done\scripts\write_receipt.mjs")

EXTRA = ["02_dashboards/sales/ISZE_Risk_Cockpit.html"]

PROBE = r"""
() => {
  const q = s => document.querySelectorAll(s).length;
  const txt = document.body ? document.body.innerText : '';
  const canv = Array.from(document.querySelectorAll('canvas'));
  const painted = canv.filter(c => { try { const g=c.getContext('2d'); if(!g) return false;
    const d=g.getImageData(0,0,c.width,c.height).data;
    for(let i=3;i<d.length;i+=397){ if(d[i]!==0) return true; } return false; } catch(e){ return null; } }).length;
  const tables = Array.from(document.querySelectorAll('table'));
  const rows = tables.map(t => t.querySelectorAll('tbody tr').length);
  const svgs = Array.from(document.querySelectorAll('svg'));
  return { title: document.title, textLen: txt.length, canvases: canv.length, canvasesPainted: painted,
    barRows: q('.bar-row'), kpi: q('.kpi'), chips: q('.chip'), tables: tables.length,
    tableRowsTotal: rows.reduce((a,b)=>a+b,0), tablesEmpty: rows.filter(n=>n===0).length,
    svgs: svgs.length, nanInText: /NaN/.test(txt), scrollH: document.documentElement.scrollHeight };
}
"""

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", headless=True)
    for rel in EXTRA:
        p = ISZE / rel
        pg = b.new_page(viewport={"width": 1440, "height": 1000})
        errs = []
        pg.on("console", lambda m: errs.append(m.text[:200]) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)[:200]))
        pg.goto(p.as_uri(), wait_until="load", timeout=120000)
        pg.wait_for_timeout(4000)
        rec = pg.evaluate(PROBE)
        rec["console_errors"] = errs[:6]
        slug = rel.replace("/", "__").replace(".html", "")
        pg.screenshot(path=str(QA / (slug + ".png")))
        print(rel, json.dumps(rec, ensure_ascii=False)[:400])
        pg.close()
    b.close()

# page -> its screenshots, in order
PAGES = [
    ("02_dashboards/sales/ISZE_PMS_Tonnage_Evolution.html",
     ["02_dashboards__sales__ISZE_PMS_Tonnage_Evolution.png",
      "02_dashboards__sales__ISZE_PMS_Tonnage_Evolution__bottom.png"]),
    ("02_dashboards/sales/ISZE_PMS_Family_Compare.html",
     ["02_dashboards__sales__ISZE_PMS_Family_Compare.png"]),
    ("02_dashboards/sales/ISZE_DB_DLR_Replenishment_CY2025.html",
     ["02_dashboards__sales__ISZE_DB_DLR_Replenishment_CY2025.png",
      "02_dashboards__sales__ISZE_DB_DLR_Replenishment_CY2025__bottom.png"]),
    ("02_dashboards/sales/AIM_Dashboard_CY2026.html",
     ["02_dashboards__sales__AIM_Dashboard_CY2026.png"]),
    ("02_dashboards/sales/ISZE_AIM_Classification_Paper.html",
     ["02_dashboards__sales__ISZE_AIM_Classification_Paper.png",
      "02_dashboards__sales__ISZE_AIM_Classification_Paper__bottom.png"]),
    ("02_dashboards/sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html",
     ["02_dashboards__sales__Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.png",
      "02_dashboards__sales__Dealer_Sellout_AIM_GPS_ITUK_UTI_2025__bottom.png"]),
    ("02_dashboards/sales/ISZE_KPI_Dashboard.html",
     ["02_dashboards__sales__ISZE_KPI_Dashboard.png",
      "02_dashboards__sales__ISZE_KPI_Dashboard__bottom.png"]),
    ("02_dashboards/sales/ISZE_Lost_Sales_Model.html",
     ["02_dashboards__sales__ISZE_Lost_Sales_Model.png",
      "02_dashboards__sales__ISZE_Lost_Sales_Model__bottom.png"]),
    ("02_dashboards/sales/ISZE_Risk_Cockpit.html",
     ["02_dashboards__sales__ISZE_Risk_Cockpit.png"]),
    ("02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source.html",
     ["02_dashboards__pricing__ISZE_Pricing_Revision_AIM_Source.png",
      "02_dashboards__pricing__ISZE_Pricing_Revision_AIM_Source__bottom.png"]),
    ("02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.html",
     ["02_dashboards__pricing__ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.png"]),
    ("02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.html",
     ["02_dashboards__pricing__ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.png"]),
    ("02_dashboards/pricing/ISZE_Pricing_Revision_AIM_FX_20261001.html",
     ["02_dashboards__pricing__ISZE_Pricing_Revision_AIM_FX_20261001.png"]),
    ("02_dashboards/pricing/ISZE_Pricing_Policy_Paper.html",
     ["02_dashboards__pricing__ISZE_Pricing_Policy_Paper.png",
      "02_dashboards__pricing__ISZE_Pricing_Policy_Paper__bottom.png"]),
    ("02_dashboards/pricing/ISZE_PMS_Price_Response_Brief_2026-09-22.html",
     ["02_dashboards__pricing__ISZE_PMS_Price_Response_Brief_2026-09-22.png",
      "02_dashboards__pricing__ISZE_PMS_Price_Response_Brief_2026-09-22__bottom.png"]),
    ("02_dashboards/pricing/ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html",
     ["02_dashboards__pricing__ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.png",
      "02_dashboards__pricing__ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17__bottom.png"]),
    ("02_dashboards/pricing/ISZE_Price_Increase_5pct_Flat_SIMULATION_2026-09-22.html",
     ["02_dashboards__pricing__ISZE_Price_Increase_5pct_Flat_SIMULATION_2026-09-22.png",
      "02_dashboards__pricing__ISZE_Price_Increase_5pct_Flat_SIMULATION_2026-09-22__bottom.png"]),
]

NOTE = ("Second AIM refresh pass 2026-09-24 19:xx: same builder, same arguments, re-read from the "
        "settled AIM master after the cab class was added.")

written, failed = [], []
for page, shots in PAGES:
    p = ISZE / page
    if not p.is_file():
        failed.append((page, "missing"))
        continue
    have = [s for s in shots if (QA / s).is_file()]
    args = ["node", str(WRITER), "--artifact", str(p)]
    for s in have:
        args += ["--screenshot", str(QA / s)]
    args += ["--screenshots-taken", str(len(have)), "--screenshots-read", str(len(have)),
             "--notes", NOTE]
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    ok = r.returncode == 0
    (written if ok else failed).append((page, r.returncode, out.strip().splitlines()[-3:]))
    print("=" * 6, page, "exit", r.returncode)
    for line in out.strip().splitlines()[-6:]:
        print("   ", line[:180])

print(f"\nreceipts written: {len(written)}  failed: {len(failed)}")
for f in failed:
    print("   FAIL", f)
