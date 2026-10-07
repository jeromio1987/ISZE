# -*- coding: utf-8 -*-
"""B1 phase 3b — probe the newly-allowed hosts: does the RAW html carry a price, does it
show IVA/EUR, and what is the shop's own search URL?
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

TARGETS = [
    "https://www.casadaspecas.pt/",
    "https://www.rodasa.com/",
    "https://www.rasch.pt/",
    "https://www.agauto.pt/",
    "https://www.lojadaspecas.pt/",
    "https://www.parts.pt/",
    "https://www.motointegrator.pt/",
    "https://www.winparts.es/",
    "https://www.rodauto.pt/",
    "https://www.silvauto.pt/",
    "https://www.pneubeato.com/",
    "https://www.midas.pt/",
]

PRICE_RE = re.compile(r"(?:EUR|€)\s?\d{1,4}[.,]\d{2}|\d{1,4}[.,]\d{2}\s?(?:EUR|€)")
VAT_RE = re.compile(r"(?i)\b(iva|vat|incl\.?\s*iva|sem\s+iva|com\s+iva|preço)\b")


def main() -> int:
    f = PoliteFetcher()
    for url in TARGETS:
        host = url.split("//", 1)[-1].strip("/").replace(":", "_")
        print(f"\n{'='*80}\n{url}")
        try:
            html = f.get(url)
        except ConsentRefused as e:
            print(f"  CONSENT REFUSED: {e}")
            continue
        if not html:
            print("  no body")
            continue
        (PAGES / f"{host}__home.html").write_text(html, encoding="utf-8", errors="replace")
        title = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
        print(f"  {len(html):,}B   title: "
              f"{re.sub(chr(10),' ',title.group(1)).strip()[:90] if title else '-'}")
        prices = PRICE_RE.findall(html)
        print(f"  price tokens: {len(prices)} {prices[:5]}   IVA: {bool(VAT_RE.search(html))}   "
              f"ld+json: {len(re.findall(r'application/ld.json', html))}")
        forms = re.findall(r"<form[^>]*action=[\"']([^\"']+)[\"']", html, re.I)
        print(f"  forms: {forms[:5]}")
        for m in re.finditer(r"<form\b[^>]*>.*?</form>", html, re.S | re.I):
            blk = m.group(0)
            names = re.findall(r"<input[^>]*name=[\"']([^\"']+)[\"']", blk, re.I)
            if any(k in " ".join(names).lower() for k in ("search", "busca", "pesquisa", "q", "query", "sku", "part")):
                print(f"    search form names: {names[:8]} action="
                      f"{re.search(r'action=[\"\']([^\"\']*)', blk, re.I).group(1) if 'action=' in blk.lower() else '-'}")
        links = re.findall(r"href=[\"']([^\"']*(?:search|busca|pesquisa|resultados|produto)[^\"']*)[\"']", html, re.I)
        print(f"  search-ish links: {sorted(set(links))[:6]}")
    print(f"\nfetch stats: {f.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
