# -*- coding: utf-8 -*-
"""B1 phase 6 — for the shops whose robots allows a search and whose sitemap is named,
walk the sitemap (through PoliteFetcher) and count product URLs carrying an Isuzu OE
number from our seed list. This is the cheapest way to find a host that stocks our parts.
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
SEEDS = [ln.strip() for ln in (B1 / "seed_oe_pns.csv").read_text(encoding="utf-8").splitlines()
         if ln.strip()]
SEEDS_ALSO_DASHED = set()
for pn in SEEDS:                                        # 8982447940 -> 8-98244-794-0 style
    if len(pn) == 10:
        SEEDS_ALSO_DASHED.add(f"{pn[:1]}-{pn[1:6]}-{pn[6:9]}-{pn[9:]}")
LOC = re.compile(r"<loc>\s*(?:<!\[CDATA\[)?\s*(.*?)\s*(?:\]\]>)?\s*</loc>", re.S | re.I)
SITEMAP_ROOT = re.compile(r"^https?://[^/]+/$")

HOSTS = [
    ("https://www.parts.pt", ["/sitemap.xml"]),
    ("https://www.areal.pt", ["/sitemap.xml"]),
    ("https://www.agauto.pt", ["/sitemap.xml"]),
    ("https://www.epecas.pt", ["/sitemap_index.xml"]),
    ("https://www.pneubeato.com", ["/sitemap.xml"]),
    ("https://www.rodasa.com", ["/sitemap.xml", "/sitemap_index.xml", "/wp-sitemap.xml"]),
    ("https://www.nortecar.pt", ["/sitemap.xml"]),
    ("https://www.pneubeato.com", ["/sitemap.xml"]),
]


def get(f, url):
    try:
        return f.get(url)
    except ConsentRefused as e:
        print(f"    REFUSED {url} ({e})")
        return None


def main() -> int:
    f = PoliteFetcher()
    seen = set()
    for base, paths in HOSTS:
        if base in seen:
            continue
        seen.add(base)
        print(f"\n=== {base}")
        queue = [base + p for p in paths]
        walked = 0
        while queue and walked < 6:
            sm = queue.pop(0)
            html = get(f, sm)
            if html is None:
                continue
            walked += 1
            kind = "index" if "<sitemapindex" in html[:4000].lower() else "urlset"
            locs = LOC.findall(html)
            print(f"  {sm}  {len(html):,}B  {kind}  locs={len(locs)}")
            if kind == "index":
                queue.extend(locs[:6])
                continue
            hits = [u for u in locs if any(pn in u for pn in SEEDS)
                    or any(d in u for d in SEEDS_ALSO_DASHED)]
            isuzu = [u for u in locs if "isuzu" in u.lower()]
            print(f"    OE-number URLs: {len(hits)}  'isuzu' URLs: {len(isuzu)}")
            for u in (hits + isuzu)[:6]:
                print(f"      {u[:150]}")
    print(f"\nfetch stats: {f.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
