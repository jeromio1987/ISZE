# -*- coding: utf-8 -*-
"""B1 phase 9 — final wide robots battery of plausible Portuguese parts-shop domains
(plus a few ES shops that ship to PT). Records every verdict; nothing fetched beyond robots.
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
B1 = ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "_u26" / "B1"
SHARED = B1.parent / "B_HOSTS_CLAIMED.csv"

HOSTS = [
    "www.autopecas-online.pt", "www.autopecas.com.pt", "www.pecas.online", "www.pecasauto-online.com",
    "www.autoparts-online.pt", "www.lojadopecas.pt", "www.pecasdecarro.pt", "www.pecasautomoveis.pt",
    "www.superpecas.pt", "www.megapecas.pt", "www.pecasja.pt", "www.mundodaspecas.pt",
    "www.mundopecas.pt", "www.pecas24.pt", "www.casadopneu.pt", "www.pneusonline.pt",
    "www.autoboutique.pt", "www.autolux.pt", "www.ricardopecas.pt", "www.rparts.pt",
    "www.iberoparts.pt", "www.europarts.pt", "www.motorparts.pt", "www.repuestos.pt",
    "www.4rodas.pt", "www.mecanico.pt", "www.autocenter.pt", "www.autojardim.pt",
    "www.sidatauto.pt", "www.mecauto.pt", "www.lusoparts.pt", "www.autopartes.pt",
    # ES shops that ship to Portugal
    "www.todosrepuestos.com", "www.recambiosonline.es", "www.autorepuestos.es",
    "www.piezasauto.es", "www.repuestoscoches24.es", "www.recambioscoche.es",
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


def main() -> int:
    tried = B1 / "tried.csv"
    claims = []
    allowed = []
    with tried.open("a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        for host in HOSTS:
            base = "https://" + host
            v, first = verdict(base, "/")
            time.sleep(2.2)
            print(f"  {v:<12} {host}")
            w.writerow([host, base + "/", v, f"phase9 sweep | {first}",
                        datetime.now(timezone.utc).isoformat(timespec="seconds")])
            claims.append([host, "B1", v, "", "phase9 sweep"])
            if v == "allowed":
                allowed.append(host)
    with SHARED.open("a", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerows(claims)
    print(f"\nallowed: {allowed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
