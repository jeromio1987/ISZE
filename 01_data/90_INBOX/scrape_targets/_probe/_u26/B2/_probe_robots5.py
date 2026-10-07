# -*- coding: utf-8 -*-
"""B2 batch 5: robots for PT Isuzu / truck-parts hosts."""
from __future__ import annotations
import csv, io, subprocess, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
CONSENT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\04_tools\autodoc_scraper\check_scrape_consent.py")
PN = "8982705240"
CAND = [
    ("imotors.pt", "https://www.imotors.pt", f"/?s={PN}"),
    ("loja.imotors.pt", "https://loja.imotors.pt", "/"),
    ("pecas.isuzu.pt", "https://pecas.isuzu.pt", "/"),
    ("autosueco.pt", "https://www.autosueco.pt", f"/?s={PN}"),
    ("auto-sueco.pt", "https://www.auto-sueco.pt", f"/?s={PN}"),
    ("pecasauto24.pt", "https://www.pecasauto24.pt", f"/?s={PN}"),
    ("apecas.pt", "https://www.apecas.pt", f"/?s={PN}"),
    ("aparts.pt", "https://www.aparts.pt", f"/?s={PN}"),
    ("autopecas-online.pt", "https://www.autopecas-online.pt", f"/?s={PN}"),
    ("partesauto.pt", "https://www.partesauto.pt", f"/?s={PN}"),
    ("recambios.pt", "https://www.recambios.pt", f"/?s={PN}"),
    ("autopecasbaratas.pt", "https://www.autopecasbaratas.pt", f"/?s={PN}"),
    ("pecasbaratas.pt", "https://www.pecasbaratas.pt", f"/?s={PN}"),
    ("auto-hub.pt", "https://www.auto-hub.pt", f"/?s={PN}"),
    ("meupecas.pt", "https://www.meupecas.pt", f"/?s={PN}"),
    ("pecas-express.pt", "https://www.pecas-express.pt", f"/?s={PN}"),
    ("autopecasexpress.pt", "https://www.autopecasexpress.pt", f"/?s={PN}"),
    ("portugalpecas.pt", "https://www.portugalpecas.pt", f"/?s={PN}"),
    ("expresspecas.pt", "https://www.expresspecas.pt", f"/?s={PN}"),
    ("lojapeças.pt", "https://www.lojadepecas.pt", f"/?s={PN}"),
    ("peçasonline24.pt", "https://www.pecasonline24.pt", f"/?s={PN}"),
    ("euromaster.pt", "https://www.euromaster.pt", f"/?s={PN}"),
    ("bosch-service.pt", "https://www.bosch-service.pt", "/"),
    ("carglass.pt", "https://www.carglass.pt", "/"),
    ("viparts.pt", "https://www.viparts.pt", f"/?s={PN}"),
    ("iveco-parts.pt", "https://www.iveco-parts.pt", "/"),
    ("truckparts-online.pt", "https://www.truckparts-online.pt", "/"),
    ("grupomota.pt", "https://www.grupomota.pt", "/"),
    ("salvadorcaetano.pt", "https://www.salvadorcaetano.pt", "/"),
    ("autosueco.pt2", "https://autosueco.pt", "/"),
]
def probe(base, path):
    p = subprocess.run([sys.executable, str(CONSENT), "--url", base, "--path", path], capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip().replace("\n", " | ")
rows = []
for host, base, path in CAND:
    rc, out = probe(base, path)
    verdict = "allowed" if rc == 0 else ("blocked" if "BLOCKED" in out else "unknown")
    print(f"{verdict:<8} {host:<24} {out[:80]}")
    rows.append({"host": host, "base": base, "path": path, "exit": rc, "verdict": verdict, "detail": out})
with (HERE / "_robots_probe_batch5.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["host","base","path","exit","verdict","detail"]); w.writeheader(); w.writerows(rows)
al = [r["host"] for r in rows if r["verdict"]=="allowed"]
print("\nALLOWED:", ", ".join(al) if al else "(none)")
