# -*- coding: utf-8 -*-
"""B2 batch 11: last PT truck/parts specialist names."""
from __future__ import annotations
import csv, io, subprocess, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
CONSENT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\04_tools\autodoc_scraper\check_scrape_consent.py")
PN = "8982705240"
CAND = [
    ("camiper.pt", "https://www.camiper.pt", f"/?s={PN}"),
    ("rodopecas.pt", "https://www.rodopecas.pt", f"/?s={PN}"),
    ("frial.pt", "https://www.frial.pt", f"/?s={PN}"),
    ("autoluz.pt", "https://www.autoluz.pt", f"/?s={PN}"),
    ("alianca.pt", "https://www.alianca.pt", f"/?s={PN}"),
    ("socarparts.pt", "https://www.socarparts.pt", f"/?s={PN}"),
    ("interfrenos.pt", "https://www.interfrenos.pt", f"/?s={PN}"),
    ("bragauto.pt", "https://www.bragauto.pt", f"/?s={PN}"),
    ("autosapopecas.pt", "https://autosapopecas.pt", f"/?s={PN}"),
    ("tedex.pt", "https://www.tedex.pt", f"/?s={PN}"),
    ("mcr.pt", "https://www.mcr.pt", f"/?s={PN}"),
    ("grupomc.pt", "https://www.grupomc.pt", f"/?s={PN}"),
    ("sival.pt", "https://www.sival.pt", f"/?s={PN}"),
    ("civic.pt", "https://www.civic.pt", f"/?s={PN}"),
    ("cobat.pt", "https://www.cobat.pt", f"/?s={PN}"),
    ("josedecastro.pt", "https://www.josedecastro.pt", f"/?s={PN}"),
    ("luisaguiar.pt", "https://www.luisaguiar.pt", f"/?s={PN}"),
    ("autobragafirme.pt", "https://www.autobragafirme.pt", f"/?s={PN}"),
    ("auto-pecas-norte.pt", "https://www.auto-pecas-norte.pt", f"/?s={PN}"),
    ("pecasnorte.pt", "https://www.pecasnorte.pt", f"/?s={PN}"),
    ("sulpecas.pt", "https://www.sulpecas.pt", f"/?s={PN}"),
    ("nortpecas.pt", "https://www.nortpecas.pt", f"/?s={PN}"),
    ("centroauto.pt", "https://www.centroauto.pt", f"/?s={PN}"),
    ("auto-jardim.pt", "https://www.auto-jardim.pt", f"/?s={PN}"),
    ("autojardim.pt", "https://www.autojardim.pt", f"/?s={PN}"),
    ("pecasequipamentos.pt", "https://www.pecasequipamentos.pt", f"/?s={PN}"),
    ("truckpartsdiffusion.pt", "https://www.truckpartsdiffusion.pt", f"/?s={PN}"),
    ("tpd.pt", "https://www.tpd.pt", f"/?s={PN}"),
    ("mecanotruck.pt", "https://www.mecanotruck.pt", f"/?s={PN}"),
    ("truckmecanica.pt", "https://www.truckmecanica.pt", f"/?s={PN}"),
]
def probe(base, path):
    p = subprocess.run([sys.executable, str(CONSENT), "--url", base, "--path", path], capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip().replace("\n", " | ")
rows = []
for host, base, path in CAND:
    rc, out = probe(base, path)
    verdict = "allowed" if rc == 0 else ("blocked" if "BLOCKED" in out else "unknown")
    if verdict == "allowed":
        print(f"{verdict:<8} {host:<24} {out[:70]}")
    rows.append({"host": host, "base": base, "path": path, "exit": rc, "verdict": verdict, "detail": out})
with (HERE / "_robots_probe_batch11.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["host","base","path","exit","verdict","detail"]); w.writeheader(); w.writerows(rows)
al = [r["host"] for r in rows if r["verdict"]=="allowed"]
print("\nALLOWED:", ", ".join(al) if al else "(none)")
