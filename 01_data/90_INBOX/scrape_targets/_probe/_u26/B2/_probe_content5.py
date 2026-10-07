# -*- coding: utf-8 -*-
"""B2 content probe 5: spareparts.pt structure + more PT WooCommerce shops."""
from __future__ import annotations
import io, json, re, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26")
sys.path.insert(0, str(WT / "04_tools" / "delegation" / "parsers"))
from fetch_polite import PoliteFetcher, ConsentRefused
HERE = Path(__file__).resolve().parent
PN = "8982705240"
C = "ADBP420136"
T = [
    ("spareparts.pt|home", "https://www.spareparts.pt/"),
    ("spareparts.pt|prod", f"https://www.spareparts.pt/?s={PN}&post_type=product"),
    ("spareparts.pt|comp", f"https://www.spareparts.pt/?s={C}&post_type=product"),
    ("spareparts.pt|isuzu", "https://www.spareparts.pt/?s=isuzu&post_type=product"),
    ("spareparts.pt|wp-json", "https://www.spareparts.pt/wp-json/wp/v2/product?search=isuzu"),
]
TAG = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.I|re.S)
out = []
f = PoliteFetcher()
for label, url in T:
    rec = {"label": label, "url": url}
    try:
        html = f.get(url)
    except ConsentRefused:
        rec["verdict"] = "consent_refused"; out.append(rec); print(f"{label:<22} CONSENT REFUSED"); continue
    if not html:
        rec["verdict"] = "no_body"; out.append(rec); print(f"{label:<22} NO BODY"); continue
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", TAG.sub(" ", html))).strip()
    rec["bytes"] = len(html); rec["text_len"] = len(txt); rec["price"] = len(re.findall(r"\u20ac\s*\d|\d+[.,]\d{2}\s*\u20ac", txt))
    rec["head"] = txt[:300]
    out.append(rec)
    print(f"{label:<22} b={len(html):<8} txt={len(txt):<7} prices={rec['price']}")
    print(f"    {txt[:260]!r}")
(HERE / "_content_probe5.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print("stats:", f.stats)
