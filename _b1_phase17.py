# -*- coding: utf-8 -*-
"""B1 phase 17 — last robots battery of remaining plausible PT auto-parts e-commerce
domains, then a targeted sitemap check of the allowed auto-parts shops for our seed
OE numbers. Nothing here fetches a part page except through PoliteFetcher.
"""
from __future__ import annotations

import csv
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
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
SHARED = B1.parent / "B_HOSTS_CLAIMED.csv"
LOC = re.compile(r"<loc>\s*(?:<!\[CDATA\[)?\s*(.*?)\s*(?:\]\]>)?\s*</loc>", re.S | re.I)

HOSTS = [
    "www.pecasauto.pt", "www.pecas-online.pt", "www.autopecasonline.pt", "www.lojapecas.pt",
    "www.pecasdecarro.pt", "www.distripecas.pt", "www.servisauto.pt", "www.auto2000.pt",
    "www.motorminuto.pt", "www.gtpecas.pt", "www.jmpecas.pt", "www.partsmal.pt",
    "www.pecasagora.pt", "www.maispecas.pt", "www.pecasoriginais.pt", "www.auto-material.com",
    "www.pecasauto.com", "www.autopecas.pt", "www.pecas.pt", "www.carpecas.pt",
    "www.todasaspecas.pt", "www.pecaspt.pt", "www.auto-parts-online.pt", "www.partsonline.pt",
]


def verdict(base: str, path: str) -> tuple[str, str]:
    try:
        p = subprocess.run([sys.executable, str(GATE), "--url", base, "--path", path],
                           capture_output=True, text=True, timeout=45)
    except subprocess.TimeoutExpired:
        return "unreachable", "timed out"
    lines = (p.stdout or "").strip().splitlines()
    first = lines[0] if lines else ""
    if p.returncode == 0:
        return "allowed", first
    if first.startswith("BLOCKED"):
        return "blocked", first
    return "unreachable", (first or (p.stderr or "").strip()[:120])


SEEDS = [ln.strip() for ln in (B1 / "seed_oe_pns.csv").read_text(encoding="utf-8").splitlines()
         if ln.strip()]
SITEMAPS = [
    ("https://www.casadaspecas.pt", "/sitemap.xml"),
    ("https://www.lojadaspecas.pt", "/sitemap.xml"),
    ("https://www.rodasa.com", "/products-sitemap.xml"),
    ("https://www.pneubeato.com", "/sitemap.xml"),
]


def main() -> int:
    f = PoliteFetcher()
    print("### final robots battery")
    claims = []
    tried = B1 / "tried.csv"
    with tried.open("a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        for host in HOSTS:
            base = "https://" + host
            v, first = verdict(base, "/")
            time.sleep(2.2)
            print(f"  {v:<12} {host}")
            w.writerow([host, base + "/", v, f"phase17 sweep | {first}",
                        datetime.now(timezone.utc).isoformat(timespec="seconds")])
            claims.append([host, "B1", v, "", "phase17 sweep"])
    with SHARED.open("a", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerows(claims)

    print("\n### sitemap OE-number scan on the allowed shops")
    dash = {f"{p[:1]}-{p[1:6]}-{p[6:9]}-{p[9:]}" for p in SEEDS if len(p) == 10}
    for base, path in SITEMAPS:
        try:
            h = f.get(base + path)
        except ConsentRefused as e:
            print(f"  {base}{path}: REFUSED ({e})")
            continue
        if not h:
            print(f"  {base}{path}: err")
            continue
        locs = LOC.findall(h)
        hits = [u for u in locs if any(p in u for p in SEEDS) or any(d in u for d in dash)]
        isu = [u for u in locs if "isuzu" in u.lower()]
        print(f"  {base}{path}: {len(locs):,} locs | seed-OE {len(hits)} | isuzu {len(isu)}")
    print(f"\nfetch stats: {f.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
