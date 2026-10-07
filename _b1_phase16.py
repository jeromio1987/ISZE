# -*- coding: utf-8 -*-
"""B1 phase 16 — final decisive test on Winparts.es (a TecDoc catalogue that ships in EUR):
  * product pages are robots-allowed (only /search?q= and /parts/ are not);
  * is the price server-rendered on a product page?
  * does it carry Isuzu at all?
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
LOC = re.compile(r"<loc>\s*(?:<!\[CDATA\[)?\s*(.*?)\s*(?:\]\]>)?\s*</loc>", re.S | re.I)
PRICE = re.compile(r"\d{1,4}[.,]\d{2}\s?€|€\s?\d{1,4}[.,]\d{2}")

SITEMAP = "https://www.winparts.es/sitemap/sitemapindex.xml"


def squash(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def main() -> int:
    f = PoliteFetcher()
    print("== sitemap index")
    h = f.get(SITEMAP)
    if not h:
        print("  err")
        return 1
    locs = LOC.findall(h)
    print(f"  {len(h):,}B locs={len(locs)}")
    kids = [u for u in locs if re.search(r"product|piezas|part", u, re.I)] or locs[:4]
    for u in kids[:6]:
        print("   ", u)

    # pick a product URL from the first product sitemap
    prod = None
    for u in kids[:4]:
        txt = f.get(u)
        if not txt:
            continue
        pl = [x for x in LOC.findall(txt) if re.search(r"/[a-z0-9-]+/c\d+\.html|/p/|/producto",
                                                      x, re.I)]
        print(f"  {u}: {len(LOC.findall(txt))} locs, {len(pl)} product-shaped")
        if pl and prod is None:
            prod = pl[0]
        if prod:
            break
    print(f"\n== product page test: {prod}")
    if prod:
        txt = f.get(prod)
        if txt:
            (PAGES / "winparts_es__product_test.html").write_text(txt, encoding="utf-8",
                                                                 errors="replace")
            pr = PRICE.findall(txt)
            print(f"  {len(txt):,}B  server-side prices={len(pr)}{pr[:6]}")
            print(f"  isuzu={txt.lower().count('isuzu')}  vat_words="
                  f"{bool(re.search(r'(?i)iva|21%', txt))}")

    # does Winparts.es know Isuzu as a make?
    print("\n== make search page")
    for u in ["https://www.winparts.es/marca/isuzu",
              "https://www.winparts.es/piezas-de-auto/isuzu"]:
        try:
            txt = f.get(u)
        except ConsentRefused as e:
            print(f"  REFUSED {u} ({e})")
            continue
        print(f"  {u} -> {len(txt) if txt else 0:,}B  isuzu={txt.lower().count('isuzu') if txt else 0}")
    print(f"\nfetch stats: {f.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
