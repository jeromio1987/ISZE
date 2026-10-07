# -*- coding: utf-8 -*-
"""B2 content probe 9: final allowed candidates."""
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
    ("turbodiesel", f"https://www.turbodiesel.pt/?s={PN}&post_type=product"),
    ("turbodiesel|isuzu", "https://www.turbodiesel.pt/?s=isuzu&post_type=product"),
    ("radiadores", f"https://www.radiadores.pt/?s={PN}&post_type=product"),
    ("radiadores|isuzu", "https://www.radiadores.pt/?s=isuzu&post_type=product"),
    ("baterias", f"https://www.baterias.pt/?s={PN}&post_type=product"),
    ("isuzuportugal.com", f"https://www.isuzuportugal.com/?s={PN}"),
    ("isuzuportugal.com|prod", "https://www.isuzuportugal.com/?s=isuzu&post_type=product"),
]
TAG = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.I|re.S)
for label, url in T:
    try:
        b = f.get(url)
    except ConsentRefused:
        print(f"{label:<22} CONSENT REFUSED"); continue
    if not b:
        print(f"{label:<22} NO BODY"); continue
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", TAG.sub(" ", b))).strip()
    pr = re.findall(r"\u20ac\s*\d[\d.,]*|\d[\d.,]*\s*\u20ac", txt)
    print(f"{label:<22} b={len(b):<8} txt={len(txt):<7} prices={len(pr)}")
    print("   ", txt[:220])
