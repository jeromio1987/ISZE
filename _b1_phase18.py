# -*- coding: utf-8 -*-
"""B1 phase 18 — last two allowed hosts: pecasoriginais.pt and pecasauto.com.
Home shape, server-side prices, IVA, Isuzu presence, and the shop's own search URL.
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
    "https://www.pecasoriginais.pt/",
    "https://www.pecasauto.com/",
]


def main() -> int:
    f = PoliteFetcher()
    for url in TESTS:
        tag = url.split("//", 1)[-1].strip("/").replace(".", "_")
        print(f"\n{'='*80}\n{url}")
        try:
            h = f.get(url)
        except ConsentRefused as e:
            print(f"  REFUSED {e}")
            continue
        if not h:
            print("  err")
            continue
        (PAGES / f"{tag}__home.html").write_text(h, encoding="utf-8", errors="replace")
        title = re.search(r"<title[^>]*>(.*?)</title>", h, re.S | re.I)
        pr = PRICE.findall(h)
        print(f"  {len(h):,}B  title={re.sub(chr(10),' ',title.group(1)).strip()[:80] if title else '-'}")
        print(f"  server-side prices={len(pr)}{pr[:6]}  iva={bool(re.search(r'(?i)iva', h))}  "
              f"isuzu={h.lower().count('isuzu')}")
        print("  forms:", re.findall(r'<form[^>]*action="([^"]*)"', h, re.I)[:5])
        print("  inputs:", sorted(set(re.findall(r'<input[^>]*name="([^"]+)"', h, re.I)))[:12])
    print(f"\nfetch stats: {f.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
