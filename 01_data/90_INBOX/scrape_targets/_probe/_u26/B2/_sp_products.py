# -*- coding: utf-8 -*-
"""B2: what products does spareparts.pt actually index? (Isuzu / brake / filter)."""
from __future__ import annotations
import io, re, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26")
sys.path.insert(0, str(WT / "04_tools" / "delegation" / "parsers"))
from fetch_polite import PoliteFetcher, ConsentRefused
f = PoliteFetcher()
T = [
    ("isuzu", "https://spareparts.pt/search?q=isuzu"),
    ("dmax", "https://spareparts.pt/search?q=d-max"),
    ("brake", "https://spareparts.pt/search?q=brake+pad"),
    ("oelfilter", "https://spareparts.pt/search?q=oil+filter"),
]
for label, url in T:
    try:
        b = f.get(url)
    except ConsentRefused:
        print(f"{label:<12} CONSENT REFUSED"); continue
    if not b:
        print(f"{label:<12} NO BODY"); continue
    # product titles + prices from Shopify JSON-LD / grid
    titles = re.findall(r'"name"\s*:\s*"([^"]{3,90})"', b)
    prices = re.findall(r'"price"\s*:\s*"?([0-9.,]+)', b)
    prod_links = re.findall(r'href="(/products/[^"?#]+)"', b)
    print(f"{label:<12} len={len(b)} titles={len(titles)} prices={len(prices)} links={len(set(prod_links))}")
    print("   titles:", titles[:12])
    print("   prices:", prices[:12])
    print("   links :", sorted(set(prod_links))[:8])
