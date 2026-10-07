# -*- coding: utf-8 -*-
"""B1 phase 15 — decisive coverage test on megapecas.pt (the one PT shop with
server-rendered prices and an Isuzu make option):

  * does a generic search ("filtro") return cards while an Isuzu OE returns none?
  * does the ISUZU make filter return anything?

If the OE search returns nothing while a generic term returns cards, megapecas has no
Isuzu coverage and is not usable for this harvest.
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
CARD_RE = re.compile(r'class="[^"]*product[^"]*card|class="card-product|<h2 class="price', re.I)
PRICE_RE = re.compile(r"\d{1,4}(?:[.,]\d{2})\s?€")

TESTS = [
    ("generic filtro", "https://megapecas.pt/pt/produtos?Search=filtro"),
    ("generic travão", "https://megapecas.pt/pt/produtos?Search=travao"),
    ("OE 8982447940", "https://megapecas.pt/pt/produtos?Search=8982447940"),
    ("OE 8982705240", "https://megapecas.pt/pt/produtos?Search=8982705240"),
    ("competitor F026407349", "https://megapecas.pt/pt/produtos?Search=F026407349"),
    ("make ISUZU page", "https://megapecas.pt/pt/marcas/isuzu"),
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
        (PAGES / f"megapecas__{name}.html").write_text(h, encoding="utf-8", errors="replace")
        prices = PRICE_RE.findall(h)
        cards = CARD_RE.findall(h)
        iw = h.find('"numberOfItems"')
        n_items = re.search(r'"numberOfItems":(\d+)', h)
        print(f"{tag:<24} {len(h):>8,}B  prices={len(prices):>3}  card_markers={len(cards):>3}  "
              f"numberOfItems={n_items.group(1) if n_items else '-'}")
    print(f"\nfetch stats: {f.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
