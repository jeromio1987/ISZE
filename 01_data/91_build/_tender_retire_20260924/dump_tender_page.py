"""Dump the rendered Evidence tender page's full visible text."""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:3100/tender/"
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_tender_retire_20260924")


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", args=["--no-sandbox", "--disable-gpu"])
        page = browser.new_page(viewport={"width": 1600, "height": 2400})
        page.goto(URL, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(8000)
        html = page.content()
        text = page.evaluate("() => document.body.innerText")
        (OUT / "evidence_tender_dom.html").write_text(html, encoding="utf-8", newline="\n")
        (OUT / "evidence_tender_text.txt").write_text(text, encoding="utf-8", newline="\n")
        # what the page fetched
        print("fetched resources containing 'tender':")
        for u in page.evaluate(
            "() => performance.getEntriesByType('resource').map(r => r.name)"
            ".filter(n => /tender/i.test(n))"
        ):
            print("   ", u)
        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
