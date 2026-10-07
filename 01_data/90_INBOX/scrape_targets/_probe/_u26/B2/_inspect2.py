# -*- coding: utf-8 -*-
"""B2: inspect remaining cached result pages offline."""
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
    ("sotecnica", f"https://www.sotecnica.pt/?s={PN}"),
    ("ascendum", f"https://www.ascendum.pt/?s={PN}"),
    ("midas", f"https://www.midas.pt/?s={PN}"),
    ("roady", f"https://www.roady.pt/?s={PN}"),
    ("sotecnica_home", "https://www.sotecnica.pt/"),
    ("ascendum_home", "https://www.ascendum.pt/"),
    ("datapt_home", "https://www.datapremium.pt/"),
]
TAG = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.I|re.S)
for label, url in URLS:
    html = f.get(url)
    if not html:
        print(f"### {label}: NO CACHE"); continue
    body = TAG.sub(" ", html)
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()
    print(f"\n### {label} ({len(html)}b) :: {txt[:600]}")
