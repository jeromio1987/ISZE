# -*- coding: utf-8 -*-
"""B2 batch 12: final PT / Isuzu-facing names."""
from __future__ import annotations
import csv, io, subprocess, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
CONSENT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\04_tools\autodoc_scraper\check_scrape_consent.py")
PN = "8982705240"
CAND = [
    ("ciberpecas.pt", "https://www.ciberpecas.pt", f"/?s={PN}"),
    ("masipesa.pt", "https://www.masipesa.pt", f"/?s={PN}"),
    ("motorkit.pt", "https://www.motorkit.pt", f"/?s={PN}"),
    ("autosmart.pt", "https://www.autosmart.pt", f"/?s={PN}"),
    ("rexbo.pt", "https://www.rexbo.pt", f"/search?q={PN}"),
    ("autodoc-store.pt", "https://www.autodoc-store.pt", f"/search?q={PN}"),
    ("pecasautoexpresso.pt", "https://www.pecasautoexpresso.pt", f"/?s={PN}"),
    ("expressoauto.pt", "https://www.expressoauto.pt", f"/?s={PN}"),
    ("autoexpresso.pt", "https://www.autoexpresso.pt", f"/?s={PN}"),
    ("turbodiesel.pt", "https://www.turbodiesel.pt", f"/?s={PN}"),
    ("dieselparts.pt", "https://www.dieselparts.pt", f"/?s={PN}"),
    ("injetores.pt", "https://www.injetores.pt", f"/?s={PN}"),
    ("bombas.pt", "https://www.bombas.pt", f"/?s={PN}"),
    ("turbos.pt", "https://www.turbos.pt", f"/?s={PN}"),
    ("escape.pt", "https://www.escape.pt", f"/?s={PN}"),
    ("embreagem.pt", "https://www.embreagem.pt", f"/?s={PN}"),
    ("amortecedores.pt", "https://www.amortecedores.pt", f"/?s={PN}"),
    ("radiadores.pt", "https://www.radiadores.pt", f"/?s={PN}"),
    ("alternadores.pt", "https://www.alternadores.pt", f"/?s={PN}"),
    ("baterias.pt", "https://www.baterias.pt", f"/?s={PN}"),
    ("isuzu-parts.pt", "https://www.isuzu-parts.pt", f"/?s={PN}"),
    ("isuzupart.pt", "https://www.isuzupart.pt", f"/?s={PN}"),
    ("isuzu-dmax.pt", "https://www.isuzu-dmax.pt", f"/?s={PN}"),
    ("dmax.pt", "https://www.dmax.pt", f"/?s={PN}"),
    ("dmaz.pt", "https://www.dmaz.pt", f"/?s={PN}"),
    ("isuzuservice.pt", "https://www.isuzuservice.pt", f"/?s={PN}"),
    ("isuzuportugal.com", "https://www.isuzuportugal.com", f"/?s={PN}"),
    ("imotorspecas.pt", "https://www.imotorspecas.pt", f"/?s={PN}"),
    ("imotors.pt2", "https://imotors.pt", f"/?s={PN}"),
    ("isuzu.pt2", "https://isuzu.pt", f"/?s={PN}"),
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
with (HERE / "_robots_probe_batch12.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["host","base","path","exit","verdict","detail"]); w.writeheader(); w.writerows(rows)
al = [r["host"] for r in rows if r["verdict"]=="allowed"]
print("\nALLOWED:", ", ".join(al) if al else "(none)")
