# -*- coding: utf-8 -*-
"""B2 batch 10: PT pickup/4x4/truck specialist shops + remaining ES groups."""
from __future__ import annotations
import csv, io, subprocess, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
CONSENT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\04_tools\autodoc_scraper\check_scrape_consent.py")
PN = "8982705240"
CAND = [
    ("dmaxportugal.pt", "https://www.dmaxportugal.pt", f"/?s={PN}"),
    ("isuzupecas.pt", "https://www.isuzupecas.pt", f"/?s={PN}"),
    ("pickupsolutions.pt", "https://www.pickupsolutions.pt", f"/?s={PN}"),
    ("pickupstore.pt", "https://www.pickupstore.pt", f"/?s={PN}"),
    ("acessorios4x4.pt", "https://www.acessorios4x4.pt", f"/?s={PN}"),
    ("loja4x4.pt", "https://www.loja4x4.pt", f"/?s={PN}"),
    ("norte4x4.pt", "https://www.norte4x4.pt", f"/?s={PN}"),
    ("terrano4x4.pt", "https://www.terrano4x4.pt", f"/?s={PN}"),
    ("offroadparts.pt", "https://www.offroadparts.pt", f"/?s={PN}"),
    ("autopecasdofoco.pt", "https://www.autopecasdofoco.pt", f"/?s={PN}"),
    ("batistapecas.pt", "https://www.batistapecas.pt", f"/?s={PN}"),
    ("fonsecapecas.pt", "https://www.fonsecapecas.pt", f"/?s={PN}"),
    ("soraipecas.pt", "https://www.soraipecas.pt", f"/?s={PN}"),
    ("coimbraparts.pt", "https://www.coimbraparts.pt", f"/?s={PN}"),
    ("aveiropecas.pt", "https://www.aveiropecas.pt", f"/?s={PN}"),
    ("bragapecas.pt", "https://www.bragapecas.pt", f"/?s={PN}"),
    ("leiriapecas.pt", "https://www.leiriapecas.pt", f"/?s={PN}"),
    ("faroauto.pt", "https://www.faroauto.pt", f"/?s={PN}"),
    ("setubalpecas.pt", "https://www.setubalpecas.pt", f"/?s={PN}"),
    ("lisboapecas.pt", "https://www.lisboapecas.pt", f"/?s={PN}"),
    # ES / EU with .pt reach, truck specialists
    ("recambioscoche.es", "https://www.recambioscoche.es", f"/buscar?q={PN}"),
    ("repuestoscoches24.es", "https://www.repuestoscoches24.es", f"/search?q={PN}"),
    ("todosrepuestos.es", "https://www.todosrepuestos.es", f"/search?q={PN}"),
    ("autorepuestos.es", "https://www.autorepuestos.es", f"/search?q={PN}"),
    ("piezasauto.es", "https://www.piezasauto.es", f"/search?q={PN}"),
    ("recambiosviaweb.es", "https://www.recambiosviaweb.es", f"/search?q={PN}"),
    ("carservice.es", "https://www.carservice.es", f"/?s={PN}"),
    ("viamobil.es", "https://www.viamobil.es", f"/?s={PN}"),
    ("truckparts.es", "https://www.truckparts.es", f"/?s={PN}"),
    ("camionesrepuestos.es", "https://www.camionesrepuestos.es", f"/?s={PN}"),
]
def probe(base, path):
    p = subprocess.run([sys.executable, str(CONSENT), "--url", base, "--path", path], capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip().replace("\n", " | ")
rows = []
for host, base, path in CAND:
    rc, out = probe(base, path)
    verdict = "allowed" if rc == 0 else ("blocked" if "BLOCKED" in out else "unknown")
    print(f"{verdict:<8} {host:<24} {out[:70]}")
    rows.append({"host": host, "base": base, "path": path, "exit": rc, "verdict": verdict, "detail": out})
with (HERE / "_robots_probe_batch10.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["host","base","path","exit","verdict","detail"]); w.writeheader(); w.writerows(rows)
al = [r["host"] for r in rows if r["verdict"]=="allowed"]
print("\nALLOWED:", ", ".join(al) if al else "(none)")
