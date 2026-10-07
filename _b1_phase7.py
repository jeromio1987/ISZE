# -*- coding: utf-8 -*-
"""B1 phase 7 — inspect the two live leads + a final targeted host battery.

(a) nortecar.pt: its "sitemap.xml" had 241 KB but 0 <loc> — see what it actually is.
(b) pneubeato.com: its Isuzu D-Max category — does it list products with prices and part numbers?
(c) a final robots battery of Isuzu-specific and remaining PT shop guesses.
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

BATTERY = [
    ("https://www.isuzu.pt", "/", "Isuzu PT importer"),
    ("https://www.isuzupecas.pt", "/", "PT Isuzu parts shop guess"),
    ("https://www.pecasisuzu.pt", "/", "PT Isuzu parts shop guess"),
    ("https://www.isuzupartes.pt", "/", "PT Isuzu parts shop guess"),
    ("https://www.autoimpor.pt", "/", "PT parts shop"),
    ("https://www.acp.pt", "/", "PT parts"),
    ("https://www.autoparts.pt", "/", "PT parts (retry)"),
    ("https://www.pecasauto.com.pt", "/", "PT parts"),
    ("https://www.pecasonline.pt", "/", "PT parts (retry)"),
    ("https://www.carparts.pt", "/", "PT parts (retry)"),
    ("https://www.autopecas.online", "/", "PT parts"),
    ("https://www.pecasauto.pt", "/", "PT parts (retry)"),
    ("https://www.auto-parts.pt", "/", "PT parts (retry)"),
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
    f = PoliteFetcher()
    print("### nortecar.pt sitemap bytes")
    h = f.get("https://www.nortecar.pt/sitemap.xml")
    if h:
        print(f"  {len(h):,}B  head: {re.sub(chr(10), ' ', h[:300])!r}")
        print(f"  <loc> count: {h.lower().count('<loc>')}  <url> count: {h.lower().count('<url>')}")

    print("\n### pneubeato.com Isuzu D-Max category")
    for u in ["https://www.pneubeato.com/travoes-ebc/isuzu/d-max",
              "https://www.pneubeato.com/travoes-ebc/isuzu"]:
        try:
            h = f.get(u)
        except ConsentRefused as e:
            print(f"  REFUSED {u} ({e})")
            continue
        if not h:
            print(f"  err/non-200 {u}")
            continue
        prices = re.findall(r"\d{1,4}[.,]\d{2}\s?€", h)
        print(f"  {u}\n    {len(h):,}B prices={len(prices)}{prices[:6]} "
              f"Isuzu OEs? dashed={len(re.findall(r'8-9\d{4}-\d{3}-\d', h))}")

    print("\n### final robots battery")
    claims = []
    tried = B1 / "tried.csv"
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
    print(f"\nfetch stats: {f.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
