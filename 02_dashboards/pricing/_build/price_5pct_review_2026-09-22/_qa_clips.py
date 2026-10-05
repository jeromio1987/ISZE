"""QA captures for the 2026-09-22 +5% flat simulation page.

Element-scoped screenshots, because page clips fail for anything below the viewport fold and the
tables are all below it. Writes into _qa/ beside the build folder.
"""
from pathlib import Path
import json

from playwright.sync_api import sync_playwright

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
STAMP = "2026-09-22"
HTML = ISZE / "02_dashboards" / "pricing" / f"ISZE_Price_Increase_5pct_Flat_SIMULATION_{STAMP}.html"
OUT = ISZE / "02_dashboards" / "pricing" / "_build" / f"price_5pct_review_{STAMP}" / "_qa"
OUT.mkdir(parents=True, exist_ok=True)

report = {"html": str(HTML), "taken": [], "console_errors": [], "probe": {}}

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", headless=True)
    page = b.new_page(viewport={"width": 1400, "height": 900}, device_scale_factor=2)
    page.on("console", lambda m: report["console_errors"].append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: report["console_errors"].append(str(e)))
    page.goto(HTML.as_uri(), wait_until="load")
    page.wait_for_timeout(3000)

    probe = page.evaluate("""() => {
        const out = {scrollW: document.documentElement.scrollWidth,
                     clientW: document.documentElement.clientWidth,
                     clipped: [], canvases: [], tables: 0, rows: 0};
        document.querySelectorAll('*').forEach(el => {
            if (el.scrollWidth > el.clientWidth + 4 && el.clientWidth > 0) {
                out.clipped.push({tag: el.tagName, cls: String(el.className).slice(0,30),
                                  sw: el.scrollWidth, cw: el.clientWidth,
                                  txt: (el.textContent||'').trim().slice(0,40)});
            }
        });
        document.querySelectorAll('canvas').forEach((c,i) => {
            const r = c.getBoundingClientRect();
            out.canvases.push({i, w: Math.round(r.width), h: Math.round(r.height)});
        });
        out.tables = document.querySelectorAll('table').length;
        out.rows = document.querySelectorAll('tbody tr').length;
        return out;
    }""")
    report["probe"] = probe
    print("horizontal overflow:", probe["scrollW"], "vs", probe["clientW"],
          "->", "OK" if probe["scrollW"] <= probe["clientW"] + 1 else "OVERFLOW")
    print("clipped elements:", len(probe["clipped"]))
    for c in probe["clipped"][:10]:
        print("   ", c)
    print("canvases:", probe["canvases"], "tables:", probe["tables"], "rows:", probe["rows"])

    def shot(sel, name):
        page.locator(sel).screenshot(path=str(OUT / f"{name}.png"))
        report["taken"].append(str(OUT / f"{name}.png"))

    shot("header.top", "el_header")
    shot(".kpis", "el_kpis")
    for i in range(page.locator(".note").count()):
        shot(f".note >> nth={i}", f"el_note{i+1}")
    for i in range(page.locator(".card").count()):
        shot(f".card >> nth={i}", f"el_card{i+1}")
    shot(".split", "el_split")

    # whole-page stills at two widths, for the visual read
    for w, tag in ((1400, "desktop"), (900, "narrow")):
        page.set_viewport_size({"width": w, "height": 1200})
        page.wait_for_timeout(400)
        page.screenshot(path=str(OUT / f"page_{tag}.png"), full_page=True)
        report["taken"].append(str(OUT / f"page_{tag}.png"))

    print("cards:", page.locator(".card").count(), "notes:", page.locator(".note").count())
    print("console errors:", report["console_errors"])
    b.close()

print("QA_CLIPS_DONE", len(report["taken"]), "screenshots")
(OUT / "qa_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
