# -*- coding: utf-8 -*-
"""B1 phase 4 — deep probe of the newest allowed hosts: home + a real OE-number search.

For each host: fetch the home page (find the search URL pattern), then fetch the shop's
own search for three seed Isuzu numbers (2 brake-pad, 1 oil filter) and report:
  * HTTP status and whether the result page is server-rendered;
  * whether the searched number appears on the page;
  * whether prices appear in the RAW html (no JS);
  * whether EUR / IVA wording appears.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

HERE = Path(__file__).resolve().parent
for c in [HERE, *HERE.parents]:
    if (c / "04_tools" / "autodoc_scraper" / "check_scrape_consent.py").exists():
        ISZE = c
        break
sys.path.insert(0, str(ISZE / "04_tools" / "delegation" / "parsers"))
from fetch_polite import PoliteFetcher, ConsentRefused   # noqa: E402

B1 = HERE if HERE.name == "B1" else (
    ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "_u26" / "B1")
PAGES = B1 / "pages"

SEEDS = ["8982447940", "8975546610", "8982705240"]     # 2 brake-pad kits, 1 oil filter

# host -> candidate search URLs to try (the shop's own search)
HOSTS = {
    "www.epecas.pt": ["https://www.epecas.pt/", "https://www.epecas.pt/pesquisa?q={pn}",
                      "https://www.epecas.pt/search?q={pn}"],
    "www.areal.pt": ["https://www.areal.pt/", "https://www.areal.pt/pesquisa?q={pn}"],
    "www.autoparts24.eu": ["https://www.autoparts24.eu/", "https://www.autoparts24.eu/search?q={pn}",
                           "https://www.autoparts24.eu/pesquisa?q={pn}"],
    "www.motointegrator.com": ["https://www.motointegrator.com/"],
    "www.winparts.nl": ["https://www.winparts.nl/", "https://www.winparts.nl/search?q={pn}"],
    "www.todoparatucoche.com": ["https://www.todoparatucoche.com/", "https://www.todoparatucoche.com/buscar?q={pn}"],
}

PRICE_RE = re.compile(r"(?:EUR|€)\s?\d{1,4}[.,]\d{2}|\d{1,4}[.,]\d{2}\s?(?:EUR|€)")
VAT_RE = re.compile(r"(?i)\b(iva|vat|incl\.?\s*iva)\b")


def look(html: str, pn: str) -> str:
    prices = PRICE_RE.findall(html)
    vis = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
    return (f"{len(html):,}B  pn_on_page={pn in html}  price_tokens={len(prices)}{prices[:4]}  "
            f"IVA={bool(VAT_RE.search(html))}  visible={len(vis):,}B")


def main() -> int:
    f = PoliteFetcher()
    for host, urls in HOSTS.items():
        print(f"\n{'='*84}\n### {host}")
        for tpl in urls:
            if "{pn}" in tpl:
                for pn in SEEDS:
                    url = tpl.format(pn=pn)
                    try:
                        html = f.get(url)
                    except ConsentRefused as e:
                        print(f"  REFUSED {url} :: {e}")
                        continue
                    if not html:
                        print(f"  nomatch/err  {url}")
                        continue
                    tag = f"{host}__search_{pn}"
                    (PAGES / f"{tag}.html").write_text(html, encoding="utf-8", errors="replace")
                    print(f"  {url}\n    {look(html, pn)}")
            else:
                try:
                    html = f.get(tpl)
                except ConsentRefused as e:
                    print(f"  REFUSED {tpl} :: {e}")
                    continue
                if not html:
                    print(f"  nomatch/err  {tpl}")
                    continue
                (PAGES / f"{host}__home.html").write_text(html, encoding="utf-8", errors="replace")
                print(f"  {tpl}\n    {look(html, 'n/a')}")
                forms = re.findall(r"<form\b[^>]*action=[\"']([^\"']+)[\"'][^>]*>", html, re.I)
                names = re.findall(r"<input[^>]*name=[\"']([^\"']+)[\"']", html, re.I)
                print(f"    forms={forms[:5]} inputs={sorted(set(names))[:12]}")
    print(f"\nfetch stats: {f.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
