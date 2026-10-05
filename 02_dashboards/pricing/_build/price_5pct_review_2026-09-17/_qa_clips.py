"""QA captures for the +5% review page, element-scoped so each region is legible.

Uses element screenshots rather than page clips: page clips fail for anything below the
viewport fold, which is where the tables live.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HTML = ISZE / "02_dashboards" / "pricing" / "ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html"
OUT = ISZE / "02_dashboards" / "pricing" / "_build" / "price_5pct_review_2026-09-17" / "_qa"
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", headless=True)
    page = b.new_page(viewport={"width": 1400, "height": 900}, device_scale_factor=2)
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(HTML.as_uri(), wait_until="load")
    page.wait_for_timeout(2500)

    # ---- layout probe first
    probe = page.evaluate("""() => {
        const out = {scrollW: document.documentElement.scrollWidth,
                     clientW: document.documentElement.clientWidth,
                     clipped: [], canvases: []};
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
        return out;
    }""")
    print("horizontal overflow:", probe["scrollW"], "vs", probe["clientW"],
          "->", "OK" if probe["scrollW"] <= probe["clientW"] + 1 else "OVERFLOW")
    print("clipped elements:", len(probe["clipped"]))
    for c in probe["clipped"][:10]:
        print("   ", c)
    print("canvases:", probe["canvases"])

    # ---- element captures
    page.locator("header.top").screenshot(path=str(OUT / "el_header.png"))
    page.locator(".kpis").screenshot(path=str(OUT / "el_kpis.png"))
    for i in range(page.locator(".note").count()):
        page.locator(".note").nth(i).screenshot(path=str(OUT / f"el_note{i+1}.png"))
    for i in range(page.locator(".card").count()):
        page.locator(".card").nth(i).screenshot(path=str(OUT / f"el_card{i+1}.png"))

    print("cards:", page.locator(".card").count(), "notes:", page.locator(".note").count())
    print("console errors:", errors)
    b.close()
print("QA_CLIPS_DONE")
