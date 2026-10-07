# -*- coding: utf-8 -*-
"""B1 phase 4b — deep probe: autopartslogistic.com, winparts.nl, soauto/feuvert/roady.

Try each host's own search (and a known product URL for Winparts) for the seed Isuzu
numbers; report whether the RAW html carries the number and a price. Fetches through
PoliteFetcher (consent gate + >=2.2 s + cache). Nothing parsed to rows here.
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
SEEDS = ["8982447940", "8975546610", "8982705240"]

PLAN = [
    # (url template, note)  {pn} substituted
    ("https://www.autopartslogistic.com/", "home"),
    ("https://www.autopartslogistic.com/search?q={pn}", "guess search"),
    ("https://www.autopartslogistic.com/index.php?controller=search&s={pn}", "prestashop search"),
    ("https://www.autopartslogistic.com/buscar?q={pn}", "es search"),
    ("https://www.autopartslogistic.com/es/buscar?q={pn}", "es search"),
    ("https://www.winparts.nl/", "home"),
    ("https://www.winparts.nl/zoeken?zoekterm={pn}", "nl search"),
    ("https://www.winparts.nl/zoeken/?zoekterm={pn}", "nl search2"),
]

PRICE_RE = re.compile(r"(?:EUR|€)\s?\d{1,4}[.,]\d{2}|\d{1,4}[.,]\d{2}\s?(?:EUR|€)")


def report(url: str, html: str, pn: str) -> None:
    prices = PRICE_RE.findall(html)
    print(f"    {url}\n      {len(html):,}B  pn={pn in html}  price_tokens={len(prices)}{prices[:4]}")


def main() -> int:
    f = PoliteFetcher()
    for tpl, note in PLAN:
        print(f"\n=== {note}: {tpl}")
        if "{pn}" in tpl:
            for pn in SEEDS:
                url = tpl.format(pn=pn)
                try:
                    html = f.get(url)
                except ConsentRefused as e:
                    print(f"    REFUSED {url} :: {e}")
                    continue
                if not html:
                    print(f"    err/non-200  {url}")
                    continue
                (PAGES / f"deep_{re.sub(r'[^a-z0-9]', '_', url.lower())}__{pn}.html").write_text(
                    html, encoding="utf-8", errors="replace")
                report(url, html, pn)
        else:
            try:
                html = f.get(tpl)
            except ConsentRefused as e:
                print(f"    REFUSED {tpl} :: {e}")
                continue
            if not html:
                print(f"    err/non-200  {tpl}")
                continue
            (PAGES / f"deep_{re.sub(r'[^a-z0-9]', '_', tpl.lower())}__home.html").write_text(
                html, encoding="utf-8", errors="replace")
            report(tpl, html, "n/a")
            forms = re.findall(r"<form\b[^>]*action=[\"']([^\"']+)[\"'][^>]*>(.{0,800}?)</form>",
                               html, re.I | re.S)
            for act, blk in forms[:6]:
                names = re.findall(r"name=[\"']([^\"']+)[\"']", blk, re.I)
                print(f"      form action={act[:80]} names={names[:8]}")
    print(f"\nfetch stats: {f.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
