"""Focused QA capture of the part-number table (the block changed in this pass).

Tight clips at 1440 and 390 so the new Description column can be read at full
resolution, plus a measurement of the description cell against its container to
prove long text wraps instead of clipping or widening the panel.
"""
import io
import json
import os
import sys

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
HTML = os.path.join(ROOT, "02_dashboards", "pricing",
                    "ISZE_Price_BP_Weighted_Compare.html")
QA = os.path.join(ROOT, "02_dashboards", "pricing", "_qa_bp_weighted")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL = "file:///" + HTML.replace("\\", "/")

taken = []
measure = {}
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME, headless=True)
    for w in (1440, 390):
        ctx = br.new_context(viewport={"width": w, "height": 900}, device_scale_factor=1)
        page = ctx.new_page()
        page.goto(URL)
        page.wait_for_timeout(1400)
        box = page.evaluate(
            """() => {
              const h = [...document.querySelectorAll('h2')]
                .find(e => e.textContent.includes('carry the most euro'));
              const r = h.getBoundingClientRect();
              return {top: r.top + window.scrollY - 12};
            }"""
        )
        p = os.path.join(QA, f"05_pntable_w{w}.png")
        page.screenshot(path=p, full_page=True,
                        clip={"x": 0, "y": max(0, box["top"]),
                              "width": w, "height": min(700, 4000)},
                        animations="disabled")
        taken.append(p)

        # measure: does the description column overflow its own cell or the panel?
        measure[w] = page.evaluate(
            """() => {
              const table = document.getElementById('pnBody').closest('table');
              const scroller = table.closest('.scroll');
              const rows = [...document.querySelectorAll('#pnBody tr')];
              const desc = rows.map(tr => tr.children[1]);
              const longest = desc.reduce((a, b) =>
                (a && a.innerText.length > b.innerText.length) ? a : b, null);
              return {
                tableWidth: table.getBoundingClientRect().width,
                scrollWidth: scroller.scrollWidth,
                clientWidth: scroller.clientWidth,
                docScrollWidth: document.documentElement.scrollWidth,
                viewport: window.innerWidth,
                clippedCells: desc.filter(td => td.scrollWidth > td.clientWidth + 2).length,
                descRows: desc.length,
                emptyDesc: desc.filter(td => !td.innerText.trim()).length,
                longestText: longest ? longest.innerText.trim() : '',
                longestCellH: longest ? Math.round(longest.getBoundingClientRect().height) : 0,
                longestScrollH: longest ? longest.scrollHeight : 0,
              };
            }"""
        )
        ctx.close()
    br.close()

print("PART-NUMBER TABLE SHOTS:", len(taken))
for t in taken:
    print(" ", os.path.basename(t), f"{os.path.getsize(t):,} bytes")
print()
print(json.dumps(measure, indent=2))
