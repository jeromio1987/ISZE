# -*- coding: utf-8 -*-
"""B2 discovery batch 4: robots for the real search endpoints found on homepages."""
from __future__ import annotations
import csv, io, subprocess, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
CONSENT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\04_tools\autodoc_scraper\check_scrape_consent.py")
CANDIDATES = [
    ("truckparts.pt", "https://www.truckparts.pt", "/?s=8982705240"),
    ("sotecnica.pt", "https://www.sotecnica.pt", "/?s=8982705240"),
    ("turbopecas.pt", "https://www.turbopecas.pt", "/?s=8982705240"),
    ("turbopecas.datapremium.pt", "https://turbopecas.datapremium.pt", "/"),
    ("b-parts.com", "https://www.b-parts.com", "/pt/auto-parts/search?q=8982705240"),
    ("b-parts.com", "https://www.b-parts.com", "/pt/auto-parts/search?part_number=8982705240"),
    ("roady.pt", "https://www.roady.pt", "/?s=8982705240"),
    ("midas.pt", "https://www.midas.pt", "/?s=8982705240"),
    ("isuzu.pt", "https://www.isuzu.pt", "/?s=8982705240"),
    ("ascendum.pt", "https://www.ascendum.pt", "/?s=8982705240"),
    ("datapremium.pt", "https://www.datapremium.pt", "/"),
]
def probe(base, path):
    p = subprocess.run([sys.executable, str(CONSENT), "--url", base, "--path", path], capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip().replace("\n", " | ")
rows = []
for host, base, path in CANDIDATES:
    rc, out = probe(base, path)
    verdict = "allowed" if rc == 0 else ("blocked" if "BLOCKED" in out else "unknown")
    print(f"{verdict:<8} {host:<26} {path:<48} {out[:70]}")
    rows.append({"host": host, "base": base, "path": path, "exit": rc, "verdict": verdict, "detail": out})
with (HERE / "_robots_probe_batch4.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["host","base","path","exit","verdict","detail"]); w.writeheader(); w.writerows(rows)
