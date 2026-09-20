import os, json
from playwright.sync_api import sync_playwright

BASE = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected"
QA = os.path.join(BASE, "_qa")
out = {}
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 1400})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("file:///" + os.path.join(BASE, "10_Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html").replace("\\", "/"), wait_until="load")
    pg.wait_for_timeout(800)
    txt = pg.evaluate("() => document.querySelector('.callout').textContent.replace(/\\s+/g,' ').trim()")
    out["f10_callout"] = txt
    out["errors"] = errs
    el = pg.query_selector(".callout")
    if el:
        el.screenshot(path=os.path.join(QA, "defectfix_10c_scope_callout.png"))
    basis = pg.evaluate("() => document.querySelector('.basis-strip').textContent.replace(/\\s+/g,' ').trim()")
    out["f10_basis"] = basis
    pg.screenshot(path=os.path.join(QA, "defectfix_10d_top_runtime.png"))
    b.close()
with open(os.path.join(QA, "_runtime_probe_f10.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
