"""Close-up screenshot of the tender block on the aim-leakage Evidence page."""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_tender_retire_20260924")


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", args=["--no-sandbox", "--disable-gpu"])
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto("http://localhost:3100/aim-leakage/", wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(9000)
        # scroll the tender heading into view and shoot the viewport
        found = page.evaluate(
            """() => {
                for (const h of document.querySelectorAll('h2,h3')) {
                    if (/Tender \\/ R&M channel/.test(h.innerText)) {
                        h.scrollIntoView({block: 'start'});
                        window.scrollBy(0, -260);
                        return h.innerText;
                    }
                }
                return null;
            }"""
        )
        print("heading found:", found)
        page.wait_for_timeout(1500)
        page.screenshot(path=str(OUT / "aim_leakage_tender_block.png"))
        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
