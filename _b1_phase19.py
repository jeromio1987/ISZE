# -*- coding: utf-8 -*-
"""B1 phase 19 — autoparts24.eu (EU TecDoc shop, ships PT, EUR): is a product price
server-rendered, and does the shop know our Isuzu numbers?
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
PRICE = re.compile(r"\d{1,4}[.,]\d{2}\s?€|€\s?\d{1,4}[.,]\d{2}|EUR\s?\d")

TESTS = [
    ("home", "https://www.autoparts24.eu/"),
    ("search OE brake", "https://www.autoparts24.eu/search?q=8982447940"),
    ("search OE oil", "https://www.autoparts24.eu/search?q=8982705240"),
    ("search brand", "https://www.autoparts24.eu/search?q=ADBP420136"),
]


def main() -> int:
    f = PoliteFetcher()
    for tag, url in TESTS:
        try:
            h = f.get(url)
        except ConsentRefused as e:
            print(f"{tag}: REFUSED {e}")
            continue
        if not h:
            print(f"{tag}: err")
            continue
        name = re.sub(r"[^a-z0-9]+", "_", tag.lower())
        (PAGES / f"ap24__{name}.html").write_text(h, encoding="utf-8", errors="replace")
        pr = PRICE.findall(h)
        results_marker = len(re.findall(r"class=\"[^\"]*(?:product|article|item)[^\"]*\"", h, re.I))
        print(f"{tag:<18} {len(h):>8,}B  prices={len(pr)}{pr[:6]}  "
              f"product-ish_classes={results_marker}")
        if "8982447940" in h or "8982705240" in h or "ADBP420136" in h:
            i = max(h.find("8982447940"), h.find("8982705240"), h.find("ADBP420136"))
            print("     ctx:", re.sub(r"\s+", " ", h[max(0, i - 180): i + 180])[:340])
    print(f"\nfetch stats: {f.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
