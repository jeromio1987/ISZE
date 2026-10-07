# -*- coding: utf-8 -*-
"""B2 discovery: test robots.txt of candidate Portuguese / PT-facing hosts."""
from __future__ import annotations
import csv, io, subprocess, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
CONSENT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\04_tools\autodoc_scraper\check_scrape_consent.py")

CANDIDATES = [
    ("autopecasonline24.pt", "https://www.autopecasonline24.pt", "/search?query=8982705240"),
    ("mister-auto.pt", "https://www.mister-auto.pt", "/search?q=8982705240"),
    ("b-parts.com", "https://www.b-parts.com", "/pt/search?q=8982705240"),
    ("pecasauto.pt", "https://www.pecasauto.pt", "/pesquisa?q=8982705240"),
    ("autopecas.pt", "https://www.autopecas.pt", "/search?q=8982705240"),
    ("tudoautopecas.pt", "https://www.tudoautopecas.pt", "/search?q=8982705240"),
    ("maispecas.pt", "https://www.maispecas.pt", "/search?q=8982705240"),
    ("norauto.pt", "https://www.norauto.pt", "/search?q=8982705240"),
    ("roady.pt", "https://www.roady.pt", "/search?q=8982705240"),
    ("midas.pt", "https://www.midas.pt", "/search?q=8982705240"),
    ("feuvert.pt", "https://www.feuvert.pt", "/search?q=8982705240"),
    ("isuzu.pt", "https://www.isuzu.pt", "/"),
    ("peças-online.pt", "https://www.xn--peas-online-zhb.pt", "/"),
    ("pecasonline.pt", "https://www.pecasonline.pt", "/search?q=8982705240"),
    ("autoparts.pt", "https://www.autoparts.pt", "/search?q=8982705240"),
    ("rexauto.pt", "https://www.rexauto.pt", "/"),
    ("carmona.pt", "https://www.carmona.pt", "/"),
    ("grupoautosilva.pt", "https://www.grupoautosilva.pt", "/"),
    ("spareto.com", "https://spareto.com", "/oe/8982705240"),
    ("cardoso.pt", "https://www.cardoso.pt", "/"),
    ("camial.pt", "https://www.camial.pt", "/"),
    ("truckparts.pt", "https://www.truckparts.pt", "/"),
    ("autotratores.pt", "https://www.autotratores.pt", "/"),
    ("pecascamiao.pt", "https://www.pecascamiao.pt", "/"),
    ("autopeças.pt", "https://www.xn--autopeas-8za.pt", "/"),
    ("sotecnica.pt", "https://www.sotecnica.pt", "/"),
    ("isuzuportugal.pt", "https://www.isuzuportugal.pt", "/"),
    ("nors.pt", "https://www.nors.pt", "/"),
    ("ascendum.pt", "https://www.ascendum.pt", "/"),
    ("sadive.pt", "https://www.sadive.pt", "/"),
    ("sermec.pt", "https://www.sermec.pt", "/"),
    ("auto365.pt", "https://www.auto365.pt", "/"),
    ("carlogi.pt", "https://www.carlogi.pt", "/search?q=8982705240"),
    ("autoze.pt", "https://www.autoze.pt", "/"),
    ("interpecas.pt", "https://www.interpecas.pt", "/"),
    ("pecauto.com", "https://www.pecauto.com", "/"),
    ("mafra.pt", "https://www.mafra.pt", "/"),
    ("autosapopecas.pt", "https://www.autosapopecas.pt", "/"),
    ("turbopecas.pt", "https://www.turbopecas.pt", "/"),
]

def probe(base, path):
    p = subprocess.run([sys.executable, str(CONSENT), "--url", base, "--path", path],
                       capture_output=True, text=True)
    out = (p.stdout or "").strip().replace("\n", " | ")
    return p.returncode, out

rows = []
for host, base, path in CANDIDATES:
    rc, out = probe(base, path)
    verdict = "allowed" if rc == 0 else ("blocked" if "BLOCKED" in out else "unknown")
    print(f"{verdict:<8} {host:<26} {out[:100]}")
    rows.append({"host": host, "base": base, "path": path, "exit": rc, "verdict": verdict, "detail": out})

with (HERE / "_robots_probe.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["host", "base", "path", "exit", "verdict", "detail"])
    w.writeheader(); w.writerows(rows)

allowed = [r["host"] for r in rows if r["verdict"] == "allowed"]
print("\nALLOWED:", ", ".join(allowed) if allowed else "(none)")
