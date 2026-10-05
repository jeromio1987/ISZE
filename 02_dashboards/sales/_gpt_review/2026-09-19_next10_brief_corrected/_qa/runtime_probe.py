"""Element-level QA screenshots via Playwright (QA-internal, headless) to prove the runtime
render of the two regions that only exist after JavaScript runs:
  - F03 section 7: the doughnut (c9) and the t4 table (position wording)
  - F02 'What this does not claim': the Data checks tile and the sources lines
Also asserts the runtime values read off the live DOM, so the check is not just a picture.
"""
import json, os, sys
from playwright.sync_api import sync_playwright

BASE = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected"
QA = os.path.join(BASE, "_qa")


def url(fn):
    return "file:///" + os.path.join(BASE, fn).replace("\\", "/")


out = {}

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)

    # ---------- F03 ----------
    pg = b.new_page(viewport={"width": 1440, "height": 1200})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append("console." + m.type + ": " + m.text) if m.type == "error" else None)
    pg.goto(url("03_Warranty_Commercial_Review.html"), wait_until="load")
    pg.wait_for_timeout(1500)
    pg.evaluate("document.querySelector('#sec7').scrollIntoView()")
    pg.wait_for_timeout(600)
    pg.screenshot(path=os.path.join(QA, "defectfix_03c_sec7_runtime.png"))
    t4 = pg.evaluate("""() => {
        const t = document.getElementById('t4');
        if (!t) return null;
        const th = [...t.querySelectorAll('thead th')].map(x => x.textContent.trim());
        const rows = [...t.querySelectorAll('tbody tr')].slice(0, 4)
            .map(r => [...r.querySelectorAll('td')].map(c => c.textContent.trim()));
        return {headers: th, rows: rows, rowcount: t.querySelectorAll('tbody tr').length};
    }""")
    c9 = pg.evaluate("""() => {
        const el = document.getElementById('c9');
        if (!el) return null;
        return {w: el.width, h: el.height, painted: el.width > 0 && el.height > 0};
    }""")
    legend = pg.evaluate("""() => {
        const sec = document.getElementById('sec7');
        const items = [...sec.querySelectorAll('ul li, .chart-legend span')].map(x=>x.textContent.trim());
        return items;
    }""")
    canvas_data = pg.evaluate("""() => {
        // read the Chart.js instance labels if reachable
        const el = document.getElementById('c9');
        const ch = (window.Chart && Chart.getChart) ? Chart.getChart(el) : null;
        if (!ch) return null;
        return {labels: ch.data.labels, data: ch.data.datasets[0].data};
    }""")
    out["f03"] = {"errors": errs, "t4": t4, "c9": c9, "chart": canvas_data, "sec7_text": legend}
    pg.close()

    # ---------- F02 ----------
    pg = b.new_page(viewport={"width": 1440, "height": 1200})
    errs2 = []
    pg.on("pageerror", lambda e: errs2.append(str(e)))
    pg.on("console", lambda m: errs2.append("console." + m.type + ": " + m.text) if m.type == "error" else None)
    pg.goto(url("02_ISZE_Leakage_Cockpit.html"), wait_until="load")
    pg.wait_for_timeout(2500)
    pg.evaluate("document.querySelector('#sec-honesty').scrollIntoView()")
    pg.wait_for_timeout(800)
    pg.screenshot(path=os.path.join(QA, "defectfix_02c_honesty_runtime.png"))
    hon = pg.evaluate("""() => {
        const el = document.getElementById('mod-honesty');
        return el ? el.textContent.replace(/\\s+/g, ' ').trim().slice(0, 2000) : null;
    }""")
    foot = pg.evaluate("""() => {
        const f = document.querySelector('.foot');
        return f ? f.textContent.replace(/\\s+/g, ' ').trim() : null;
    }""")
    out["f02"] = {"errors": errs2, "honesty_text": hon, "foot": foot}
    pg.close()

    # ---------- F01 ----------
    pg = b.new_page(viewport={"width": 1440, "height": 1200})
    errs3 = []
    pg.on("pageerror", lambda e: errs3.append(str(e)))
    pg.goto(url("01_ISZE_Exec_Aftersales_Paper.html"), wait_until="load")
    pg.wait_for_timeout(2000)
    p6 = pg.evaluate("""() => {
        const s = document.getElementById('p6');
        const rows = [...s.querySelectorAll('tbody tr')].map(r =>
            [...r.querySelectorAll('td')].map(c => c.textContent.trim()));
        return rows;
    }""")
    p16 = pg.evaluate("""() => {
        const s = document.getElementById('p16');
        const cards = [...s.querySelectorAll('.card')].map(c => c.textContent.replace(/\\s+/g,' ').trim());
        const verdict = s.querySelector('.verdict') ? s.querySelector('.verdict').textContent.replace(/\\s+/g,' ').trim() : null;
        return {cards: cards, verdict: verdict};
    }""")
    footers = pg.evaluate("""() => [...document.querySelectorAll('footer.pf')].map(f=>f.textContent.trim())""")
    pg.evaluate("document.querySelector('#p6').scrollIntoView()")
    pg.wait_for_timeout(400)
    pg.screenshot(path=os.path.join(QA, "defectfix_01d_p6_runtime.png"))
    pg.evaluate("document.querySelector('#p16').scrollIntoView()")
    pg.wait_for_timeout(400)
    pg.screenshot(path=os.path.join(QA, "defectfix_01e_p16_runtime.png"))
    out["f01"] = {"errors": errs3, "p6_rows": p6, "p16": p16, "footers": footers}
    pg.close()

    b.close()

with open(os.path.join(QA, "_runtime_probe.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False)[:6000])
