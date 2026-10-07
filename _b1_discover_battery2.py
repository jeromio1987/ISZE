# -*- coding: utf-8 -*-
"""B1 phase 2b — wider candidate battery: robots verdict per host (via the consent gate).

Covers more Portuguese (.pt) shop domains and the Portuguese storefronts of EU platforms.
Each verdict is appended to B1/tried.csv and to the shared B_HOSTS_CLAIMED.csv, so B2 sees
what is taken. No part page is fetched.
"""
from __future__ import annotations

import csv
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
B1 = HERE if HERE.name == "B1" else (
    ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "_u26" / "B1")
SHARED = B1.parent / "B_HOSTS_CLAIMED.csv"

# host, path, why
BATTERY = [
    # Portuguese parts distributors / shops
    ("https://www.jap.pt", "/", "PT aftermarket distributor JAP"),
    ("https://www.nors.pt", "/", "PT aftermarket distributor Grupo NORS"),
    ("https://www.gruponors.pt", "/", "PT aftermarket distributor Grupo NORS"),
    ("https://www.pecasauto24.pt", "/", "PT online parts shop"),
    ("https://www.pecas24.pt", "/", "PT online parts shop"),
    ("https://www.autopecas24.pt", "/", "PT online parts shop"),
    ("https://www.casadaspecas.pt", "/", "PT online parts shop"),
    ("https://www.dipema.pt", "/", "PT parts distributor"),
    ("https://www.rodasa.com", "/", "PT parts distributor (alt domain)"),
    ("https://www.rasch.pt", "/", "PT parts distributor"),
    ("https://www.agauto.pt", "/", "PT parts distributor"),
    ("https://www.lojadaspecas.pt", "/", "PT online parts shop"),
    ("https://www.pecasonline.com.pt", "/", "PT online parts shop"),
    ("https://www.autopecasonline.pt", "/", "PT online parts shop"),
    ("https://www.pneubeato.com", "/", "PT tyre+parts online"),
    ("https://www.startmotive.com", "/", "PT/EU parts platform (PT domain variants)"),
    ("https://www.autoparts.pt", "/", "PT online parts shop"),
    ("https://www.multiparts.pt", "/", "PT online parts shop"),
    ("https://www.parts.pt", "/", "PT online parts shop"),
    ("https://www.euautoparts.pt", "/", "EU platform PT storefront"),
    ("https://www.winparts.pt", "/", "Winparts PT storefront"),
    ("https://www.skruvat.pt", "/", "Skruvat PT storefront"),
    ("https://www.alvadi.pt", "/", "Alvadi PT storefront"),
    ("https://www.trodo.pt", "/", "Trodo PT storefront"),
    ("https://www.autoteiledirekt.pt", "/", "DE platform PT storefront"),
    ("https://www.pkwteile.pt", "/", "DE platform PT storefront"),
    ("https://www.kfzteile.pt", "/", "DE platform PT storefront"),
    ("https://www.motointegrator.pt", "/", "EU platform PT storefront"),
    ("https://www.buycarparts.pt", "/", "EU platform PT storefront"),
    ("https://www.onlinecarparts.pt", "/", "EU platform PT storefront"),
    ("https://www.autopartspro.pt", "/", "EU platform PT storefront"),
    ("https://www.recambioscoche.es", "/", "ES TecDoc shop, ships PT, EUR"),
    ("https://www.oscaro.es", "/", "ES operator (retired family) - recorded"),
    ("https://www.winparts.es", "/", "Winparts ES storefront"),
    ("https://www.carparts.pt", "/", "PT online parts shop"),
    ("https://www.auto5.pt", "/", "PT chain"),
    ("https://www.midas.pt", "/", "PT chain"),
    ("https://www.rodauto.pt", "/", "PT parts shop"),
    ("https://www.silvauto.pt", "/", "PT parts shop"),
    ("https://www.autopeças.pt", "/", "PT online parts shop"),
    ("https://www.pecas-para-auto.pt", "/", "PT online parts shop"),
    ("https://www.turboparts.pt", "/", "PT parts shop"),
    ("https://www.autopecas.pt", "/", "PT online parts shop"),
    ("https://www.pecas.pt", "/", "PT online parts shop"),
    ("https://www.auto-parts.pt", "/", "PT online parts shop"),
]

NO_RETRY = {"https://www.oscaro.es"}


def verdict(base: str, path: str) -> tuple[str, str]:
    try:
        p = subprocess.run([sys.executable, str(GATE), "--url", base, "--path", path],
                           capture_output=True, text=True, timeout=60)
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
    tried = B1 / "tried.csv"
    rows_claim = []
    with tried.open("a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        for base, path, why in BATTERY:
            if base in NO_RETRY:
                v, first = "not_retried", "operator already blocked/retired in recon"
            else:
                v, first = verdict(base, path)
                time.sleep(2.2)
            host = base.split("//", 1)[-1]
            print(f"  {v:<12} {host:<34} {why}")
            w.writerow([host, base + path, v, f"{why} | {first}",
                        datetime.now(timezone.utc).isoformat(timespec="seconds")])
            rows_claim.append([host, "B1", v, "", why])
    with SHARED.open("a", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerows(rows_claim)
    print(f"\nappended {len(rows_claim)} rows to {tried} and {SHARED}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
