# -*- coding: utf-8 -*-
"""Fetch the original notice document for each result notice already in tender_data.json.
Germany: oeffentlichevergabe.de /api/notices/{id}. Norway: Doffin public API /download/{id} (key from the scraper's own loader).
Saves raw files only, into a NEW folder; never overwrites; never prints the key. Run with python -I."""
import json, re, sys, time, urllib.request, urllib.error
from pathlib import Path
sys.path.insert(0, r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install")
from nordics_keys import get_doffin_key

OUTDIR = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\tender_result_notices_20261015\raw")
OUTDIR.mkdir(parents=True, exist_ok=True)
d = json.load(open(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\14_dashboards\tender_data.json", encoding="utf-8"))
res = [n for n in d["notices"] if re.search(r"RESULT|can-standard|can-modif|conclusion", str(n.get("Notice Type")), re.I)]
key = get_doffin_key()
log = []
for n in res:
    nid = n["Source Notice ID"]; src = "DE" if "DE-OV" in str(n.get("Source")) else "NO"
    f = OUTDIR / f"{src}_{nid}.xml"
    if f.exists():
        log.append((src, nid, "exists", f.stat().st_size)); continue
    if src == "DE":
        url = f"https://oeffentlichevergabe.de/api/notices/{nid}"; h = {"User-Agent": "ISZE-tender-monitor/3 (internal research)"}
    else:
        url = f"https://dof-notices-prod-api.azure-api.net/public/v2/download/{nid}"; h = {"Ocp-Apim-Subscription-Key": key, "User-Agent": "ISZE-tender-monitor/3"}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=40) as r:
            b = r.read()
        f.write_bytes(b); log.append((src, nid, "ok", len(b)))
    except urllib.error.HTTPError as e:
        log.append((src, nid, f"HTTP {e.code}", 0))
    except Exception as e:
        log.append((src, nid, type(e).__name__, 0))
    time.sleep(4.0)
from collections import Counter
print(Counter((a, c) for a, b, c, s in log))
print("total", len(log), "bytes", sum(s for *_, s in log))
for r in log:
    if r[2] not in ("ok", "exists"): print(r)
