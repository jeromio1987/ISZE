# -*- coding: utf-8 -*-
"""B2 content probe 2: real search endpoints, judge server-rendered prices."""
from __future__ import annotations
import io, json, re, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26")
sys.path.insert(0, str(WT / "04_tools" / "delegation" / "parsers"))
from fetch_polite import PoliteFetcher, ConsentRefused
HERE = Path(__file__).resolve().parent
PN = "8982705240"
TARGETS = [
    ("truckparts.pt|oe", f"https://www.truckparts.pt/?s={PN}"),
    ("sotecnica.pt|oe", f"https://www.sotecnica.pt/?s={PN}"),
    ("turbopecas.pt|oe", f"https://www.turbopecas.pt/?s={PN}"),
    ("roady.pt|oe", f"https://www.roady.pt/?s={PN}"),
    ("midas.pt|oe", f"https://www.midas.pt/?s={PN}"),
    ("isuzu.pt|oe", f"https://www.isuzu.pt/?s={PN}"),
    ("ascendum.pt|oe", f"https://www.ascendum.pt/?s={PN}"),
    ("b-parts.com|oe", f"https://www.b-parts.com/pt/auto-parts/search?q={PN}"),
    ("datapremium.pt|home", "https://www.datapremium.pt/"),
    ("truckparts.pt|comp", "https://www.truckparts.pt/?s=ADBP420136"),
    ("sotecnica.pt|comp", "https://www.sotecnica.pt/?s=ADBP420136"),
]
PRICE_RE = re.compile(r"(?:EUR|\u20ac|\d+[.,]\d{2}\s*(?:\u20ac|EUR))", re.I)
EUR_RE = re.compile(r"\u20ac\s*\d+[.,]\d{2}|\d+[.,]\d{2}\s*\u20ac")
TAG_RE = re.compile(r"<[^>]+>")
out = []
f = PoliteFetcher()
for label, url in TARGETS:
    rec = {"label": label, "url": url, "bytes": 0, "text_len": 0, "verdict": "?", "notes": ""}
    try:
        html = f.get(url)
    except ConsentRefused:
        rec["verdict"] = "consent_refused"; out.append(rec); print(f"{label:<22} CONSENT REFUSED"); continue
    if not html:
        rec["verdict"] = "no_body(http_or_error)"; out.append(rec); print(f"{label:<22} NO BODY"); continue
    text = re.sub(r"\s+", " ", TAG_RE.sub(" ", html))
    rec["bytes"] = len(html); rec["text_len"] = len(text)
    rec["price_hits"] = len(PRICE_RE.findall(text))
    rec["eur_hits"] = len(EUR_RE.findall(text))
    rec["has_pn"] = PN in html.replace("-", "")
    rec["title"] = (re.search(r"<title[^>]*>(.*?)</title>", html, re.I|re.S) or [None,""])[1][:80] if re.search(r"<title[^>]*>(.*?)</title>", html, re.I|re.S) else ""
    if rec["price_hits"] > 0 and len(text) > 800:
        rec["verdict"] = "server_rendered_prices"
    elif len(text) < 800:
        rec["verdict"] = "likely_js_shell"
    else:
        rec["verdict"] = "html_no_prices"
    rec["notes"] = text[:300]
    out.append(rec)
    print(f"{label:<22} bytes={rec['bytes']:<8} text={rec['text_len']:<7} eur={rec['eur_hits']:<4} haspn={rec['has_pn']} -> {rec['verdict']}")
    print(f"    title: {rec['title']!r}")
(HERE / "_content_probe2.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print("\nstats:", f.stats)
