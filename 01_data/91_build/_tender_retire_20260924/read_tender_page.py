"""Read the rendered Evidence tender page and report what the tiles actually show.

The page is client-rendered, so a screenshot alone does not say whether a 0 is
real or a not-yet-hydrated tile. This drives a real browser and reads the text.
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:3100/tender/"
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_tender_retire_20260924")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            args=["--no-sandbox", "--disable-gpu"],
        )
        page = browser.new_page(viewport={"width": 1600, "height": 2400})
        page.goto(URL, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(8000)

        print("TITLE :", page.title())
        print("URL   :", page.url)
        print()

        # every BigValue tile, in document order: title + the number next to it
        tiles = page.evaluate(
            """() => {
                const out = [];
                const seen = new Set();
                for (const el of document.querySelectorAll('*')) {
                    const t = (el.innerText || '').replace(/\\s+/g, ' ').trim();
                    if (/^(\\S+ )?(Opportunities|Actionable|Pipeline value)\\b/.test(t)
                        && t.length < 90 && !seen.has(t)) {
                        seen.add(t);
                        out.push(t);
                    }
                }
                return out;
            }"""
        )
        print("TILES :")
        for t in tiles:
            print("   ", t)

        body = page.evaluate("() => document.body.innerText")
        print()
        print("BODY KEYS:")
        for pat in ("619", "281", "279", "31", "128", "491", "16", "22 Sep 2026",
                    "superseded", "Superseded", "no longer"):
            print(f"    {pat!r:16} count={body.count(pat)}")

        rows = page.evaluate(
            """() => [...document.querySelectorAll('table tbody tr')].slice(0,3)
                     .map(r => [...r.querySelectorAll('td')].map(c => c.innerText.trim()).join(' | '))"""
        )
        print()
        print("TABLE ROWS:", len(rows))
        for r in rows:
            print("   ", r[:180])

        errors = page.evaluate(
            """() => [...document.querySelectorAll('[class*=error],[class*=Error]')]
                     .map(e => e.innerText.trim().slice(0,200)). filter(Boolean).slice(0,5)"""
        )
        print()
        print("VISIBLE ERROR ELEMENTS:", errors)

        page.screenshot(path=str(OUT / "evidence_tender_playwright.png"), full_page=True)
        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
