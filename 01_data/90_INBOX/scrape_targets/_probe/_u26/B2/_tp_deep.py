# -*- coding: utf-8 -*-
"""B2: turbopecas.pt catalogue deep look + spareparts.pt Shopify check."""
from __future__ import annotations
import io, re, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26")
sys.path.insert(0, str(WT / "04_tools" / "delegation" / "parsers"))
from fetch_polite import PoliteFetcher, ConsentRefused
f = PoliteFetcher()
T = [
    ("tp|shop", "https://www.turbopecas.pt/weblog/"),
    ("tp|loja", "https://www.turbopecas.pt/loja/"),
    ("tp|marcas", "https://www.turbopecas.pt/marcas/"),
    ("tp|produto_guess", "https://www.turbopecas.pt/produto/"),
    ("tp|sitemap", "https://www.turbopecas.pt/sitemap.xml"),
    ("tp|sitemap_idx", "https://www.turbopecas.pt/sitemap_index.xml"),
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
        print("   locs:", len(locs), locs[:10])
    else:
        links = sorted(set(re.findall(r'href="([^"]*(?:produto|product|loja|shop|catalog)[^"]*)"', b, re.I)))[:20]
        txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", b))
        print("   links:", links)
        print("   ", txt[:200])
