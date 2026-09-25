"""Screenshot the two Evidence pages that read the tender source, and read their text."""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_tender_retire_20260924")
PAGES = {"tender": "http://localhost:3100/tender/",
         "aim-leakage": "http://localhost:3100/aim-leakage/"}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", args=["--no-sandbox", "--disable-gpu"])
        for name, url in PAGES.items():
            page = browser.new_page(viewport={"width": 1600, "height": 1200})
            page.goto(url, wait_until="networkidle", timeout=120000)
            page.wait_for_timeout(9000)
            text = page.evaluate("() => document.body.innerText")
            (OUT / f"evidence_{name}_text.txt").write_text(text, encoding="utf-8", newline="\n")
            page.screenshot(path=str(OUT / f"evidence_{name}_full.png"), full_page=True)
            print(f"--- {name}: {url}")
            print(f"    title: {page.title()}   text {len(text)} chars")
            for pat in ("619", "281", "279", "400", "352", "208"):
                print(f"    {pat!r:6} count={text.count(pat)}")
            # error / empty markers
            marks = [m for m in ("Error", "error", "failed", "Failed", "No data",
                                 "undefined", "NaN") if m in text]
            print(f"    suspicious markers: {marks}")
            browser.contexts[0].pages[-1].close()
        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
