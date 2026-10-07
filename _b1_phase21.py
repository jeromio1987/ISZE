# -*- coding: utf-8 -*-
"""B1 phase 21 — b-parts.com (Portuguese used-parts marketplace, robots-allowed):
is a price server-rendered, and does it expose our Isuzu OE numbers?
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
PRICE = re.compile(r"\d{1,4}[.,]\d{2}\s?€|€\s?\d{1,4}[.,]\d{2}")

TESTS = [
    ("home", "https://www.b-parts.com/"),
    ("robots", "https://www.b-parts.com/robots.txt"),
    ("search OE", "https://www.b-parts.com/search?q=8982447940"),
    ("isuzu", "https://www.b-parts.com/isuzu/"),
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
            print(f"{tag}: err/non-200")
            continue
        name = re.sub(r"[^a-z0-9]+", "_", tag.lower())
        (PAGES / f"bparts__{name}.html").write_text(h, encoding="utf-8", errors="replace")
        pr = PRICE.findall(h)
        print(f"{tag:<10} {len(h):>9,}B  prices={len(pr)}{pr[:6]}  "
              f"isuzu={h.lower().count('isuzu')}  json_price={h.count('\"price\"')}")
    print(f"\nfetch stats: {f.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
