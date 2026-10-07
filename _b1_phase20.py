# -*- coding: utf-8 -*-
"""B1 phase 20 — three decisive checks, then stop:
  1. megapecas: does an Isuzu make/model browse return product cards with a price?
  2. pneubeato: the EBC applications page for Isuzu — products/prices?
  3. b-parts.com and a few last PT shops: robots verdict.
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
PAGES = B1 / "pages"
SHARED = B1.parent / "B_HOSTS_CLAIMED.csv"
PRICE = re.compile(r"\d{1,4}(?:[.,]\d{2})\s?€")
NUM = re.compile(r'"numberOfItems":(\d+)')

BATTERY = ["www.b-parts.com", "www.b-parts.pt", "www.autoteile-preiswert.pt",
           "www.piecesauto.pt", "www.oscaro.es", "www.auto-doc.pt", "www.autodoc24.pt",
           "www.mister-auto.com", "www.repuestoscoche.es", "www.autoparts-24.pt"]


def verdict(base, path):
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


def main() -> int:
    f = PoliteFetcher()

    print("### 1. megapecas Isuzu browse")
    for u in ["https://megapecas.pt/pt/produtos?Make=ISUZU",
              "https://megapecas.pt/pt/produtos?Make=2",
              "https://megapecas.pt/pt/ProductListForm?Make=ISUZU&Search="]:
        try:
            h = f.get(u)
        except ConsentRefused as e:
            print(f"  REFUSED {u} ({e})")
            continue
        if not h:
            print(f"  err {u}")
            continue
        pr = PRICE.findall(h)
        n = NUM.search(h)
        print(f"  {u}\n    {len(h):,}B prices={len(pr)} numberOfItems={n.group(1) if n else '-'} "
              f"isuzu={h.lower().count('isuzu')}")

    print("\n### 2. pneubeato EBC applications (Isuzu)")
    for u in ["https://www.pneubeato.com/travoes-ebc-aplicacoes.html?marca=isuzu",
              "https://www.pneubeato.com/travoes-ebc-discos.html",
              "https://www.pneubeato.com/travoes-ebc-kit-pastilha-discos.html"]:
        try:
            h = f.get(u)
        except ConsentRefused as e:
            print(f"  REFUSED {u} ({e})")
            continue
        if not h:
            print(f"  err {u}")
            continue
        tag = re.sub(r"[^a-z0-9]+", "_", u.split("pneubeato.com/")[-1].lower())[:40]
        (PAGES / f"pneubeato__{tag}.html").write_text(h, encoding="utf-8", errors="replace")
        pr = PRICE.findall(h)
        ebc = sorted(set(re.findall(r"\bD[PZ]?\d{3,5}[A-Z]?\b", h)))[:8]
        print(f"  {u}\n    {len(h):,}B prices={len(pr)} ebc_refs={ebc} isuzu={h.lower().count('isuzu')}")

    print("\n### 3. last robots battery")
    claims = []
    tried = B1 / "tried.csv"
    with tried.open("a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        for host in BATTERY:
            base = "https://" + host
            v, first = verdict(base, "/")
            time.sleep(2.2)
            print(f"  {v:<12} {host}")
            w.writerow([host, base + "/", v, f"phase20 sweep | {first}",
                        datetime.now(timezone.utc).isoformat(timespec="seconds")])
            claims.append([host, "B1", v, "", "phase20 sweep"])
    with SHARED.open("a", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerows(claims)
    print(f"\nfetch stats: {f.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
