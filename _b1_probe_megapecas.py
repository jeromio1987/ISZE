# -*- coding: utf-8 -*-
"""B1 phase 11 — megapecas.pt: robots, its own search/ProductList endpoint, and a probe of
seed Isuzu numbers. Also autocenter.pt search and a product page (WooCommerce).
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
SEEDS = ["8982447940", "8975546610", "8982705240", "8980791040"]


def show(label, html, pn=None):
    prices = PRICE_RE.findall(html)
    print(f"  {label}\n    {len(html):,}B  pn_on_page={pn in html if pn else 'n/a'}  "
          f"price_tokens={len(prices)}{prices[:5]}  IVA={bool(re.search(r'(?i)iva', html))}  "
          f"isuzu={html.lower().count('isuzu')}")


def main() -> int:
    f = PoliteFetcher()
    # robots
    for host in ["https://megapecas.pt", "https://www.megapecas.pt", "https://autocenter.pt"]:
        r = f.get(host + "/robots.txt")
        print(f"\n=== robots {host} ===\n{'-'*60}")
        if r:
            for ln in r.splitlines():
                if ln.strip() and not ln.strip().startswith("#"):
                    print("  " + ln.strip()[:140])

    print("\n=== megapecas search attempts ===")
    tries = [
        "https://megapecas.pt/pt/ProductListForm?q={pn}",
        "https://megapecas.pt/pt/produtos?q={pn}",
        "https://megapecas.pt/pt/pesquisa?q={pn}",
        "https://megapecas.pt/pt/ProductListForm?search={pn}",
        "https://megapecas.pt/pt/ProductListForm?referencia={pn}",
    ]
    for tpl in tries:
        for pn in SEEDS[:2]:
            url = tpl.format(pn=pn)
            try:
                html = f.get(url)
            except ConsentRefused as e:
                print(f"  REFUSED {url} :: {e}")
                break
            if not html:
                print(f"  err {url}")
                continue
            show(url, html, pn)
            if pn in html:
                (PAGES / f"megapecas__search_{pn}.html").write_text(html, encoding="utf-8",
                                                                    errors="replace")
        print()
    print(f"fetch stats: {f.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
