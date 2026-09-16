#!/usr/bin/env python3
"""Deep P0/P1 portal probe — DK/PT/HU/IE/CZ/SE/ES/HILMA alternatives. Honest JSON only."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests

HERE = Path(__file__).resolve().parent
OUT = HERE / "_overnight_deep_p0p1_probe.json"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

TARGETS: List[Dict[str, Any]] = [
    # ES PLACSP WAF workarounds
    {"id": "ES_atom_643", "method": "GET",
     "url": "https://contrataciondelestado.es/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom"},
    {"id": "ES_atom_1044", "method": "GET",
     "url": "https://contrataciondelestado.es/sindicacion_1044/PlataformasAgregadasSinMenores.atom"},
    {"id": "ES_atom_sectorpublico", "method": "GET",
     "url": "https://contrataciondelsectorpublico.gob.es/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom"},
    {"id": "ES_datosabiertos", "method": "GET",
     "url": "https://contrataciondelestado.es/wps/portal/datosabiertos"},
    {"id": "ES_hacienda_referer", "method": "GET",
     "url": "https://contrataciondelestado.es/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom",
     "headers": {"Referer": "https://www.hacienda.gob.es/"}},
    # DK udbud.dk — SPA; hunt API from main.js / known backends
    {"id": "DK_home", "method": "GET", "url": "https://udbud.dk/"},
    {"id": "DK_api_udbud", "method": "GET", "url": "https://api.udbud.dk/"},
    {"id": "DK_api_search", "method": "GET", "url": "https://api.udbud.dk/v1/notices"},
    {"id": "DK_api_procurements", "method": "GET",
     "url": "https://api.udbud.dk/api/procurements?pageSize=5"},
    {"id": "DK_kfst", "method": "GET",
     "url": "https://www.kfst.dk/udbud/"},
    # PT BASE
    {"id": "PT_base4", "method": "GET", "url": "https://www.base.gov.pt/base4"},
    {"id": "PT_base4_contratos", "method": "GET",
     "url": "https://www.base.gov.pt/Base4/pt/pesquisa/?type=contratos&texto=veiculo"},
    {"id": "PT_base4_ajax", "method": "POST",
     "url": "https://www.base.gov.pt/Base4/pt/resultados/",
     "data": {"type": "search_contratos", "query": "veiculo", "sort": "-publicationDate", "page": "0", "size": "5"},
     "headers": {"Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest",
                 "Referer": "https://www.base.gov.pt/Base4/pt/pesquisa/?type=contratos"}},
    {"id": "PT_impic_api", "method": "GET",
     "url": "https://www.base.gov.pt/apiBase2/v1/contratos"},
    {"id": "PT_dados_gov", "method": "GET",
     "url": "https://dados.gov.pt/api/1/datasets/?q=base+contratos&page_size=5"},
    # HU EKR
    {"id": "HU_ekr", "method": "GET", "url": "https://ekr.gov.hu/"},
    {"id": "HU_ekr_search", "method": "GET",
     "url": "https://ekr.gov.hu/portal/kozbeszerzes/eljarasok"},
    {"id": "HU_ekr_api_guess", "method": "GET",
     "url": "https://ekr.gov.hu/api/notice/search"},
    {"id": "HU_kozbeszerzes", "method": "GET",
     "url": "https://www.kozbeszerzes.hu/"},
    # IE eTenders
    {"id": "IE_home", "method": "GET", "url": "https://www.etenders.gov.ie/epps/home.do"},
    {"id": "IE_search", "method": "GET",
     "url": "https://www.etenders.gov.ie/epps/quickSearchAction.do?searchType=cft&keyword=vehicle"},
    {"id": "IE_rss", "method": "GET",
     "url": "https://www.etenders.gov.ie/epps/cft/listContractNotices.do?searchType=cft"},
    # CZ NEN / VVZ
    {"id": "CZ_nen", "method": "GET", "url": "https://nen.nipez.cz/"},
    {"id": "CZ_vvz", "method": "GET", "url": "https://www.vestnikverejnychzakazek.cz/"},
    {"id": "CZ_nen_api", "method": "GET",
     "url": "https://nen.nipez.cz/api/"},
    {"id": "CZ_hlidac", "method": "GET",
     "url": "https://www.hlidacstatu.cz/api/v2/verejnezakazky/hledat?dotaz=vozidlo&strana=1"},
    # SE — fragmented
    {"id": "SE_uhmd", "method": "GET",
     "url": "https://www.upphandlingsmyndigheten.se/"},
    {"id": "SE_kommers", "method": "GET",
     "url": "https://www.kommersannons.se/"},
    {"id": "SE_oppnadata", "method": "GET",
     "url": "https://www.dataportal.se/sv/datasets?q=upphandling"},
    # HILMA alternate hosts / products
    {"id": "FI_hilma_portal", "method": "GET",
     "url": "https://www.hankintailmoitukset.fi/fi/"},
    {"id": "FI_hilma_avp", "method": "GET",
     "url": "https://hns-hilma-prod-apim.azure-api.net/avp/Notices"},
    {"id": "FI_hilma_dev", "method": "GET",
     "url": "https://hns-hilma-prod-apim.developer.azure-api.net/"},
]


def sniff(resp: requests.Response) -> Dict[str, Any]:
    text = resp.text or ""
    ct = (resp.headers.get("content-type") or "").lower()
    waf = any(x in text.lower() for x in ("request rejected", "access denied", "akamai", "cloudflare", "captcha"))
    jsonish = "json" in ct or text.strip()[:1] in ("{", "[")
    atom = "atom" in ct or "<feed" in text[:500].lower() or "<rss" in text[:500].lower()
    scripts = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', text, flags=re.I)[:15]
    api_hints = sorted(set(re.findall(r'https?://[a-z0-9._/-]*(?:api|odata|search|notice)[a-z0-9._/-]*', text, flags=re.I)))[:20]
    return {
        "http": resp.status_code,
        "ct": ct[:80],
        "bytes": len(resp.content or b""),
        "final": str(resp.url),
        "waf_like": waf,
        "jsonish": jsonish,
        "atom_rss": atom,
        "preview": text[:220].replace("\n", " "),
        "scripts": scripts,
        "api_hints": api_hints,
    }


def load_hilma_key() -> Optional[str]:
    env = HERE / "nordics_api_keys.env"
    if not env.exists():
        return None
    for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip().startswith("ISZE_HILMA_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    results: Dict[str, Any] = {
        "probed_at": datetime.now(timezone.utc).isoformat(),
        "targets": {},
    }
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept": "*/*"})

    for t in TARGETS:
        tid = t["id"]
        headers = dict(session.headers)
        headers.update(t.get("headers") or {})
        # Attach HILMA key when hitting APIM
        if "hilma" in tid.lower() and "azure-api" in t["url"]:
            key = load_hilma_key()
            if key:
                headers["Ocp-Apim-Subscription-Key"] = key
        try:
            if t.get("method", "GET").upper() == "POST":
                resp = session.post(t["url"], data=t.get("data"), headers=headers, timeout=45, allow_redirects=True)
            else:
                resp = session.get(t["url"], headers=headers, timeout=45, allow_redirects=True)
            results["targets"][tid] = sniff(resp)
            print(f"[{tid}] {results['targets'][tid]['http']} bytes={results['targets'][tid]['bytes']} waf={results['targets'][tid]['waf_like']}")
        except Exception as exc:
            results["targets"][tid] = {"error": str(exc)}
            print(f"[{tid}] ERROR {exc}")

    # Follow DK SPA: if home has main.*.js, fetch and mine API hosts
    dk = results["targets"].get("DK_home") or {}
    mined: List[Dict[str, Any]] = []
    for src in dk.get("scripts") or []:
        full = urljoin("https://udbud.dk/", src)
        try:
            r = session.get(full, timeout=45)
            hosts = sorted(set(re.findall(r'https?://[a-zA-Z0-9._-]+(?:/api[^"\'\\s]*)?', r.text)))
            endpoints = sorted(set(re.findall(r'["\'](/api/[^"\']+)["\']', r.text)))[:40]
            mined.append({"js": full, "http": r.status_code, "bytes": len(r.content), "hosts": hosts[:30], "endpoints": endpoints})
            # Probe discovered absolute API hosts briefly
            for h in hosts[:8]:
                if "udbud" not in h and "kfst" not in h and "azure" not in h:
                    continue
                try:
                    pr = session.get(h if h.endswith("/") else h + "/", timeout=20)
                    mined.append({"probe": h, "http": pr.status_code, "bytes": len(pr.content), "preview": pr.text[:120]})
                except Exception as e:
                    mined.append({"probe": h, "error": str(e)})
        except Exception as e:
            mined.append({"js": full, "error": str(e)})
    results["dk_js_mine"] = mined

    # PT: mine Base4 JS for ajax endpoints
    pt = results["targets"].get("PT_base4") or {}
    pt_mine: List[Dict[str, Any]] = []
    for src in (pt.get("scripts") or [])[:8]:
        full = urljoin("https://www.base.gov.pt/", src)
        try:
            r = session.get(full, timeout=45)
            endpoints = sorted(set(re.findall(r'["\']([^"\']*(?:resultados|api|pesquisa|contrato)[^"\']*)["\']', r.text, flags=re.I)))[:50]
            pt_mine.append({"js": full, "http": r.status_code, "bytes": len(r.content), "endpoints": endpoints})
        except Exception as e:
            pt_mine.append({"js": full, "error": str(e)})
    results["pt_js_mine"] = pt_mine

    OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
