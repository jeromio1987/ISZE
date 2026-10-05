"""Render a page with the real Chrome binary and report what actually painted.

Counts league rows, chart rows, hero figures, and any JS console/page errors.
Used to compare the rebuilt source page against the deploy mirror, both of which
were produced from the same builder.

Usage: python _render_check.py <html-path> [label]
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
path = pathlib.Path(sys.argv[1]).resolve()
label = sys.argv[2] if len(sys.argv) > 2 else path.name

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME, headless=True,
                                 args=["--hide-scrollbars"])
    page = browser.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    page.on("console", lambda m: errors.append(f"{m.type}: {m.text}")
            if m.type == "error" else None)
    page.goto(path.as_uri(), wait_until="load")
    page.wait_for_timeout(900)
    res = page.evaluate(
        """() => {
        const q=(s)=>document.querySelector(s);
        const n=(s)=>document.querySelectorAll(s).length;
        const t=(s)=>{const e=q(s);return e?e.textContent.trim():null;};
        return {
          title: document.title,
          hero_gap: t('.hstats .hstat:nth-child(1) .v'),
          hero_nb: t('#hero-nb'), hero_cap: t('#hero-cap'),
          hero_billed: t('#hero-billed'), hero_rep: t('#hero-rep'),
          league_rows: n('#league-tbody tr'),
          league_foot: n('#league-foot tr'),
          c1: n('#c1-rows .brow'), c2: n('#c2-rows .brow'), c3: n('#c3-rows .brow'),
          c4: n('#c4-rows .brow'), c5: n('#c5-rows .brow'), c6: n('#c6-rows .brow'),
          noprice_rows: n('table tbody tr'),
          undefined_txt: (document.body.innerText.match(/undefined|NaN/g)||[]).length,
        };}""")
    browser.close()

print(f"=== {label} ===")
print("path:", path)
for k, v in res.items():
    print(f"  {k}: {v}")
print("  js_errors:", errors if errors else "clean")
