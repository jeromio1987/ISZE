import os, json
from playwright.sync_api import sync_playwright
BASE = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected"
QA = os.path.join(BASE, "_qa")
out = {}
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    for fn, sel, png in [
        ("04_ISZE_AIM_Classification_Paper.html", ".basis-strip", "defectfix_04b_basis.png"),
        ("07_ISZE_Pricing_Revision_AIM_Source.html", ".basis-strip", "defectfix_07b_basis.png"),
    ]:
        pg = b.new_page(viewport={"width": 1440, "height": 1200})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("file:///" + os.path.join(BASE, fn).replace("\\", "/"), wait_until="load")
        pg.wait_for_timeout(1800)
        txt = pg.evaluate("s => { const e=document.querySelector(s); return e? e.textContent.replace(/\\s+/g,' ').trim():null; }", sel)
        kpi = pg.evaluate("() => { const e=document.querySelector('.kpi .val, .hero .val, h1'); return e? e.textContent.replace(/\\s+/g,' ').trim():null; }")
        out[fn] = {"errors": errs, "basis": txt, "first_big_text": kpi}
        el = pg.query_selector(sel)
        if el:
            el.screenshot(path=os.path.join(QA, png))
        pg.close()
    b.close()
with open(os.path.join(QA, "_runtime_probe_basis.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
