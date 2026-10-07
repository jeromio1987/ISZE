# -*- coding: utf-8 -*-
"""B1 phase 2d — fourth candidate battery (robots verdict per host)."""
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
    ("https://www.autopecas24h.pt", "/", "PT online parts shop"),
    ("https://www.pecasauto24h.pt", "/", "PT online parts shop"),
    ("https://www.sitioauto.pt", "/", "PT online parts shop"),
    ("https://www.autopecasbaratas.pt", "/", "PT online parts shop"),
    ("https://www.pecas-auto.pt", "/", "PT online parts shop"),
    ("https://www.lojadepecasauto.pt", "/", "PT online parts shop"),
    ("https://www.autopecasportugal.pt", "/", "PT online parts shop"),
    ("https://www.auto-jardim.pt", "/", "PT online parts shop"),
    ("https://www.ferrariauto.pt", "/", "PT parts"),
    ("https://www.mcardoso.pt", "/", "PT parts"),
    ("https://www.valecar.pt", "/", "PT parts"),
    ("https://www.nortecar.pt", "/", "PT parts"),
    ("https://www.topauto.pt", "/", "PT parts"),
    ("https://www.lojauto.pt", "/", "PT parts"),
    ("https://www.pecasdeauto.pt", "/", "PT parts"),
    ("https://www.pecaauto.pt", "/", "PT parts"),
    ("https://www.mpecas.pt", "/", "PT parts"),
    ("https://www.autopecas24.pt", "/", "PT parts (retry)"),
    ("https://www.autopecas-online.com", "/", "PT/ES parts"),
    ("https://www.autoparts24.pt", "/", "EU platform PT storefront"),
    ("https://www.piecesauto24.pt", "/", "EU platform PT storefront"),
    ("https://www.autoteile24.pt", "/", "EU platform PT storefront"),
    ("https://www.piecesauto24.com", "/", "EU platform"),
    ("https://www.piecesdiscount24.pt", "/", "EU platform PT storefront"),
    ("https://www.oscaro.pt", "/", "operator (recon) - recorded"),
    # already allowed; re-verify with one clean verdict
    ("https://www.autopartslogistic.com", "/", "ES platform, allowed (deep-probe next)"),
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
            print(f"  {v:<12} {host:<36} {why}")
            w.writerow([host, base + path, v, f"{why} | {first}",
                        datetime.now(timezone.utc).isoformat(timespec="seconds")])
            claims.append([host, "B1", v, "", why])
    with SHARED.open("a", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerows(claims)
    print(f"\nappended {len(claims)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
