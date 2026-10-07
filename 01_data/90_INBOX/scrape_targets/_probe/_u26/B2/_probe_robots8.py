# -*- coding: utf-8 -*-
"""B2 batch 8: pan-EU shops with PT storefronts + truckshops."""
from __future__ import annotations
import csv, io, subprocess, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
CONSENT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\04_tools\autodoc_scraper\check_scrape_consent.py")
PN = "8982705240"
CAND = [
    ("motordoctor.pt", "https://www.motordoctor.pt", f"/search?q={PN}"),
    ("motordoctor.pt2", "https://motordoctor.pt", f"/search?q={PN}"),
    ("autoersatzteile.pt", "https://www.autoersatzteile.pt", f"/search?q={PN}"),
    ("autoteile24.pt", "https://www.autoteile24.pt", f"/search?q={PN}"),
    ("autodoc24.pt", "https://www.autodoc24.pt", f"/search?q={PN}"),
    ("ersatzteileshop.pt", "https://www.ersatzteileshop.pt", f"/search?q={PN}"),
    ("teilediscount.pt", "https://www.teilediscount.pt", f"/search?q={PN}"),
    ("autoteile-preiswert.pt", "https://www.autoteile-preiswert.pt", f"/search?q={PN}"),
    ("partsbit.pt", "https://www.partsbit.pt", f"/search?q={PN}"),
    ("autoteiledirekt.pt", "https://www.autoteiledirekt.pt", f"/search?q={PN}"),
    ("autoteile-express.pt", "https://www.autoteile-express.pt", f"/search?q={PN}"),
    ("ersatzteile-24.com", "https://www.ersatzteile-24.com", f"/search?q={PN}"),
    ("autopartslogistic.com", "https://www.autopartslogistic.com", f"/search?q={PN}"),
    ("autopartslogistic.com2", "https://autopartslogistic.com", f"/search?q={PN}"),
    ("motointegrator.com", "https://www.motointegrator.com", f"/search?q={PN}"),
    ("rtgparts.eu", "https://www.rtgparts.eu", f"/search?q={PN}"),
    ("autotruckparts.eu", "https://www.autotruckparts.eu", f"/search?q={PN}"),
    ("truckparts24.eu", "https://www.truckparts24.eu", f"/search?q={PN}"),
    ("truckpartsonline.eu", "https://www.truckpartsonline.eu", f"/search?q={PN}"),
    ("eurotruckparts.eu", "https://www.eurotruckparts.eu", f"/search?q={PN}"),
    ("kamazparts.eu", "https://www.kamazparts.eu", f"/search?q={PN}"),
    ("trucktec.eu", "https://www.trucktec.eu", f"/search?q={PN}"),
    ("sampa.pt", "https://www.sampa.pt", f"/?s={PN}"),
    ("europart.pt", "https://www.europart.pt", f"/?s={PN}"),
    ("europart.net", "https://www.europart.net", f"/?s={PN}"),
    ("vanheck.pt", "https://www.vanheck.pt", f"/?s={PN}"),
    ("goldspeed.pt", "https://www.goldspeed.pt", f"/?s={PN}"),
    ("autototal.pt", "https://www.autototal.pt", f"/?s={PN}"),
    ("interparts.pt", "https://www.interparts.pt", f"/?s={PN}"),
    ("mister-parts.pt", "https://www.mister-parts.pt", f"/?s={PN}"),
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
with (HERE / "_robots_probe_batch8.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["host","base","path","exit","verdict","detail"]); w.writeheader(); w.writerows(rows)
al = [r["host"] for r in rows if r["verdict"]=="allowed"]
print("\nALLOWED:", ", ".join(al) if al else "(none)")
