# -*- coding: utf-8 -*-
"""B2 discovery batch 2: robots.txt for more PT-facing hosts."""
from __future__ import annotations
import csv, io, subprocess, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
CONSENT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\04_tools\autodoc_scraper\check_scrape_consent.py")
CANDIDATES = [
    ("nors.pt", "https://nors.pt", "/"),
    ("autopecas24horas.pt", "https://www.autopecas24horas.pt", "/search?q=8982705240"),
    ("pecasauto24.pt", "https://www.pecasauto24.pt", "/search?q=8982705240"),
    ("autoindustrial.pt", "https://www.autoindustrial.pt", "/"),
    ("casadosrolamentos.pt", "https://www.casadosrolamentos.pt", "/"),
    ("rolamentos.pt", "https://www.rolamentos.pt", "/"),
    ("autofren.pt", "https://www.autofren.pt", "/"),
    ("grupoandres.pt", "https://www.grupoandres.pt", "/"),
    ("recambiosviaverde.pt", "https://www.recambiosviaverde.pt", "/"),
    ("daparto.pt", "https://www.daparto.pt", "/Teilenummernsuche/Teile/8982705240"),
    ("winparts.pt", "https://www.winparts.pt", "/zoekresultaten?zoek=8982705240"),
    ("autoteiledirekt.pt", "https://www.autoteiledirekt.pt", "/search?q=8982705240"),
    ("onlinecarparts.pt", "https://www.onlinecarparts.pt", "/search?q=8982705240"),
    ("buycarparts.pt", "https://www.buycarparts.pt", "/search?q=8982705240"),
    ("eurocarparts.pt", "https://www.eurocarparts.pt", "/search?q=8982705240"),
    ("peçasauto.pt", "https://www.xn--peasauto-w1a.pt", "/search?q=8982705240"),
    ("pecas-e-acessorios.pt", "https://www.pecaseacessorios.pt", "/"),
    ("auto-mecanica.pt", "https://www.automecanica.pt", "/"),
    ("santiagopecas.pt", "https://www.santiagopecas.pt", "/"),
    ("algarveparts.pt", "https://www.algarveparts.pt", "/"),
    ("madeirapecas.pt", "https://www.madeirapecas.pt", "/"),
    ("madeinportugalparts.pt", "https://www.madeinportugalparts.pt", "/"),
    ("isuzuparts.pt", "https://www.isuzuparts.pt", "/"),
    ("dmaxparts.pt", "https://www.dmaxparts.pt", "/"),
    ("pickupparts.pt", "https://www.pickupparts.pt", "/"),
    ("4x4parts.pt", "https://www.4x4parts.pt", "/"),
    ("todo-tt.pt", "https://www.todo-terreno.pt", "/"),
    ("autopecasgarcia.pt", "https://www.autopecasgarcia.pt", "/"),
    ("lousapecas.pt", "https://www.lousapecas.pt", "/"),
    ("valepartes.pt", "https://www.valepartes.pt", "/"),
    ("sermec.pt", "https://sermec.pt", "/"),
    ("cabauto.pt", "https://www.cabauto.pt", "/"),
    ("ecoparts.pt", "https://www.ecoparts.pt", "/"),
    ("retomapecas.pt", "https://www.retomapecas.pt", "/"),
    ("truckcenter.pt", "https://www.truckcenter.pt", "/"),
    ("camiaos.pt", "https://www.camiaos.pt", "/"),
    ("pesados.pt", "https://www.pesados.pt", "/"),
    ("autocamioes.pt", "https://www.autocamioes.pt", "/"),
    ("auto-camioes.pt", "https://www.auto-camioes.pt", "/"),
    ("transportesmagazine.pt", "https://www.transportesmagazine.pt", "/"),
]
def probe(base, path):
    p = subprocess.run([sys.executable, str(CONSENT), "--url", base, "--path", path], capture_output=True, text=True)
    out = (p.stdout or "").strip().replace("\n", " | ")
    return p.returncode, out
rows = []
for host, base, path in CANDIDATES:
    try:
        rc, out = probe(base, path)
    except Exception as e:
        rc, out = 1, f"ERR {e}"
    verdict = "allowed" if rc == 0 else ("blocked" if "BLOCKED" in out else "unknown")
    print(f"{verdict:<8} {host:<26} {out[:95]}")
    rows.append({"host": host, "base": base, "path": path, "exit": rc, "verdict": verdict, "detail": out})
with (HERE / "_robots_probe_batch2.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["host", "base", "path", "exit", "verdict", "detail"])
    w.writeheader(); w.writerows(rows)
allowed = [r["host"] for r in rows if r["verdict"] == "allowed"]
print("\nALLOWED:", ", ".join(allowed) if allowed else "(none)")
