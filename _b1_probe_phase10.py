# -*- coding: utf-8 -*-
"""B1 phase 10 — deep probe of the last four allowed hosts + buycarparts.pt/car-parts.pt
style Magento shops: home shape, raw prices, and the shop's own search URL/form.
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
PRICE_RE = re.compile(r"(?:EUR|€)\s?\d{1,4}[.,]\d{2}|\d{1,4}[.,]\d{2}\s?€")

URLS = [
    "https://www.autopecas.com.pt/",
    "https://www.megapecas.pt/",
    "https://www.autolux.pt/",
    "https://www.autocenter.pt/",
]


def main() -> int:
    f = PoliteFetcher()
    for url in URLS:
        host = url.split("//", 1)[-1].strip("/")
        print(f"\n{'='*84}\n{url}")
        try:
            html = f.get(url)
        except ConsentRefused as e:
            print(f"  REFUSED {e}")
            continue
        if not html:
            print("  err/non-200")
            continue
        (PAGES / f"{host}__home.html").write_text(html, encoding="utf-8", errors="replace")
        title = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
        print(f"  {len(html):,}B  title: {re.sub(chr(10),' ',title.group(1)).strip()[:95] if title else '-'}")
        prices = PRICE_RE.findall(html)
        print(f"  price tokens: {len(prices)}{prices[:6]}  IVA={bool(re.search(r'(?i)iva', html))}  "
              f"isuzu={html.lower().count('isuzu')}")
        for m in re.finditer(r"<form\b.*?</form>", html, re.S | re.I):
            blk = re.sub(r"\s+", " ", m.group(0))
            act = re.search(r'action="([^"]*)"', blk, re.I)
            names = re.findall(r'name="([^"]+)"', blk, re.I)
            print(f"  form action={act.group(1) if act else '-'} names={names[:8]}")
        print(f"  search-ish links: "
              f"{sorted(set(re.findall(r'href=.([^\"].*(?:pesquisa|busca|search|produtos)[^\"].).',
                                     html, re.I)))[:8]}")
    print(f"\nfetch stats: {f.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
