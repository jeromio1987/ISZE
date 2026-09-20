"""Focused QA capture of the excluded section (the block changed in this pass).

Takes a tight clip at three widths so the new copy can be read at full
resolution: does the excluded table paint, do the plain-language labels and the
"whose it is" column fit, does the lubricant sub-table show its rows.
"""
import io
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
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME, headless=True)
    for w in (1440, 1280, 390):
        ctx = br.new_context(viewport={"width": w, "height": 900}, device_scale_factor=1)
        page = ctx.new_page()
        page.goto(URL)
        page.wait_for_timeout(1200)
        # the excluded heading and everything after it up to the judgements block
        box = page.evaluate(
            """() => {
              const h = [...document.querySelectorAll('h2')]
                .find(e => e.textContent.includes('What this comparison does not cover'));
              const end = document.querySelector('.warn');
              const a = h.getBoundingClientRect(), b = end.getBoundingClientRect();
              return {top: a.top + window.scrollY - 20,
                      bottom: b.top + window.scrollY - 10};
            }"""
        )
        p = os.path.join(QA, f"04_excluded_w{w}.png")
        page.screenshot(path=p, full_page=True,
                        clip={"x": 0, "y": max(0, box["top"]),
                              "width": w, "height": max(60, box["bottom"] - box["top"])},
                        animations="disabled")
        taken.append(p)
        ctx.close()
    br.close()

print("EXCLUDED SECTION SHOTS:", len(taken))
for t in taken:
    print(" ", os.path.basename(t), f"{os.path.getsize(t):,} bytes")
