# -*- coding: utf-8 -*-
"""B2 batch 7: more PT sellers + pan-EU shops that ship to Portugal."""
from __future__ import annotations
import csv, io, subprocess, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
CONSENT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\04_tools\autodoc_scraper\check_scrape_consent.py")
PN = "8982705240"
CAND = [
    # PT sellers, more names
    ("domauto.pt", "https://www.domauto.pt", f"/?s={PN}"),
    ("auto-online.pt", "https://www.auto-online.pt", f"/?s={PN}"),
    ("partsonline.pt", "https://www.partsonline.pt", f"/?s={PN}"),
    ("pecas-pt.com", "https://www.pecas-pt.com", f"/?s={PN}"),
    ("autopecasbeira.pt", "https://www.autopecasbeira.pt", f"/?s={PN}"),
    ("perfilauto.pt", "https://www.perfilauto.pt", f"/?s={PN}"),
    ("autotrator.pt", "https://www.autotrator.pt", f"/?s={PN}"),
    ("soscar.pt", "https://www.soscar.pt", f"/?s={PN}"),
    ("pecasusadas.pt", "https://www.pecasusadas.pt", f"/?s={PN}"),
    ("sucatas.pt", "https://www.sucatas.pt", f"/?s={PN}"),
    ("autousados.pt", "https://www.autousados.pt", f"/?s={PN}"),
    ("pecas-auto.pt", "https://www.pecas-auto.pt", f"/?s={PN}"),
    ("carparts.pt", "https://www.carparts.pt", f"/?s={PN}"),
    ("autopecas24.pt", "https://www.autopecas24.pt", f"/?s={PN}"),
    ("gppecas.pt", "https://www.gppecas.pt", f"/?s={PN}"),
    ("pecasdecamiao.pt", "https://www.pecasdecamiao.pt", f"/?s={PN}"),
    ("camioespartes.pt", "https://www.camioespartes.pt", f"/?s={PN}"),
    ("truckparts.pt[shop]", "https://www.truckparts.pt", "/loja/"),
    ("truckparts.pt[cat]", "https://www.truckparts.pt", "/produtos/"),
    # ES / EU groups with .pt or ship-PT shops
    ("recambiosviaweb.pt", "https://www.recambiosviaweb.pt", f"/?s={PN}"),
    ("rodasa.pt", "https://rodasa.pt", f"/?s={PN}"),
    ("grupoandres.com", "https://www.grupoandres.com", f"/?s={PN}"),
    ("andres.es", "https://www.andres.es", f"/?s={PN}"),
    ("alcampo.es", "https://www.alcampo.es", "/"),
    ("alvadi.ee", "https://alvadi.ee", f"/en/spare-parts/search?q={PN}"),
    ("alvadi.lt", "https://alvadi.lt", f"/en/spare-parts/search?q={PN}"),
    ("cars245.com", "https://cars245.com", f"/en/search?q={PN}"),
    ("autoosad.ee", "https://www.autoosad.ee", f"/search?q={PN}"),
    ("topautoosad.ee", "https://www.topautoosad.ee", f"/search?q={PN}"),
    ("aeromotors.pl", "https://www.aeromotors.pl", f"/search?q={PN}"),
    ("skruvat.pt", "https://www.skruvat.pt", f"/search?q={PN}"),
    ("motointegrator.pt", "https://www.motointegrator.pt", f"/search?q={PN}"),
    ("micksgarage.com", "https://www.micksgarage.com", f"/search?q={PN}"),
    ("carpartsdirect.pt", "https://www.carpartsdirect.pt", f"/?s={PN}"),
    ("autopeças.pt", "https://www.autopecas.pt", f"/?s={PN}"),
    ("truckpartseurope.pt", "https://www.truckpartseurope.pt", f"/?s={PN}"),
    ("europarts.pt", "https://www.europarts.pt", f"/?s={PN}"),
    ("spareparts.pt", "https://www.spareparts.pt", f"/?s={PN}"),
    ("autopecem.pt", "https://www.autopecem.pt", f"/?s={PN}"),
]
def probe(base, path):
    p = subprocess.run([sys.executable, str(CONSENT), "--url", base, "--path", path], capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip().replace("\n", " | ")
rows = []
for host, base, path in CAND:
    rc, out = probe(base, path)
    verdict = "allowed" if rc == 0 else ("blocked" if "BLOCKED" in out else "unknown")
    print(f"{verdict:<8} {host:<24} {out[:72]}")
    rows.append({"host": host, "base": base, "path": path, "exit": rc, "verdict": verdict, "detail": out})
with (HERE / "_robots_probe_batch7.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["host","base","path","exit","verdict","detail"]); w.writeheader(); w.writerows(rows)
al = [r["host"] for r in rows if r["verdict"]=="allowed"]
print("\nALLOWED:", ", ".join(al) if al else "(none)")
