# -*- coding: utf-8 -*-
"""B1 phase 5 — probe the winparts.es /search?q= endpoint (matches its own form) for the
seed Isuzu numbers, and report whether the RAW html carries the number and a price.
Buyer-facing candidates besides Portugal-only shops. PoliteFetcher throughout.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent
for c in [HERE, *HERE.parents]:
    if (c / "04_tools" / "autodoc_scraper" / "check_scrape_consent.py").exists():
        ISZE = c
        break
sys.path.insert(0, str(ISZE / "04_tools" / "delegation" / "parsers"))
from fetch_polite import PoliteFetcher, ConsentRefused   # noqa: E402

B1 = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "_u26" / "B1"
PAGES = B1 / "pages"
SEEDS = ["8982447940", "8975546610", "8982705240", "8980791040"]
PRICE_RE = re.compile(r"(?:EUR|€)\s?\d{1,4}[.,]\d{2}|\d{1,4}[.,]\d{2}\s?(?:EUR|€)")


def main() -> int:
    f = PoliteFetcher()
    for pn in SEEDS:
        url = f"https://www.winparts.es/search?q={pn}"
        print(f"\n=== {url}")
        try:
            html = f.get(url)
        except ConsentRefused as e:
            print(f"  REFUSED {e}")
            continue
        if not html:
            print("  err/non-200")
            continue
        (PAGES / f"winparts_es__search_{pn}.html").write_text(html, encoding="utf-8", errors="replace")
        prices = PRICE_RE.findall(html)
        print(f"  {len(html):,}B  pn_on_page={pn in html}  price_tokens={len(prices)}{prices[:5]}")
        title = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
        print(f"  title: {re.sub(chr(10),' ',title.group(1)).strip()[:110] if title else '-'}")
        # does the number appear in a product href/slug?
        hits = re.findall(r'href="([^"]*' + re.escape(pn) + r'[^"]*)"', html)
        print(f"  hrefs containing the number: {hits[:5]}")
        # any product card / price element?
        print(f"  'data-price' occurrences: {html.count('data-price')}  "
              f"'price' class occurrences: {html.count('class=\"price')}")
    print(f"\nfetch stats: {f.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
