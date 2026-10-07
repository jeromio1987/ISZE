# -*- coding: utf-8 -*-
"""B1 phase 2e — read robots.txt of the remaining allowed hosts and print the directives
that decide whether a part-number search is permitted.
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
for c in [HERE, *HERE.parents]:
    if (c / "04_tools" / "autodoc_scraper" / "check_scrape_consent.py").exists():
        ISZE = c
        break
B1 = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "_u26" / "B1"

HOSTS = [
    "https://www.winparts.es", "https://www.winparts.nl", "https://www.todoparatucoche.com",
    "https://www.oscaro.pt", "https://www.casadaspecas.pt", "https://www.rodasa.com",
    "https://www.pneubeato.com", "https://www.midas.pt", "https://www.nortecar.pt",
    "https://www.parts.pt", "https://www.areal.pt", "https://www.epecas.pt",
    "https://www.auto5.pt", "https://www.rodauto.pt", "https://www.silvauto.pt",
    "https://www.autoparts24.eu", "https://www.rasch.pt", "https://www.agauto.pt",
    "https://www.lojadaspecas.pt",
]


def main() -> int:
    out = B1 / "robots"
    out.mkdir(parents=True, exist_ok=True)
    for base in HOSTS:
        host = base.split("//", 1)[-1]
        try:
            r = requests.get(base + "/robots.txt", timeout=25, headers={"User-Agent": UA})
        except Exception as e:                                   # noqa: BLE001
            print(f"\n=== {host} === ERROR {str(e)[:90]}")
            continue
        (out / f"{host}.robots.txt").write_bytes(r.content)
        print(f"\n=== {host} ===  HTTP {r.status_code}  {len(r.content)} bytes")
        if r.status_code != 200:
            continue
        for ln in r.text.splitlines():
            s = ln.strip()
            if s and not s.startswith("#") and s.lower().startswith(
                    ("disallow", "allow", "sitemap", "crawl-delay")):
                print("  " + s[:150])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
