# -*- coding: utf-8 -*-
"""B2: does either working PT search index Isuzu at all?"""
from __future__ import annotations
import io, re, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26")
sys.path.insert(0, str(WT / "04_tools" / "delegation" / "parsers"))
from fetch_polite import PoliteFetcher, ConsentRefused
TAG = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.I|re.S)
f = PoliteFetcher()
T = [
    ("truckparts|isuzu", "https://www.truckparts.pt/?s=isuzu&post_type=product"),
    ("truckparts|dmax", "https://www.truckparts.pt/?s=d-max&post_type=product"),
    ("truckparts|filtro", "https://www.truckparts.pt/?s=filtro&post_type=product"),
    ("turbopecas|isuzu", "https://www.turbopecas.pt/?s=isuzu&post_type=product"),
    ("turbopecas|dmax", "https://www.turbopecas.pt/?s=d-max&post_type=product"),
    ("turbopecas|travão", "https://www.turbopecas.pt/?s=trav%C3%A3o&post_type=product"),
]
for label, url in T:
    try:
        html = f.get(url)
    except ConsentRefused:
        print(f"{label:<20} CONSENT REFUSED"); continue
    if not html:
        print(f"{label:<20} NO BODY"); continue
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", TAG.sub(" ", html))).strip()
    m = None
    for kw in ["resultado", "Nothing Found", "Não foi possível", "a procurar por", "Pesquisou por", "resultados"]:
        i = txt.lower().find(kw.lower())
        if i >= 0:
            m = txt[max(0,i-40):i+160]; break
    print(f"{label:<20} b={len(html):<8} :: {m or txt[:180]!r}")
