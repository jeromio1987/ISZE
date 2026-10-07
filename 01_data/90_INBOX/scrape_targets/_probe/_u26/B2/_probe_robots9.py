# -*- coding: utf-8 -*-
"""B2 batch 9: europart product-search + a few remaining shapes."""
from __future__ import annotations
import csv, io, subprocess, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
CONSENT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\04_tools\autodoc_scraper\check_scrape_consent.py")
PN = "8982705240"
CAND = [
    ("europart.net", "https://www.europart.net", f"/assortment/product-search/filter?query={PN}"),
    ("europart.net", "https://www.europart.net", f"/assortment/product-search/filter?search={PN}"),
    ("europart.net", "https://www.europart.net", "/assortment/product-search/"),
    ("europart.pt", "https://www.europart.pt", "/assortment/product-search/"),
    ("europart.es", "https://www.europart.es", "/assortment/product-search/"),
    ("turbopecas.pt", "https://www.turbopecas.pt", "/?s=ADBP420136&post_type=product"),
    ("turbopecas.pt", "https://www.turbopecas.pt", "/?s=BOSCH&post_type=product"),
    ("turbopecas.pt", "https://www.turbopecas.pt", "/?s=FEB%C3%89&post_type=product"),
]
def probe(base, path):
    p = subprocess.run([sys.executable, str(CONSENT), "--url", base, "--path", path], capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip().replace("\n", " | ")
rows = []
for host, base, path in CAND:
    rc, out = probe(base, path)
    verdict = "allowed" if rc == 0 else ("blocked" if "BLOCKED" in out else "unknown")
    print(f"{verdict:<8} {host:<18} {path[:46]:<48} {out[:60]}")
    rows.append({"host": host, "base": base, "path": path, "exit": rc, "verdict": verdict, "detail": out})
with (HERE / "_robots_probe_batch9.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["host","base","path","exit","verdict","detail"]); w.writeheader(); w.writerows(rows)
