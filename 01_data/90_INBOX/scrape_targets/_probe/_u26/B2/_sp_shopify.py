# -*- coding: utf-8 -*-
"""B2: spareparts.pt Shopify search + product sitemap scan."""
from __future__ import annotations
import io, re, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26")
sys.path.insert(0, str(WT / "04_tools" / "delegation" / "parsers"))
from fetch_polite import PoliteFetcher, ConsentRefused
f = PoliteFetcher()
T = [
    ("sp|search_oe", "https://spareparts.pt/search?q=8982705240"),
    ("sp|search_comp", "https://spareparts.pt/search?q=ADBP420136"),
    ("sp|search_isuzu", "https://spareparts.pt/search?q=isuzu"),
    ("sp|search_brake", "https://spareparts.pt/search?q=brake+pad"),
    ("sp|sm_prod1", "https://spareparts.pt/sitemap_products_1.xml"),
    ("sp|sm_agentic", "https://spareparts.pt/sitemap_agentic_discovery.xml"),
]
for label, url in T:
    try:
        b = f.get(url)
    except ConsentRefused:
        print(f"{label:<18} CONSENT REFUSED"); continue
    if not b:
        print(f"{label:<18} NO BODY"); continue
    print(f"{label:<18} len={len(b)}")
    if "sitemap" in label:
        locs = re.findall(r"<loc>([^<]+)</loc>", b)
        print("   locs:", len(locs), locs[:8])
        hits = [l for l in locs if re.search(r"isuzu|brake|filter|travao|travão|oleo|óleo", l, re.I)]
        print("   interest:", hits[:15])
    else:
        txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", b))
        pr = re.findall(r"\u20ac\s*\d[\d.,]*|\d[\d.,]*\s*\u20ac", txt)
        print("   prices:", pr[:8], "count", len(pr))
        print("   ", txt[:260])
