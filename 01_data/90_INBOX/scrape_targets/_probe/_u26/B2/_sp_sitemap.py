# -*- coding: utf-8 -*-
"""B2: spareparts.pt sitemap + is it a catalogue at all."""
from __future__ import annotations
import io, re, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26")
sys.path.insert(0, str(WT / "04_tools" / "delegation" / "parsers"))
from fetch_polite import PoliteFetcher, ConsentRefused
f = PoliteFetcher()
T = [("sp|sitemap", "https://www.spareparts.pt/sitemap.xml"),
     ("sp|sitemap_index", "https://www.spareparts.pt/sitemap_index.xml"),
     ("sp|shop", "https://www.spareparts.pt/loja/"),
     ("sp|produtos", "https://www.spareparts.pt/produtos/")]
for label, url in T:
    try:
        b = f.get(url)
    except ConsentRefused:
        print(f"{label:<18} CONSENT REFUSED"); continue
    if not b:
        print(f"{label:<18} NO BODY"); continue
    print(f"{label:<18} len={len(b)} :: {b[:600]!r}")
