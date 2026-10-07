# -*- coding: utf-8 -*-
"""B1 phase 2 — read robots.txt of the hosts the gate allowed, so a compliant search
path can be chosen before any part page is fetched.

Saves each robots.txt to B1/robots/<host>.robots.txt and prints the directives that
matter (Sitemap / Disallow / Allow) plus the exact paths that would be refused.

robots.txt itself is fetched with the declared bot identity, exactly as the recon did.
"""
from __future__ import annotations

import sys
from pathlib import Path

import requests

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

UA = "ISZE-parts-research/1.0 (+aftersales analytics; contact via IML)"
HERE = Path(__file__).resolve().parent


def root(s: Path) -> Path:
    for c in [s, *s.parents]:
        if (c / "04_tools" / "autodoc_scraper" / "check_scrape_consent.py").exists():
            return c
    raise SystemExit("root not found")


ISZE = root(HERE)
B1 = HERE if HERE.name == "B1" else (
    ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "_u26" / "B1")

ALLOWED = [
    "https://www.soauto.pt", "https://www.roady.pt", "https://www.feuvert.pt",
    "https://www.autosil.pt", "https://www.motocar.pt", "https://www.autopartslogistic.com",
    "https://www.ersatzteile-24.com", "https://www.custojusto.pt",
]


def main() -> int:
    out = B1 / "robots"
    out.mkdir(parents=True, exist_ok=True)
    for base in ALLOWED:
        host = base.split("//", 1)[-1]
        url = base + "/robots.txt"
        try:
            r = requests.get(url, timeout=25, headers={"User-Agent": UA})
        except Exception as e:                                   # noqa: BLE001
            print(f"\n=== {host} === ERROR {str(e)[:100]}")
            continue
        (out / f"{host}.robots.txt").write_bytes(r.content)
        print(f"\n=== {host} ===  HTTP {r.status_code}  {len(r.content)} bytes")
        if r.status_code != 200:
            print("  (no usable robots.txt — treated as blocked downstream)")
            continue
        text = r.text
        for ln in text.splitlines():
            s = ln.strip()
            if not s or s.startswith("#"):
                continue
            low = s.lower()
            if low.startswith(("disallow", "allow", "sitemap", "crawl-delay")):
                print("  " + s[:150])
    print(f"\nsaved robots to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
