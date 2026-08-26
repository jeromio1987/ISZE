"""Overnight probe: next P1 portals after DE (PT BASE, DK udbud, AT USP) — no fake notices."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
OUT = HERE / "_probe_overnight_next_portals.json"

UA = "Mozilla/5.0 (compatible; ISZE-TenderMonitor/3.0 overnight)"
s = requests.Session()
s.headers.update({"User-Agent": UA, "Accept": "*/*"})

probes = [
    ("PT_BASE_home", "https://www.base.gov.pt/", "GET", None, None),
    ("PT_BASE_api_docs", "https://www.base.gov.pt/Base4/pt/documentacao/", "GET", None, None),
    ("PT_APIBase2_guess", "https://www.base.gov.pt/api/contrato/pesquisa", "GET", {"texto": "veiculo", "tamanho": 5}, None),
    ("PT_APIBase_v1", "https://www.base.gov.pt/Base4/pt/resultados/", "GET", None, None),
    ("DK_udbud_home", "https://www.udbud.dk/", "GET", None, None),
    ("DK_udbud_search", "https://www.udbud.dk/Pages/Search/Index", "GET", {"q": "køretøj"}, None),
    ("DK_udbud_api_guess", "https://www.udbud.dk/api/search", "GET", {"q": "varebil"}, None),
    ("AT_USP_home", "https://www.usp.gv.at/", "GET", None, None),
    ("AT_USP_suche", "https://www.usp.gv.at/Portal.Node/usp/public/content/ausschreibungen/ausschreibungs_suche/inhalt.html", "GET", None, None),
    ("RO_SEAP_home", "https://www.e-licitatie.ro/", "GET", None, None),
    ("RO_SEAP_public", "https://www.e-licitatie.ro/pub", "GET", None, None),
]

results = []
for name, url, method, params, body in probes:
    row = {"name": name, "url": url}
    try:
        if method == "POST":
            r = s.post(url, params=params, json=body, timeout=35)
        else:
            r = s.get(url, params=params, timeout=35, allow_redirects=True)
        row["status"] = r.status_code
        row["ctype"] = (r.headers.get("Content-Type") or "")[:80]
        row["bytes"] = len(r.content or b"")
        row["final_url"] = str(r.url)[:200]
        head = (r.content or b"")[:500].lower()
        row["has_json"] = (r.content or b"")[:1] in (b"{", b"[")
        row["has_html"] = b"<html" in head or b"<!doctype" in head
        row["has_login"] = b"login" in head or b"autentic" in head or b"sign in" in head
        row["preview"] = (r.content or b"")[:180].decode("utf-8", errors="replace").replace("\n", " ")
    except Exception as exc:
        row["error"] = str(exc)
    results.append(row)
    print(f"{name}: {row.get('status')} {row.get('bytes')}B json={row.get('has_json')} err={row.get('error')}")

payload = {"probed_at": datetime.now(timezone.utc).isoformat(), "results": results}
OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {OUT}")
