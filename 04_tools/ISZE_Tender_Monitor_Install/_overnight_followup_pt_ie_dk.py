#!/usr/bin/env python3
"""Follow-up probes: PT dados.gov downloads, IE HTML parse, DK JS API mine, Hlidac, ES via proxy headers."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urljoin

import requests

HERE = Path(__file__).resolve().parent
OUT = HERE / "_overnight_followup_pt_ie_dk.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "*/*"})
    out: Dict[str, Any] = {"probed_at": datetime.now(timezone.utc).isoformat()}

    # --- PT dados.gov datasets ---
    pt_sets = [
        "https://dados.gov.pt/api/1/datasets/contratos-publicos-portal-base-impic-anuncios-de-2012-a-2026/",
        "https://dados.gov.pt/api/1/datasets/contratos-publicos-portal-base-impic-contratos-de-2012-a-2026/",
        "https://dados.gov.pt/api/1/datasets/ocds-portal-base-www-base-gov-pt/",
    ]
    out["pt_datasets"] = {}
    for url in pt_sets:
        try:
            r = s.get(url, timeout=60)
            data = r.json() if "json" in (r.headers.get("content-type") or "") else {}
            resources = []
            for res in (data.get("resources") or [])[:8]:
                resources.append({
                    "title": res.get("title"),
                    "format": res.get("format"),
                    "url": res.get("url"),
                    "last_modified": res.get("last_modified"),
                })
            out["pt_datasets"][url] = {"http": r.status_code, "title": data.get("title"), "resources": resources}
            print("PT", data.get("title"), "resources", len(resources))
            # Try first CSV/JSON resource head
            for res in resources:
                u = res.get("url") or ""
                if not u:
                    continue
                try:
                    hr = s.get(u, timeout=90, stream=True)
                    chunk = next(hr.iter_content(64_000), b"")
                    text = chunk.decode("utf-8", errors="replace")
                    out["pt_datasets"][url].setdefault("samples", []).append({
                        "url": u,
                        "http": hr.status_code,
                        "bytes_chunk": len(chunk),
                        "preview": text[:400],
                        "vehicle_hits": len(re.findall(r"ve[ií]culo|cami[aã]o|pickup|chassis|frota|manuten", text, flags=re.I)),
                    })
                    print("  sample", hr.status_code, len(chunk), "veh", out["pt_datasets"][url]["samples"][-1]["vehicle_hits"])
                    break
                except Exception as e:
                    out["pt_datasets"][url].setdefault("samples", []).append({"url": u, "error": str(e)})
        except Exception as e:
            out["pt_datasets"][url] = {"error": str(e)}

    # --- PT Base4 JS search endpoint mine ---
    try:
        page = s.get("https://www.base.gov.pt/Base4/pt/pesquisa/?type=contratos&texto=veiculo", timeout=45)
        scripts = re.findall(r'src=["\']([^"\']+)["\']', page.text)
        js_hits = []
        for src in scripts:
            if "jquery" in src.lower() or "bootstrap" in src.lower() or "autoNumeric" in src.lower():
                continue
            full = urljoin("https://www.base.gov.pt/", src)
            try:
                jr = s.get(full, timeout=45)
                eps = sorted(set(re.findall(r'["\']([^"\']*(?:resultados|/Base4/|type=search)[^"\']*)["\']', jr.text)))[:40]
                if "resultados" in jr.text or "search_" in jr.text:
                    js_hits.append({"js": full, "bytes": len(jr.content), "eps": eps, "has_search": "search_" in jr.text})
            except Exception as e:
                js_hits.append({"js": full, "error": str(e)})
        # Also try known Base4 ajax patterns from community
        ajax_tries = []
        for payload in [
            {"type": "search_contratos", "query": "veiculo", "sortBy": "-publicationDate", "page": "0", "size": "10"},
            {"type": "search_contratos", "texto": "veiculo", "sort": "-publicationDate", "page": "0", "size": "10"},
            {"type": "search_anuncios", "query": "veiculo", "page": "0", "size": "10"},
            {"type": "search_anuncios", "texto": "veiculo", "page": "0", "size": "10"},
        ]:
            rr = s.post(
                "https://www.base.gov.pt/Base4/pt/resultados/",
                data=payload,
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": "https://www.base.gov.pt/Base4/pt/pesquisa/?type=contratos",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                },
                timeout=45,
            )
            ajax_tries.append({
                "payload": payload,
                "http": rr.status_code,
                "bytes": len(rr.content or b""),
                "ct": rr.headers.get("content-type"),
                "preview": (rr.text or "")[:300],
            })
            print("PT ajax", payload["type"], rr.status_code, len(rr.content or b""))
        out["pt_base4"] = {"js_hits": js_hits, "ajax_tries": ajax_tries}
    except Exception as e:
        out["pt_base4"] = {"error": str(e)}

    # --- IE eTenders HTML ---
    try:
        ie = s.get(
            "https://www.etenders.gov.ie/epps/quickSearchAction.do?searchType=cft&keyword=vehicle&TenderStatus=0",
            timeout=60,
        )
        titles = re.findall(r'(?:class="[^"]*title[^"]*"|cftDetail)[^>]*>([^<]{10,160})<', ie.text, flags=re.I)
        links = re.findall(r'href="([^"]*cft[^"]*)"', ie.text, flags=re.I)[:30]
        out["ie"] = {
            "http": ie.status_code,
            "bytes": len(ie.content),
            "title_samples": titles[:15],
            "link_samples": links[:15],
            "has_cft": "cft" in ie.text.lower(),
            "vehicle_count": len(re.findall(r"vehicle|truck|fleet|van|pickup|maintenance", ie.text, flags=re.I)),
        }
        print("IE", ie.status_code, "bytes", len(ie.content), "veh", out["ie"]["vehicle_count"], "titles", len(titles))
        # alternate list page
        ie2 = s.get("https://www.etenders.gov.ie/epps/cft/prepareSearchCFT.do?searchType=cft", timeout=60)
        out["ie_prepare"] = {"http": ie2.status_code, "bytes": len(ie2.content), "preview": ie2.text[:250]}
    except Exception as e:
        out["ie"] = {"error": str(e)}

    # --- DK JS mine ---
    try:
        home = s.get("https://udbud.dk/", timeout=30)
        m = re.search(r'src="(/assets/js/main-[^"]+\.js)"', home.text)
        out["dk"] = {"home_bytes": len(home.content), "main_js": m.group(1) if m else None}
        if m:
            jr = s.get(urljoin("https://udbud.dk/", m.group(1)), timeout=60)
            hosts = sorted(set(re.findall(r'https?://[a-zA-Z0-9._:-]+', jr.text)))
            api_paths = sorted(set(re.findall(r'["\'](/[a-zA-Z0-9._/-]*(?:notice|search|procurement|tender|annonce)[a-zA-Z0-9._/-]*)["\']', jr.text)))[:50]
            out["dk"].update({
                "js_bytes": len(jr.content),
                "hosts": [h for h in hosts if any(x in h for x in ("udbud", "kfst", "azure", "api", "mitudbud", "erhverv"))][:40],
                "api_paths": api_paths,
            })
            print("DK hosts", out["dk"]["hosts"][:10], "paths", api_paths[:10])
            for h in out["dk"]["hosts"][:12]:
                try:
                    pr = s.get(h, timeout=20)
                    out["dk"].setdefault("host_probes", []).append({
                        "url": h, "http": pr.status_code, "bytes": len(pr.content), "preview": pr.text[:120]
                    })
                except Exception as e:
                    out["dk"].setdefault("host_probes", []).append({"url": h, "error": str(e)})
    except Exception as e:
        out["dk"] = {"error": str(e)}

    # --- CZ Hlidac public search HTML ---
    try:
        cz = s.get("https://www.hlidacstatu.cz/VerejneZakazky?Q=vozidlo", timeout=45)
        out["cz_hlidac"] = {
            "http": cz.status_code,
            "bytes": len(cz.content),
            "preview": cz.text[:300],
            "hits": len(re.findall(r"zakazk|veřejn|verejn|vozidl", cz.text, flags=re.I)),
        }
        print("CZ hlidac", cz.status_code, out["cz_hlidac"]["hits"])
    except Exception as e:
        out["cz_hlidac"] = {"error": str(e)}

    # --- HILMA alternate product paths with key ---
    key = None
    for line in (HERE / "nordics_api_keys.env").read_text(encoding="utf-8").splitlines():
        if line.startswith("ISZE_HILMA_API_KEY="):
            key = line.split("=", 1)[1].strip()
    hilma_urls = [
        "https://hns-hilma-prod-apim.azure-api.net/avp/Notices",
        "https://hns-hilma-prod-apim.azure-api.net/avp/Search",
        "https://hns-hilma-prod-apim.azure-api.net/search/Notices",
        "https://hns-hilma-prod-apim.azure-api.net/eforms/Notices",
        "https://api.hankintailmoitukset.fi/avp/Notices",
    ]
    out["hilma_alts"] = []
    for u in hilma_urls:
        headers = {"Accept": "application/json"}
        if key:
            headers["Ocp-Apim-Subscription-Key"] = key
        try:
            r = s.get(u, headers=headers, params={"publishedFrom": "2026-07-01"}, timeout=30)
            out["hilma_alts"].append({"url": u, "http": r.status_code, "preview": r.text[:160]})
            print("HILMA", u.split(".net")[-1], r.status_code)
        except Exception as e:
            out["hilma_alts"].append({"url": u, "error": str(e)})

    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
