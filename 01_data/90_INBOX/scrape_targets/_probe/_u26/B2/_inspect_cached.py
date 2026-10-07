# -*- coding: utf-8 -*-
"""B2: inspect cached result pages offline (no fetch)."""
from __future__ import annotations
import io, re, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26")
sys.path.insert(0, str(WT / "04_tools" / "delegation" / "parsers"))
from fetch_polite import PoliteFetcher
f = PoliteFetcher(offline=True)
PN = "8982705240"
URLS = [
    ("truckparts", f"https://www.truckparts.pt/?s={PN}"),
    ("sotecnica", f"https://www.sotecnica.pt/?s={PN}"),
    ("turbopecas", f"https://www.turbopecas.pt/?s={PN}"),
    ("isuzu.pt", f"https://www.isuzu.pt/?s={PN}"),
    ("ascendum", f"https://www.ascendum.pt/?s={PN}"),
]
TAG = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.I|re.S)
for label, url in URLS:
    html = f.get(url)
    if not html:
        print(f"### {label}: NO CACHE"); continue
    body = TAG.sub(" ", html)
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))
    print(f"\n### {label} ({len(html)} bytes)")
    # find context around 'resultado' / 'encontrad' / 'no results'
    for kw in ["resultado", "encontrad", "Nenhum", "no products", "Nothing", "produtos", "0 resultado"]:
        for m in re.finditer(kw, txt, re.I):
            print("   >>", txt[max(0,m.start()-90):m.start()+140])
            break
    # price-like tokens
    prices = re.findall(r"\u20ac\s*\d+[.,]\d{2}|\d+[.,]\d{2}\s*\u20ac", txt)
    print("   prices:", prices[:10], "count", len(prices))
