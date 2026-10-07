# -*- coding: utf-8 -*-
"""B1 phase 22 — b-parts.com search endpoints + sitemap scan for Isuzu and our OEs.
b-parts is a Portuguese (Porto) used-parts marketplace; home page prices are server-rendered.
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
PRICE = re.compile(r"€\s?\d{1,4}[.,]\d{2}|\d{1,4}[.,]\d{2}\s?€")
LOC = re.compile(r"<loc>\s*(?:<!\[CDATA\[)?\s*(.*?)\s*(?:\]\]>)?\s*</loc>", re.S | re.I)
SEEDS = [ln.strip() for ln in (B1 / "seed_oe_pns.csv").read_text(encoding="utf-8").splitlines()
         if ln.strip()]

TESTS = [
    "https://www.b-parts.com/auto-parts/search?query=8982447940",
    "https://www.b-parts.com/auto-parts/search?search=8982447940",
    "https://www.b-parts.com/auto-parts/search?q=8982447940",
    "https://www.b-parts.com/pt/pecas-auto/isuzu",
    "https://www.b-parts.com/isuzu-d-max",
    "https://www.b-parts.com/sitemap.xml",
]


def main() -> int:
    f = PoliteFetcher()
    for url in TESTS:
        try:
            h = f.get(url)
        except ConsentRefused as e:
            print(f"REFUSED {url} ({e})")
            continue
        if not h:
            print(f"err/non-200 {url}")
            continue
        name = re.sub(r"[^a-z0-9]+", "_", url.split("b-parts.com/")[-1].lower())[:44]
        (PAGES / f"bparts__{name}.html").write_text(h, encoding="utf-8", errors="replace")
        pr = PRICE.findall(h)
        locs = LOC.findall(h)
        print(f"{url}\n   {len(h):,}B prices={len(pr)}{pr[:4]} locs={len(locs)} "
              f"isuzu={h.lower().count('isuzu')}")
        if locs:
            isu = [u for u in locs if "isuzu" in u.lower()]
            hits = [u for u in locs if any(p in u for p in SEEDS)]
            print(f"   isuzu locs={len(isu)} seed-OE locs={len(hits)}")
            for u in (isu + hits)[:8]:
                print("     ", u[:150])
    print(f"\nfetch stats: {f.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
