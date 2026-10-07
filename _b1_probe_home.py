# -*- coding: utf-8 -*-
"""B1 phase 3 — polite live probe of the hosts whose robots allowed us.

For each candidate we fetch (through fetch_polite.PoliteFetcher: consent gate, >= 2.2 s
per host, disk cache) a small set of pages and report, from the bytes:

  * HTTP reachability and page shape (server-rendered HTML vs a JS shell);
  * whether a price is present in the RAW HTML (i.e. no JavaScript needed);
  * whether the EUR / VAT wording is on the page;
  * whether the Isuzu number or a competitor number surfaces.

Nothing is parsed into rows here. This is discovery: decide which host is usable.
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

B1 = HERE if HERE.name == "B1" else (
    ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "_u26" / "B1")
PAGES = B1 / "pages"
PAGES.mkdir(parents=True, exist_ok=True)

# First shot: home pages, to discover each shop's own search URL from its own HTML.
TARGETS = [
    "https://www.motocar.pt/",
    "https://www.autosil.pt/",
    "https://www.soauto.pt/",
    "https://www.ersatzteile-24.com/",
]

PRICE_RE = re.compile(r"(?:EUR|€)\s?\d{1,4}[.,]\d{2}|\d{1,4}[.,]\d{2}\s?(?:EUR|€)")
VAT_RE = re.compile(r"(?i)\b(iva|vat|incl\.?\s*iva|sem iva|com iva)\b")
JSONLD_RE = re.compile(r'application/ld\+json')


def shape(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return f"{len(html):,}B html / {len(text):,}B visible text"


def main() -> int:
    f = PoliteFetcher()
    for url in TARGETS:
        host = re.sub(r"[^a-zA-Z0-9._-]", "_", url.split("//", 1)[-1])
        print(f"\n{'='*80}\n{url}")
        try:
            html = f.get(url)
        except ConsentRefused as e:
            print(f"  CONSENT REFUSED: {e}")
            continue
        if not html:
            print("  no body (non-200, error, or cache miss)")
            continue
        (PAGES / f"{host}__home.html").write_text(html, encoding="utf-8", errors="replace")
        print(f"  {shape(html)}")
        title = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
        print(f"  title: {re.sub(chr(10), ' ', title.group(1)).strip()[:110] if title else '-'}")
        prices = PRICE_RE.findall(html)
        print(f"  price-like tokens in RAW html: {len(prices)}  e.g. {prices[:6]}")
        print(f"  VAT/IVA wording: {bool(VAT_RE.search(html))}   JSON-LD blocks: {len(JSONLD_RE.findall(html))}")
        # Any forms pointing at a search endpoint?
        forms = re.findall(r"<form[^>]*action=[\"']([^\"']+)[\"']", html, re.I)
        print(f"  forms: {forms[:6]}")
        inputs = re.findall(r"<input[^>]*name=[\"']([^\"']+)[\"']", html, re.I)
        print(f"  input names: {sorted(set(inputs))[:14]}")
        links = re.findall(r"href=[\"']([^\"']*(?:search|busca|pesquisa|produto|result)[^\"']*)[\"']", html, re.I)
        print(f"  search-ish links: {sorted(set(links))[:8]}")
    print(f"\nfetch stats: {f.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
