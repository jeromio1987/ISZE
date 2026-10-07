# -*- coding: utf-8 -*-
"""B2 content probe: fetch one search page per allowed host and judge it."""
from __future__ import annotations
import io, json, re, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26")
sys.path.insert(0, str(WT / "04_tools" / "delegation" / "parsers"))
from fetch_polite import PoliteFetcher, ConsentRefused  # noqa: E402
HERE = Path(__file__).resolve().parent
PN = "8982705240"
COMP = "ADBP420136"
TARGETS = [
    ("b-parts.com", f"https://www.b-parts.com/pt/search?q={PN}"),
    ("b-parts.com[c]", f"https://www.b-parts.com/pt/search?q={COMP}"),
    ("truckparts.pt", f"https://www.truckparts.pt/pesquisa?q={PN}"),
    ("truckparts.pt[s]", f"https://www.truckparts.pt/search?q={PN}"),
    ("sotecnica.pt", f"https://www.sotecnica.pt/pesquisa?q={PN}"),
    ("sotecnica.pt[s]", f"https://www.sotecnica.pt/search?q={PN}"),
    ("ascendum.pt", "https://www.ascendum.pt/"),
    ("pecauto.com", f"https://www.pecauto.com/pesquisa?q={PN}"),
    ("pecauto.com[s]", f"https://www.pecauto.com/search?q={PN}"),
    ("turbopecas.pt", f"https://www.turbopecas.pt/pesquisa?q={PN}"),
    ("turbopecas.pt[s]", f"https://www.turbopecas.pt/search?q={PN}"),
    ("roady.pt", "https://www.roady.pt/"),
    ("midas.pt", "https://www.midas.pt/"),
    ("feuvert.pt", "https://www.feuvert.pt/"),
    ("isuzu.pt", "https://www.isuzu.pt/"),
]
PRICE_RE = re.compile(r"(?:EUR|\u20ac|\d+[.,]\d{2}\s*(?:\u20ac|EUR))", re.I)
TAG_RE = re.compile(r"<[^>]+>")
out = []
f = PoliteFetcher()
for label, url in TARGETS:
    rec = {"label": label, "url": url, "http": None, "bytes": 0, "verdict": "?", "notes": ""}
    try:
        html = f.get(url)
    except ConsentRefused:
        rec["verdict"] = "consent_refused"; out.append(rec); print(f"{label:<22} CONSENT REFUSED"); continue
    if html is None:
        rec["verdict"] = "no_body(http_or_error)"; out.append(rec); print(f"{label:<22} NO BODY"); continue
    text = re.sub(r"\s+", " ", TAG_RE.sub(" ", html))
    rec["bytes"] = len(html); rec["text_len"] = len(text)
    hits = len(PRICE_RE.findall(text)); rec["price_hits"] = hits
    rec["has_pn"] = PN in html.replace("-", "")
    js = html.count("<script"); rec["scripts"] = js
    if hits > 0 and len(text) > 800:
        rec["verdict"] = "server_rendered_prices"
    elif len(text) < 800:
        rec["verdict"] = "likely_js_shell"
    else:
        rec["verdict"] = "html_no_prices"
    rec["notes"] = text[:220]
    out.append(rec)
    print(f"{label:<22} bytes={rec['bytes']:<8} text={rec['text_len']:<7} price_hits={hits:<4} scripts={js:<3} -> {rec['verdict']}")
(HERE / "_content_probe.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print("\nstats:", f.stats)
