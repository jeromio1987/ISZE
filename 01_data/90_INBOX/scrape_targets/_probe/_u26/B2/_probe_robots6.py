# -*- coding: utf-8 -*-
"""B2 batch 6: robots for more PT-facing sellers (WP product search + marketplaces)."""
from __future__ import annotations
import csv, io, subprocess, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
CONSENT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\04_tools\autodoc_scraper\check_scrape_consent.py")
PN = "8982705240"
CAND = [
    ("turbopecas.pt[wp]", "https://www.turbopecas.pt", f"/?s={PN}&post_type=product"),
    ("truckparts.pt[wp]", "https://www.truckparts.pt", f"/?s={PN}&post_type=product"),
    ("autosueco.pt", "https://www.autosueco.pt", f"/?s={PN}&post_type=product"),
    ("lojadepecas.pt", "https://www.lojadepecas.pt", f"/?s={PN}&post_type=product"),
    ("euromaster.pt", "https://www.euromaster.pt", f"/?s={PN}&post_type=product"),
    ("pecauto.com[sitemap]", "https://www.pecauto.com", "/sitemap.xml"),
    ("pecauto.com[cat]", "https://www.pecauto.com", "/pesquisa"),
    ("rodasa.pt", "https://www.rodasa.pt", f"/?s={PN}"),
    ("grupoandres.pt", "https://www.grupoandres.pt", f"/?s={PN}"),
    ("andres.pt", "https://www.andres.pt", f"/?s={PN}"),
    ("recambiosviaweb.com", "https://www.recambiosviaweb.com", f"/?s={PN}"),
    ("endado.com", "https://www.endado.com", f"/pt/search?q={PN}"),
    ("aeromotors.pt", "https://www.aeromotors.pt", f"/search?q={PN}"),
    ("ovoko.pt", "https://ovoko.pt", f"/search?q={PN}"),
    ("rrr.lt", "https://rrr.lt", f"/en/search?q={PN}"),
    ("autodalys.lt", "https://autodalys.lt", f"/search?q={PN}"),
    ("partsouq.com", "https://partsouq.com", f"/en/search/all?q={PN}"),
    ("amayama.com", "https://www.amayama.com", f"/en/search?q={PN}"),
    ("gama4x4.pt", "https://www.gama4x4.pt", f"/?s={PN}"),
    ("4x4acessorios.pt", "https://www.4x4acessorios.pt", f"/?s={PN}"),
    ("todorreno.pt", "https://www.todorreno.pt", f"/?s={PN}"),
    ("todo-terreno.pt", "https://www.todo-terreno.pt", f"/?s={PN}"),
    ("pickup4x4.pt", "https://www.pickup4x4.pt", f"/?s={PN}"),
    ("acessoriosauto.pt", "https://www.acessoriosauto.pt", f"/?s={PN}"),
    ("autopecasdesconto.pt", "https://www.autopecasdesconto.pt", f"/?s={PN}"),
    ("pecasdesconto.pt", "https://www.pecasdesconto.pt", f"/?s={PN}"),
    ("autopecaspt.pt", "https://www.autopecaspt.pt", f"/?s={PN}"),
    ("centropecas.pt", "https://www.centropecas.pt", f"/?s={PN}"),
    ("pecasauto-online.pt", "https://www.pecasauto-online.pt", f"/?s={PN}"),
    ("autopecaslisboa.pt", "https://www.autopecaslisboa.pt", f"/?s={PN}"),
    ("lisboaparts.pt", "https://www.lisboaparts.pt", f"/?s={PN}"),
    ("portoparts.pt", "https://www.portoparts.pt", f"/?s={PN}"),
    ("algarvepecas.pt", "https://www.algarvepecas.pt", f"/?s={PN}"),
    ("madeira-partes.pt", "https://www.madeira-partes.pt", f"/?s={PN}"),
    ("acorespecas.pt", "https://www.acorespecas.pt", f"/?s={PN}"),
]
def probe(base, path):
    p = subprocess.run([sys.executable, str(CONSENT), "--url", base, "--path", path], capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip().replace("\n", " | ")
rows = []
for host, base, path in CAND:
    rc, out = probe(base, path)
    verdict = "allowed" if rc == 0 else ("blocked" if "BLOCKED" in out else "unknown")
    print(f"{verdict:<8} {host:<26} {out[:75]}")
    rows.append({"host": host, "base": base, "path": path, "exit": rc, "verdict": verdict, "detail": out})
with (HERE / "_robots_probe_batch6.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["host","base","path","exit","verdict","detail"]); w.writeheader(); w.writerows(rows)
al = [r["host"] for r in rows if r["verdict"]=="allowed"]
print("\nALLOWED:", ", ".join(al) if al else "(none)")
