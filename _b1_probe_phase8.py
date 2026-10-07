# -*- coding: utf-8 -*-
"""B1 phase 8 — deep probe of the last allowed hosts: isuzu.pt, acp.pt, pecasauto.com.pt,
autopecas.online. Home page shape, raw-HTML prices, IVA, and the shop's own search URL.
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
    "https://www.isuzu.pt/",
    "https://www.acp.pt/",
    "https://www.pecasauto.com.pt/",
    "https://www.autopecas.online/",
]


def main() -> int:
    f = PoliteFetcher()
    for url in URLS:
        host = url.split("//", 1)[-1].strip("/").replace(":", "_")
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
        print(f"  price tokens: {len(prices)}{prices[:6]}")
        print(f"  IVA: {bool(re.search(r'(?i)\biva\b', html))}   'isuzu': {html.lower().count('isuzu')}")
        for m in re.finditer(r"<form\b[^>]*(?:search|busca|pesquisa|procurar)[^>]*>.*?</form>",
                             html, re.S | re.I):
            blk = re.sub(r"\s+", " ", m.group(0))
            act = re.search(r'action="([^"]*)"', blk, re.I)
            names = re.findall(r'name="([^"]+)"', blk, re.I)
            print(f"  search form action={act.group(1) if act else '-'} names={names[:8]}")
        forms = re.findall(r'<form[^>]*action="([^"]+)"', html, re.I)
        print(f"  all forms: {forms[:6]}")
        inputs = sorted(set(re.findall(r'<input[^>]*name="([^"]+)"', html, re.I)))
        print(f"  inputs: {inputs[:14]}")
        links = sorted(set(re.findall(r'href="([^"]*(?:pesquisa|busca|search|pecas|produto)[^"]*)"',
                                      html, re.I)))[:10]
        print(f"  links: {links}")
    print(f"\nfetch stats: {f.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
