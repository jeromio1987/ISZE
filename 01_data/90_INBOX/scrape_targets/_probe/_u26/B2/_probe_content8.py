# -*- coding: utf-8 -*-
"""B2 content probe 8: bragauto/mcr/sulpecas."""
from __future__ import annotations
import io, re, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26")
sys.path.insert(0, str(WT / "04_tools" / "delegation" / "parsers"))
from fetch_polite import PoliteFetcher, ConsentRefused
f = PoliteFetcher()
PN = "8982705240"
T = [
    ("bragauto", f"https://www.bragauto.pt/?s={PN}&post_type=product"),
    ("bragauto|isuzu", "https://www.bragauto.pt/?s=isuzu&post_type=product"),
    ("mcr", f"https://www.mcr.pt/?s={PN}"),
    ("mcr|isuzu", "https://www.mcr.pt/?s=isuzu"),
    ("sulpecas", f"https://www.sulpecas.pt/?s={PN}"),
    ("sulpecas|isuzu", "https://www.sulpecas.pt/?s=isuzu"),
]
TAG = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.I|re.S)
for label, url in T:
    try:
        b = f.get(url)
    except ConsentRefused:
        print(f"{label:<18} CONSENT REFUSED"); continue
    if not b:
        print(f"{label:<18} NO BODY"); continue
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", TAG.sub(" ", b))).strip()
    pr = re.findall(r"\u20ac\s*\d[\d.,]*|\d[\d.,]*\s*\u20ac", txt)
    print(f"{label:<18} b={len(b):<8} txt={len(txt):<7} prices={len(pr)}")
    print("   ", txt[:230])
