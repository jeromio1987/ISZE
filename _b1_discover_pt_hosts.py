# -*- coding: utf-8 -*-
"""U26 work package B1 - Portuguese seller discovery (robots verdict only).

Phase 1. For each candidate host it asks the existing consent gate
(`04_tools/autodoc_scraper/check_scrape_consent.py --url <base> --path <path>`), which
fetches robots.txt ONLY, and records the verdict. No part page is fetched here.

Outputs:
  B1/tried.csv            every host attempted: host, url pattern, robots verdict, outcome
  _u26/B_HOSTS_CLAIMED.csv  shared claim ledger (header created if absent; B1 rows appended)

Append-only for the shared file: it never rewrites a row owned by another agent.
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


def find_root(start: Path) -> Path:
    """The worktree root = the folder that owns 04_tools/autodoc_scraper/check_scrape_consent.py."""
    for cand in [start, *start.parents]:
        if (cand / "04_tools" / "autodoc_scraper" / "check_scrape_consent.py").exists():
            return cand
    raise SystemExit("cannot locate worktree root (no check_scrape_consent.py above me)")


HERE = Path(__file__).resolve().parent
ISZE = find_root(HERE)
GATE = ISZE / "04_tools" / "autodoc_scraper" / "check_scrape_consent.py"
# B1 folder: either we sit in it, or we sit at the root and know the relative path.
B1 = HERE if HERE.name == "B1" else (
    ISZE / "01_data" / "90_INBOX" / "scrape_targets" / "_probe" / "_u26" / "B1")
PROBE_ROOT = B1.parent
SHARED = PROBE_ROOT / "B_HOSTS_CLAIMED.csv"

# (host base, path to test, why this host). robots.txt is fetched for the base only.
BATTERY: list[tuple[str, str, str]] = [
    ("https://www.soauto.pt", "/", "PT chain, own web shop"),
    ("https://www.norauto.pt", "/", "PT chain, parts web shop"),
    ("https://www.roady.pt", "/", "PT chain (Norauto group)"),
    ("https://www.feuvert.pt", "/", "PT chain"),
    ("https://www.b-parts.pt", "/", "PT used-parts marketplace"),
    ("https://www.pecasauto.pt", "/", "PT online parts shop"),
    ("https://www.autosil.pt", "/", "PT parts distributor"),
    ("https://www.sidat.pt", "/", "PT parts distributor"),
    ("https://www.jcparts.pt", "/", "PT online parts shop"),
    ("https://www.motocar.pt", "/", "PT online parts shop"),
    ("https://www.bomcar.pt", "/", "PT online parts shop"),
    ("https://www.pecasonline.pt", "/", "PT online parts shop"),
    ("https://www.ipecas.pt", "/", "PT online parts shop"),
    ("https://www.pecascamiao.pt", "/", "PT truck parts shop"),
    ("https://www.camiao.pt", "/", "PT truck parts shop"),
    ("https://www.endado.com", "/", "EU parts platform, ships PT, EUR"),
    ("https://www.autopartslogistic.com", "/", "ES parts platform, ships PT, EUR"),
    ("https://www.recambiosviaweb.com", "/", "ES parts platform, ships PT, EUR"),
    ("https://www.skruvat.com", "/", "EU parts platform, ships PT, EUR"),
    ("https://www.ersatzteile-24.com", "/", "DE parts platform, ships PT, EUR"),
    ("https://www.olx.pt", "/", "PT classifieds, parts category"),
    ("https://www.custojusto.pt", "/", "PT classifieds, parts category"),
    # Operators already recorded blocked/retired in CROSSREF_SOURCE_RECON_2026-10-01:
    # recorded here so B2 can see them taken; NOT fetched again.
    ("https://www.autodoc.pt", "/", "RETIRED Turnstile - recorded, not fetched"),
    ("https://www.mister-auto.pt", "/", "operator blocked in recon - recorded, not fetched"),
    ("https://www.oscaro.pt", "/", "RETIRED Turnstile - recorded, not fetched"),
    ("https://www.trodo.com", "/", "operator blocked in recon - recorded, not fetched"),
]

NO_RETRY_OPERATORS = {
    "https://www.autodoc.pt", "https://www.mister-auto.pt", "https://www.oscaro.pt",
    "https://www.trodo.com",
}


def robots_verdict(base: str, path: str) -> tuple[str, str]:
    """(robots_verdict, raw first line). allowed / blocked / unreachable."""
    try:
        p = subprocess.run([sys.executable, str(GATE), "--url", base, "--path", path],
                           capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        return "unreachable", "robots fetch timed out"
    lines = (p.stdout or "").strip().splitlines()
    first = lines[0] if lines else ""
    if p.returncode == 0:
        return "allowed", first
    if first.startswith("BLOCKED"):
        return "blocked", first
    return "unreachable", first or (p.stderr or "").strip()[:140]


def main() -> int:
    if not GATE.exists():
        raise SystemExit(f"consent gate not found at {GATE}")
    B1.mkdir(parents=True, exist_ok=True)
    SHARED.parent.mkdir(parents=True, exist_ok=True)
    if not SHARED.exists():
        with SHARED.open("w", encoding="utf-8", newline="") as fh:
            csv.writer(fh).writerow(
                ["host", "claimed_by", "robots_verdict", "page_shape", "outcome"])
        print(f"created {SHARED}")

    out = B1 / "tried.csv"
    new_rows = []
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["host", "url_pattern", "robots_verdict", "outcome", "checked_at"])
        for base, path, why in BATTERY:
            if base in NO_RETRY_OPERATORS:
                verdict, first = "not_retried", "operator already blocked/retired in recon"
            else:
                verdict, first = robots_verdict(base, path)
                time.sleep(2.2)
            host = base.split("//", 1)[-1]
            print(f"  {verdict:<12} {host:<32} {why}")
            w.writerow([host, base + path, verdict, f"{why} | {first}",
                        datetime.now(timezone.utc).isoformat(timespec="seconds")])
            new_rows.append([host, "B1", verdict, "", why])

    with SHARED.open("a", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerows(new_rows)
    print(f"\nappended {len(new_rows)} claim rows to {SHARED}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
