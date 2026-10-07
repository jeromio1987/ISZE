# -*- coding: utf-8 -*-
"""B2 discovery batch 3: robots.txt for the ALLOWED hosts, on their SEARCH paths."""
from __future__ import annotations
import csv, io, subprocess, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
CONSENT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\04_tools\autodoc_scraper\check_scrape_consent.py")
# Search-path shapes for each allowed host
CANDIDATES = [
    ("b-parts.com", "https://www.b-parts.com", "/pt/search?q=8982705240"),
    ("b-parts.com", "https://www.b-parts.com", "/pt/pecas-auto/search?q=8982705240"),
    ("truckparts.pt", "https://www.truckparts.pt", "/pesquisa?q=8982705240"),
    ("truckparts.pt", "https://www.truckparts.pt", "/search?q=8982705240"),
    ("truckparts.pt", "https://www.truckparts.pt", "/loja/pesquisa?q=8982705240"),
    ("sotecnica.pt", "https://www.sotecnica.pt", "/search?q=8982705240"),
    ("sotecnica.pt", "https://www.sotecnica.pt", "/pesquisa?q=8982705240"),
    ("ascendum.pt", "https://www.ascendum.pt", "/search?q=8982705240"),
    ("pecauto.com", "https://www.pecauto.com", "/search?q=8982705240"),
    ("pecauto.com", "https://www.pecauto.com", "/pesquisa?q=8982705240"),
    ("turbopecas.pt", "https://www.turbopecas.pt", "/search?q=8982705240"),
    ("turbopecas.pt", "https://www.turbopecas.pt", "/pesquisa?q=8982705240"),
    ("auto-mecanica.pt", "https://www.auto-mecanica.pt", "/search?q=8982705240"),
    ("auto-mecanica.pt", "https://www.auto-mecanica.pt", "/pesquisa?q=8982705240"),
    ("roady.pt", "https://www.roady.pt", "/search?q=8982705240"),
    ("midas.pt", "https://www.midas.pt", "/search?q=8982705240"),
    ("feuvert.pt", "https://www.feuvert.pt", "/search?q=8982705240"),
    ("isuzu.pt", "https://www.isuzu.pt", "/search?q=8982705240"),
]
def probe(base, path):
    p = subprocess.run([sys.executable, str(CONSENT), "--url", base, "--path", path], capture_output=True, text=True)
    out = (p.stdout or "").strip().replace("\n", " | ")
    return p.returncode, out
rows = []
for host, base, path in CANDIDATES:
    rc, out = probe(base, path)
    verdict = "allowed" if rc == 0 else ("blocked" if "BLOCKED" in out else "unknown")
    print(f"{verdict:<8} {host:<20} {path:<42} {out[:80]}")
    rows.append({"host": host, "base": base, "path": path, "exit": rc, "verdict": verdict, "detail": out})
with (HERE / "_robots_probe_batch3.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["host","base","path","exit","verdict","detail"])
    w.writeheader(); w.writerows(rows)
