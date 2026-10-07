# -*- coding: utf-8 -*-
"""B1 phase 23 — b-parts.com PT Isuzu product sitemap -> product pages -> is the price
server-rendered and do the products carry Isuzu OE numbers and usable fields?
"""
from __future__ import annotations

import gzip
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
PRICE = re.compile(r"€\s?\d{1,4}[.,]\d{2}|\d{1,4}[.,]\d{2}\s?€")
LOC = re.compile(r"<loc>\s*(?:<!\[CDATA\[)?\s*(.*?)\s*(?:\]\]>)?\s*</loc>", re.S | re.I)

SM = "https://www.b-parts.com/sitemaps/sitemap-products-isuzu-pt-1.xml.gz"


def main() -> int:
    f = PoliteFetcher()
    h = f.get(SM)
    if not h:
        print(f"  sitemap err/non-200 {SM}")
        return 1
    locs = LOC.findall(h)
    print(f"sitemap {SM}: {len(h):,} chars, locs={len(locs)}")
    for u in locs[:5]:
        print("  ", u)
    # fetch the first few product pages
    for u in locs[:4]:
        try:
            p = f.get(u)
        except ConsentRefused as e:
            print(f"  REFUSED {u} ({e})")
            continue
        if not p:
            print(f"  err {u}")
            continue
        name = re.sub(r"[^a-z0-9]+", "_", u.split("b-parts.com/")[-1].lower())[:60]
        (PAGES / f"bparts__{name}.html").write_text(p, encoding="utf-8", errors="replace")
        pr = PRICE.findall(p)
        print(f"\n{u}\n   {len(p):,}B  prices={len(pr)}{pr[:6]}  "
              f"isuzu={p.lower().count('isuzu')}")
        for key in ("reference", "referencia", "oem", "Réf", '"price"', "condition", "warranty",
                    "IVA", "stock"):
            if key.lower() in p.lower():
                i = p.lower().find(key.lower())
                print(f"   [{key}] {re.sub(chr(92)+'s+', ' ', p[max(0,i-90):i+130])[:210]}")
    print(f"\nfetch stats: {f.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
