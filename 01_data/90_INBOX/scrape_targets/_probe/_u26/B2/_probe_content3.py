# -*- coding: utf-8 -*-
"""B2 content probe 3: product-type WP searches, and real catalogues."""
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
    ("turbopecas[prod]", f"https://www.turbopecas.pt/?s={PN}&post_type=product"),
    ("truckparts[prod]", f"https://www.truckparts.pt/?s={PN}&post_type=product"),
    ("autosueco[prod]", f"https://www.autosueco.pt/?s={PN}&post_type=product"),
    ("lojadepecas[prod]", f"https://www.lojadepecas.pt/?s={PN}&post_type=product"),
    ("euromaster[prod]", f"https://www.euromaster.pt/?s={PN}&post_type=product"),
    ("andres[prod]", f"https://www.andres.pt/?s={PN}&post_type=product"),
    ("autosueco[comp]", f"https://www.autosueco.pt/?s={C}&post_type=product"),
    ("partsouq", f"https://partsouq.com/en/search/all?q={PN}"),
    ("amayama", f"https://www.amayama.com/en/search?q={PN}"),
    ("pecauto[pesquisa]", "https://www.pecauto.com/pesquisa"),
    ("pecauto[sitemap]", "https://www.pecauto.com/sitemap.xml"),
]
PRICE = re.compile(r"(?:EUR|\u20ac)\s*\d|\d+[.,]\d{2}\s*(?:\u20ac|EUR)")
TAG = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.I|re.S)
out = []
f = PoliteFetcher()
for label, url in T:
    rec = {"label": label, "url": url, "bytes": 0, "verdict": "?"}
    try:
        html = f.get(url)
    except ConsentRefused:
        rec["verdict"] = "consent_refused"; out.append(rec); print(f"{label:<20} CONSENT REFUSED"); continue
    if not html:
        rec["verdict"] = "no_body"; out.append(rec); print(f"{label:<20} NO BODY"); continue
    body = TAG.sub(" ", html)
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()
    rec["bytes"] = len(html); rec["text_len"] = len(txt)
    rec["prices"] = len(PRICE.findall(txt))
    rec["has_pn_hit"] = PN in html.replace("-", "")
    low = txt.lower()
    for kw in ["nothing found", "nao foi possivel", "não foi possível", "no results", "0 resultado",
               "no products were found", "we couldn", "nenhum"]:
        if kw in low:
            rec["empty_marker"] = kw; break
    rec["verdict"] = "prices" if rec["prices"] > 0 else ("empty" if "empty_marker" in rec else "no_prices")
    rec["head"] = txt[:200]
    out.append(rec)
    print(f"{label:<20} b={rec['bytes']:<8} txt={rec['text_len']:<7} prices={rec['prices']:<4} empty={rec.get('empty_marker','-')} -> {rec['verdict']}")
    print(f"    {rec['head']!r}")
(HERE / "_content_probe3.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print("stats:", f.stats)
