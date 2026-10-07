# -*- coding: utf-8 -*-
"""B2: verify the 3 spareparts.pt "priced" false positives."""
from __future__ import annotations
import io, re, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26")
sys.path.insert(0, str(WT / "04_tools" / "delegation" / "parsers"))
from fetch_polite import PoliteFetcher
f = PoliteFetcher(offline=True)
HERE = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\01_data\90_INBOX\scrape_targets\_probe\_u26\B2")
for pn in ["116277", "6007306", "14459"]:
    p = HERE / "pages" / f"spareparts.pt__{pn}.html"
    if not p.exists():
        print(pn, "no page"); continue
    b = p.read_text(encoding="utf-8", errors="replace")
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", b))
    pr = re.findall(r".{40}\u20ac\s*\d[\d.,]*.{20}", txt)
    print(f"### {pn}: search term present={pn in b}  prices={pr[:3]}")
    # is there a real product for the PN?
    print("   title:", (re.search(r"<title[^>]*>(.*?)</title>", b, re.I|re.S) or [None,""])[1][:80] if re.search(r"<title", b, re.I) else "?")
