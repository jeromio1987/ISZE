"""Headless screenshot QA for the 2026-09-19 fixed suite folder."""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

SUITE = Path(__file__).resolve().parent
QA = SUITE / "_qa"
QA.mkdir(exist_ok=True)

PAGES = [
    ("01_lost_sales", "ISZE_Lost_Sales_Model.html", ["#c_verdict", "canvas", ".basis-strip, .basis, [class*=basis]"]),
    ("02_family", "ISZE_PMS_Family_Evolution_v2.html", ["canvas", "select", ".basis-strip, .basis, [class*=basis]"]),
    ("03_tonnage", "ISZE_PMS_Tonnage_Evolution.html", ["canvas", "select", ".basis-strip, .basis, [class*=basis]"]),
    ("04_replenishment", "ISZE_DB_DLR_Replenishment_CY2025.html", ["canvas, .bar-row, .fb-bar, table", "select", ".basis-strip, .basis, [class*=basis]"]),
    ("05_leakage", "ISZE_DB_Leakage_Review_CY2025.html", [".basis-strip, .basis, [class*=basis]", "h1, h2"]),
    ("06_command_center", "ISZE_Aftermarket_BI_Command_Center.html", [".suite-card, .suite-grid a", "#retirement-notice, .retired-banner"]),
]


def file_url(p: Path) -> str:
    return p.resolve().as_uri()


def main() -> int:
    report = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        )
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        for stem, name, selectors in PAGES:
            html = SUITE / name
            url = file_url(html)
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(1800)

            hero = QA / f"{stem}_hero.png"
            page.screenshot(path=str(hero), full_page=False)

            # Scroll to first chart / key section and capture
            scrolled = False
            for sel in selectors:
                loc = page.locator(sel).first
                try:
                    if loc.count() > 0:
                        loc.scroll_into_view_if_needed(timeout=3000)
                        page.wait_for_timeout(600)
                        scrolled = True
                        break
                except Exception:
                    continue
            mid = QA / f"{stem}_section.png"
            page.screenshot(path=str(mid), full_page=False)

            # DOM probes
            probes = page.evaluate(
                """() => {
                const text = (document.body && document.body.innerText) || '';
                const canvases = [...document.querySelectorAll('canvas')];
                const painted = canvases.filter(c => {
                  try {
                    const ctx = c.getContext('2d');
                    if (!ctx) return false;
                    const d = ctx.getImageData(0, 0, Math.min(c.width||1, 40), Math.min(c.height||1, 40)).data;
                    for (let i = 3; i < d.length; i += 4) if (d[i] > 0) return true;
                    return false;
                  } catch (e) { return c.width > 0 && c.height > 0; }
                }).length;
                const bars = document.querySelectorAll('.bar-row, .fb-bar, .fallback-bars .fb-row').length;
                const selects = document.querySelectorAll('select').length;
                const suiteLinks = document.querySelectorAll('.suite-card, a.suite-link').length;
                const h1 = (document.querySelector('h1') || {}).innerText || '';
                const blankish = text.replace(/\\s+/g,'').length < 80;
                const cdnFail = [...document.querySelectorAll('script[src]')].some(s =>
                  /cdn\\.jsdelivr|cdnjs\\.cloudflare|unpkg\\.com/i.test(s.src));
                return {
                  title: document.title,
                  h1,
                  textLen: text.length,
                  canvasCount: canvases.length,
                  paintedCanvases: painted,
                  barMarkers: bars,
                  selects,
                  suiteLinks,
                  blankish,
                  cdnScriptTags: cdnFail,
                  hasBasis: /basis|Observed|OBSERVED|trucks in service|modelled/i.test(text),
                  retired: /retired/i.test(text),
                };
              }"""
            )
            entry = {
                "file": name,
                "hero": str(hero),
                "section": str(mid),
                "scrolled": scrolled,
                **probes,
            }
            report.append(entry)
            print(json.dumps(entry, ensure_ascii=True))
        browser.close()

    out = QA / "probe_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("WROTE", out)
    # Hard fails
    fails = []
    for e in report:
        if e["blankish"]:
            fails.append(f"{e['file']}: blank body")
        if e["file"] == "ISZE_Lost_Sales_Model.html":
            if e["paintedCanvases"] < 1 and e["barMarkers"] < 1:
                fails.append(f"{e['file']}: no painted chart")
            if "losing sales" in e["h1"].lower():
                fails.append(f"{e['file']}: old h1")
        if e["file"] == "ISZE_Aftermarket_BI_Command_Center.html":
            if e["suiteLinks"] < 4 or not e["retired"]:
                fails.append(f"{e['file']}: suite index incomplete")
        if e["file"] != "ISZE_Aftermarket_BI_Command_Center.html" and not e.get("hasBasis"):
            # soft for leakage which has basis strip
            if "Leakage" in e["file"] or "PMS" in e["file"] or "Lost" in e["file"] or "Replenishment" in e["file"]:
                if not e.get("hasBasis"):
                    fails.append(f"{e['file']}: missing basis text")
        if e.get("cdnScriptTags"):
            fails.append(f"{e['file']}: CDN script tags")
    print("PROBE_FAILS", fails or "none")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
