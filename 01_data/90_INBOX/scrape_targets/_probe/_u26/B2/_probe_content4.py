# -*- coding: utf-8 -*-
"""B2 content probe 4: new allowed candidates."""
from __future__ import annotations
import io, json, re, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26")
sys.path.insert(0, str(WT / "04_tools" / "delegation" / "parsers"))
from fetch_polite import PoliteFetcher, ConsentRefused
HERE = Path(__file__).resolve().parent
PN = "8982705240"; C = "ADBP420136"
T = [
    ("motointegrator.pt", f"https://www.motointegrator.pt/search?q={PN}"),
    ("motointegrator.pt[c]", f"https://www.motointegrator.pt/search?q={C}"),
    ("aeromotors.pl", f"https://www.aeromotors.pl/search?q={PN}"),
    ("spareparts.pt", f"https://www.spareparts.pt/?s={PN}&post_type=product"),
    ("pecasusadas.pt", f"https://www.pecasusadas.pt/?s={PN}&post_type=product"),
    ("autousados.pt", f"https://www.autousados.pt/?s={PN}&post_type=product"),
    ("grupoandres.com", f"https://www.grupoandres.com/?s={PN}&post_type=product"),
    ("truckparts-s", "https://www.truckparts.pt/loja/"),
    ("truckparts-p", "https://www.truckparts.pt/produtos/"),
]
PRICE = re.compile(r"(?:EUR|\u20ac|PLN|z\u0142)\s*\d|\d+[.,]\d{2}\s*(?:\u20ac|EUR|z\u0142|PLN)")
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
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", TAG.sub(" ", html))).strip()
    rec["bytes"] = len(html); rec["text_len"] = len(txt); rec["prices"] = len(PRICE.findall(txt))
    rec["has_pn"] = PN in html.replace("-", "")
    low = txt.lower()
    for kw in ["nothing found", "não foi possível", "nie znaleziono", "no results", "0 resultado", "brak wynik"]:
        if kw in low: rec["empty"] = kw; break
    rec["verdict"] = "prices" if rec["prices"] > 0 else ("empty" if "empty" in rec else "no_prices")
    rec["head"] = txt[:200]
    out.append(rec)
    print(f"{label:<20} b={rec['bytes']:<8} txt={rec['text_len']:<7} prices={rec['prices']:<4} empty={rec.get('empty','-')} -> {rec['verdict']}")
    print(f"    {rec['head']!r}")
(HERE / "_content_probe4.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print("stats:", f.stats)
