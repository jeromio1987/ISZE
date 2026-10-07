# -*- coding: utf-8 -*-
"""B1 phase 12 — sitemap walk of megapecas.pt and autocenter.pt looking for our seed OE
numbers or an Isuzu line. Prices on megapecas are server-rendered, so a product URL that
carries one of our numbers is directly usable.
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
SEEDS = [ln.strip() for ln in (B1 / "seed_oe_pns.csv").read_text(encoding="utf-8").splitlines()
         if ln.strip()]
DASHED = {f"{p[:1]}-{p[1:6]}-{p[6:9]}-{p[9:]}" for p in SEEDS if len(p) == 10}
LOC = re.compile(r"<loc>\s*(?:<!\[CDATA\[)?\s*(.*?)\s*(?:\]\]>)?\s*</loc>", re.S | re.I)

ROOTS = [
    ("https://megapecas.pt/sitemap.xml", "megapecas"),
    ("https://autocenter.pt/wp-sitemap.xml", "autocenter"),
]


def main() -> int:
    f = PoliteFetcher()
    for root, tag in ROOTS:
        print(f"\n{'='*84}\n### {tag}  {root}")
        queue = [root]
        walked, all_locs = 0, []
        if root.endswith("sitemap.xml") and tag == "megapecas":
            txt = f.get(root)
            if txt and "<loc>" not in txt[:2000] and "<sitemapindex" not in txt[:2000]:
                # maybe an index without the string; just parse
                pass
        while queue and walked < 25:
            sm = queue.pop(0)
            try:
                txt = f.get(sm)
            except ConsentRefused as e:
                print(f"  REFUSED {sm} ({e})")
                continue
            if not txt:
                print(f"  err {sm}")
                continue
            walked += 1
            kind = "index" if "<sitemapindex" in txt[:4000].lower() else "urlset"
            locs = LOC.findall(txt)
            print(f"  {sm}  {len(txt):,}B  {kind}  locs={len(locs)}")
            if kind == "index":
                queue.extend(locs[:20])
                continue
            all_locs += locs
        hits = [u for u in all_locs if any(p in u for p in SEEDS) or any(d in u for d in DASHED)]
        isuzu = [u for u in all_locs if "isuzu" in u.lower()]
        print(f"  total locs {len(all_locs):,} | OE-number URLs {len(hits)} | 'isuzu' URLs {len(isuzu)}")
        for u in (hits + isuzu)[:12]:
            print(f"    {u[:160]}")
    print(f"\nfetch stats: {f.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
