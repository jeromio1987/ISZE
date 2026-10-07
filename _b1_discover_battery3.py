# -*- coding: utf-8 -*-
"""B1 phase 2c — third candidate battery: robots verdict per host (consent gate only)."""
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

BATTERY = [
    ("https://www.autoservice.pt", "/", "PT parts, maybe company only"),
    ("https://www.recambios.pt", "/", "PT/ES parts shop"),
    ("https://www.pecasauto-online.pt", "/", "PT online parts shop"),
    ("https://www.autopartsonline.pt", "/", "PT online parts shop"),
    ("https://www.pecas-online.pt", "/", "PT online parts shop"),
    ("https://www.epecas.pt", "/", "PT online parts shop"),
    ("https://www.sitiodaspecas.pt", "/", "PT online parts shop"),
    ("https://www.areal.pt", "/", "PT distributor"),
    ("https://www.sopedi.pt", "/", "PT distributor"),
    ("https://www.auto-material.pt", "/", "PT parts shop"),
    ("https://www.lojadoautopecas.pt", "/", "PT parts shop"),
    ("https://www.autopecasloja.pt", "/", "PT parts shop"),
    ("https://www.multiauto.pt", "/", "PT parts shop"),
    ("https://www.pneucity.pt", "/", "PT tyre+parts shop"),
    ("https://www.autopecas.pt", "/", "PT parts shop (no accent)"),
    ("https://www.autopecas-online.pt", "/", "PT parts shop"),
    ("https://www.pecasauto.pt", "/", "PT parts shop (retry)"),
    ("https://www.autosil.pt", "/", "PT distributor (already allowed)"),
    # EU platform shops that ship to Portugal
    ("https://alvadi.ee", "/", "EE TecDoc shop, ships PT, EUR"),
    ("https://www.autoparts24.eu", "/", "EU TecDoc shop"),
    ("https://www.autoteiledirekt.de", "/", "DE TecDoc shop"),
    ("https://www.pkwteile.de", "/", "DE TecDoc shop"),
    ("https://www.motointegrator.com", "/", "EU TecDoc shop"),
    ("https://www.winparts.nl", "/", "NL TecDoc shop"),
    ("https://www.recambiosviaweb.com", "/", "ES TecDoc shop (retry)"),
    ("https://www.ubricarmotos.com", "/", "ES motorcycle parts (control)"),
    ("https://www.todoparatucoche.com", "/", "ES parts shop"),
]


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
    claims = []
    with tried.open("a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        for base, path, why in BATTERY:
            v, first = verdict(base, path)
            time.sleep(2.2)
            host = base.split("//", 1)[-1]
            print(f"  {v:<12} {host:<34} {why}")
            w.writerow([host, base + path, v, f"{why} | {first}",
                        datetime.now(timezone.utc).isoformat(timespec="seconds")])
            claims.append([host, "B1", v, "", why])
    with SHARED.open("a", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerows(claims)
    print(f"\nappended {len(claims)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
