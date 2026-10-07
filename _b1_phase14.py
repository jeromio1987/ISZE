# -*- coding: utf-8 -*-
"""B1 phase 14 — decisive checks before writing up:
  1. product pages of the robots-allowed shops: is the price server-rendered?
  2. Inter Cars Portugal (a major TecDoc distributor) — robots verdict + shell?
  3. does any allowed shop carry an Isuzu line / our OE numbers?
"""
from __future__ import annotations

import re
import subprocess
import sys
import time
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
GATE = ISZE / "04_tools" / "autodoc_scraper" / "check_scrape_consent.py"
sys.path.insert(0, str(ISZE / "04_tools" / "delegation" / "parsers"))
from fetch_polite import PoliteFetcher, ConsentRefused   # noqa: E402

B1 = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "_u26" / "B1"
PAGES = B1 / "pages"
PRICE_RE = re.compile(r"\d{1,4}(?:[.,]\d{2})\s?€|€\s?\d{1,4}[.,]\d{2}")

# product pages we already know exist on robots-allowed shops
PRODUCT_PAGES = [
    ("autocenter", "https://autocenter.pt/shop/geral/pneu-nexen-n-blue-hd-205-55-r-16-91-h/"),
    ("pneubeato", "https://www.pneubeato.com/travoes-ebc/isuzu/d-max"),
]


def verdict(base: str, path: str) -> tuple[str, str, str]:
    p = subprocess.run([sys.executable, str(GATE), "--url", base, "--path", path],
                       capture_output=True, text=True, timeout=45)
    first = (p.stdout or "").strip().splitlines()
    first = first[0] if first else ""
    v = "allowed" if p.returncode == 0 else ("blocked" if first.startswith("BLOCKED")
                                             else "unreachable")
    return v, base + path, first


def main() -> int:
    f = PoliteFetcher()
    for tag, url in PRODUCT_PAGES:
        try:
            h = f.get(url)
        except ConsentRefused as e:
            print(f"{tag}: REFUSED {e}")
            continue
        if not h:
            print(f"{tag}: err {url}")
            continue
        (PAGES / f"{tag}__product_probe.html").write_text(h, encoding="utf-8", errors="replace")
        pr = PRICE_RE.findall(h)
        print(f"{tag}: {len(h):,}B  server-side prices={len(pr)}{pr[:6]}  "
              f"isuzu={h.lower().count('isuzu')}  js_price_json={'price' in h.lower()}")

    print("\n### Inter Cars Portugal / EU")
    for base, path in [("https://www.intercars.pt", "/"), ("https://intercars.pt", "/"),
                       ("https://www.intercars.eu", "/"), ("https://katalog.intercars.eu", "/")]:
        v, u, first = verdict(base, path)
        print(f"  {v:<12} {u}   [{first[:70]}]")
        time.sleep(2.2)
        if v == "allowed":
            try:
                h = f.get(base + "/robots.txt")
            except ConsentRefused as e:
                print(f"    robots REFUSED {e}")
                continue
            if h:
                print("    robots:", re.sub(r"\s+", " ", h)[:400])
    print(f"\nfetch stats: {f.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
