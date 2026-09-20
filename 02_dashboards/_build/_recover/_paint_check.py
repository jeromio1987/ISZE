"""Programmatic paint check on the rendered page.

Queries the live DOM for the figures the correction is about, so the claim
"the page shows 2,247,884 / 1,934" is evidence from the rendered page rather
than from the source text.
"""
import pathlib

from playwright.sync_api import sync_playwright

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
HTML = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_DB_Leakage_Review_CY2025.html")

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME, headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto(HTML.as_uri(), wait_until="load")
    page.wait_for_timeout(800)

    res = page.evaluate(
        """() => {
        const q=(s)=>document.querySelector(s);
        const txt=(s)=>{const e=q(s);return e?e.textContent.trim():null;};
        const n=(s)=>document.querySelectorAll(s).length;
        const DATA = window.DATA || null;
        return {
          hero_gap: txt('.hstats .hstat:nth-child(1) .v'),
          hero_rep: txt('#hero-rep'),
          hero_rep_label: q('#hero-rep') ? q('#hero-rep').nextElementSibling.textContent.trim() : null,
          hero_billed: txt('#hero-billed'),
          rep_rows_from_payload: DATA ? DATA.nw.rep_rows_cy : null,
          rep_cy_from_payload: DATA ? DATA.nw.rep_cy : null,
          rep_note_text: (document.body.innerText.match(/2,247,88[0-9]|2\\.25M|1,934/g)||[]),
          league_rows: n('#league-tbody tr'),
          chart_bars: {c1:n('#c1-rows .brow'), c2:n('#c2-rows .brow'), c3:n('#c3-rows .brow'),
                       c4:n('#c4-rows .brow'), c5:n('#c5-rows .brow'), c6:n('#c6-rows .brow')},
          noprice_table_rows: n('section table tbody tr'),
          noprice_first: txt('section table tbody tr:nth-child(1)'),
          console_pageerrors: 0,
        };}""")
    browser.close()

print("=== rendered DOM ===")
import sys
for k, v in res.items():
    print(f"  {k}: {v!r}".encode("ascii", "replace").decode("ascii"))
print("  page_errors:", (errs if errs else ["clean"]))
