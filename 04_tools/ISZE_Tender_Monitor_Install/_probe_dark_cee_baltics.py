#!/usr/bin/env python3
"""Probe dark national portals (CZ/SK/HR/SI/LT/LV/EE/GR/CY/MT/BG) + ES residual.
No Nordics. No browser spam. Write evidence JSON only.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
OUT = HERE / "_probe_dark_cee_baltics.json"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

# (name, method, url, kwargs)
PROBES: List[tuple] = [
    # EE — official open data
    ("EE_rhr_opendata", "GET", "https://riigihanked.riik.ee/rhr/api/public/v1/opendata", {}),
    ("EE_rhr_home", "GET", "https://riigihanked.riik.ee/", {}),
    ("EE_rhr_search_api_guess", "GET", "https://riigihanked.riik.ee/rhr/api/public/v1/notices", {}),
    ("EE_avahanked_rss", "GET", "https://avahanked.ee/rss.xml", {}),
    # GR — KIMDIS / Promitheus open data
    ("GR_promitheus_home", "GET", "https://www.promitheus.gov.gr/", {}),
    ("GR_eprocurement_home", "GET", "https://www.eprocurement.gov.gr/", {}),
    ("GR_kimdis_opendata_guess", "GET", "https://cerpp.eprocurement.gov.gr/kimdis/opendata", {}),
    ("GR_opendata_api_guess", "GET", "https://www.eprocurement.gov.gr/opendata", {}),
    ("GR_opendata_api2", "GET", "https://opendata.eprocurement.gov.gr/", {}),
    ("GR_portal_opendata", "GET", "https://portal.eprocurement.gov.gr/webcenter/portal/TestPortal", {}),
    # CZ
    ("CZ_nen_home", "GET", "https://nen.nipez.cz/", {}),
    ("CZ_vvz_home", "GET", "https://www.vestnikverejnychzakazek.cz/", {}),
    ("CZ_vvz_api_guess", "GET", "https://www.vestnikverejnychzakazek.cz/SearchForm/Search", {}),
    ("CZ_data_gov_search", "GET", "https://data.gov.cz/datov%C3%A1-sada?dotaz=ve%C5%99ejn%C3%A9+zak%C3%A1zky", {}),
    ("CZ_hlidac_smluv", "GET", "https://www.hlidacstatu.cz/api/v2/hledat?dotaz=isuzu&strana=1", {}),
    # SK
    ("SK_uvo_home", "GET", "https://www.uvo.gov.sk/", {}),
    ("SK_uvo_vestnik", "GET", "https://www.uvo.gov.sk/vyhladavanie/vyhladavanie-zakaziek", {}),
    ("SK_uvo_rss_guess", "GET", "https://www.uvo.gov.sk/rss", {}),
    ("SK_data_gov", "GET", "https://data.slovensko.sk/datasets?query=vestn%C3%ADk", {}),
    ("SK_evo_home", "GET", "https://www.evo.gov.sk/", {}),
    # HR
    ("HR_eojn_home", "GET", "https://eojn.nn.hr/", {}),
    ("HR_eojn_nn", "GET", "https://eojn.nn.hr/SPIN/application/ipn/DocumentManagement/SearchDokumentObjavaEP.aspx", {}),
    ("HR_nn_home", "GET", "https://narodne-novine.nn.hr/", {}),
    # SI
    ("SI_enarocanje_home", "GET", "https://www.enarocanje.si/", {}),
    ("SI_enarocanje_search", "GET", "https://www.enarocanje.si/Obrazci/", {}),
    ("SI_enarocanje_api_guess", "GET", "https://www.enarocanje.si/api/obrazci", {}),
    # LT
    ("LT_cvpp_home", "GET", "https://cvpp.eviesiejipirkimai.lt/", {}),
    ("LT_cvp_home", "GET", "https://viesiejipirkimai.lt/", {}),
    ("LT_opendata_guess", "GET", "https://data.gov.lt/datasets/?q=vie%C5%A1ieji+pirkimai", {}),
    # LV
    ("LV_eis_home", "GET", "https://www.eis.gov.lv/", {}),
    ("LV_iub_home", "GET", "https://www.iub.gov.lv/", {}),
    ("LV_eis_search", "GET", "https://www.eis.gov.lv/EIS/Procurement/Procurements.aspx", {}),
    ("LV_opendata", "GET", "https://data.gov.lv/dati/lv/dataset?q=iepirkumi", {}),
    # BG — official OCDS open-data daily bundles
    ("BG_eop_home", "GET", "https://app.eop.bg/", {}),
    ("BG_aop_home", "GET", "https://www.aop.bg/", {}),
    ("BG_eop_opendata_page", "GET", "https://app.eop.bg/today/reporting/open-data", {}),
    ("BG_eop_storage_today", "GET", "https://storage.eop.bg/open-data-2026-08-25/", {}),
    ("BG_eop_storage_yest", "GET", "https://storage.eop.bg/open-data-2026-08-24/", {}),
    ("BG_eop_storage_index", "GET", "https://storage.eop.bg/", {}),
    ("BG_opendata", "GET", "https://data.egov.bg/organisation/aop", {}),
    # CZ VVZ SPA + public list
    ("CZ_vvz_nipez", "GET", "https://vvz.nipez.cz/", {}),
    ("CZ_vvz_nove", "GET", "https://vvz.nipez.cz/nove-zakazky", {}),
    ("CZ_vvz_api_forms", "GET", "https://vvz.nipez.cz/api/Formulare", {}),
    ("CZ_vvz_api_search", "GET", "https://vvz.nipez.cz/api/Search", {}),
    # LT CVP API (needs key — probe shape)
    ("LT_cvp_export_no_key", "POST", "https://viesiejipirkimai.lt/epps-integration/api/cft-details-export",
     {"json": {"pageSize": 5, "pageNum": 1}}),
    # GR KIMDIS more guesses
    ("GR_kimdis_api", "GET", "https://cerpp.eprocurement.gov.gr/kimds2/", {}),
    ("GR_opendata_swagger", "GET", "https://www.promitheus.gov.gr/opendata/swagger", {}),
    ("GR_diavgeia_search", "GET", "https://diavgeia.gov.gr/luminapi/api/search?q=φορτηγ&page=0&size=5", {}),
    # CY
    ("CY_eproc_home", "GET", "https://www.eprocurement.gov.cy/", {}),
    ("CY_eproc_search", "GET", "https://www.eprocurement.gov.cy/ceproc/home.do", {}),
    # MT
    ("MT_etenders_home", "GET", "https://www.etenders.gov.mt/", {}),
    ("MT_etenders_epps", "GET", "https://www.etenders.gov.mt/epps/home.do", {}),
    # ES residual — alternate hosts / open data mirrors (no browser)
    ("ES_atom_retry", "GET",
     "https://contrataciondelestado.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom",
     {}),
    ("ES_datos_gob_placsp", "GET",
     "https://datos.gob.es/apidata/catalog/dataset?q=contrataci%C3%B3n+del+estado&_pageSize=5",
     {}),
    ("ES_placsp_zip_guess", "GET",
     "https://contrataciondelestado.es/wps/portal/perfilContratante",
     {}),
    # HU residual — open data mirrors
    ("HU_kozbeszerzes_home", "GET", "https://www.kozbeszerzes.hu/", {}),
    ("HU_ekr_api_guess", "GET", "https://ekr.gov.hu/api/", {}),
    ("HU_data_gov", "GET", "https://open.kormany.hu/", {}),
]


def probe_one(session: requests.Session, name: str, method: str, url: str, kwargs: dict) -> Dict[str, Any]:
    row: Dict[str, Any] = {"name": name, "url": url, "method": method}
    try:
        headers = {"User-Agent": UA, "Accept": "*/*"}
        if method.upper() == "POST":
            resp = session.post(url, headers=headers, timeout=35, **kwargs)
        else:
            resp = session.get(url, headers=headers, timeout=35, allow_redirects=True, **kwargs)
        body = resp.content or b""
        text = ""
        try:
            text = body[:2500].decode("utf-8", errors="replace")
        except Exception:
            text = str(body[:500])
        ct = (resp.headers.get("Content-Type") or "").lower()
        row.update(
            {
                "http": resp.status_code,
                "len": len(body),
                "ct": ct,
                "final_url": str(resp.url),
                "snip": text[:400].replace("\n", " ").replace("\r", " "),
                "jsonish": ("application/json" in ct) or text.lstrip().startswith(("{", "[")),
                "xmlish": ("xml" in ct) or text.lstrip().startswith("<?xml") or "<feed" in text[:200].lower(),
                "waf": "web application firewall" in text.lower() or "waf" in text.lower() and "denied" in text.lower(),
                "loginish": any(
                    x in text.lower()
                    for x in ("login", "sign in", "prihlás", "bejelentkez", "authent", "password", "captcha")
                ),
            }
        )
        if row["jsonish"] and len(body) < 2_000_000:
            try:
                data = resp.json()
                if isinstance(data, dict):
                    row["json_keys"] = list(data.keys())[:25]
                elif isinstance(data, list):
                    row["json_len"] = len(data)
                    if data and isinstance(data[0], dict):
                        row["json_item_keys"] = list(data[0].keys())[:25]
            except Exception as e:
                row["json_err"] = str(e)[:120]
    except Exception as e:
        row["error"] = str(e)[:300]
    return row


def main() -> None:
    session = requests.Session()
    results: List[Dict[str, Any]] = []
    for name, method, url, kwargs in PROBES:
        print(f"→ {name}")
        row = probe_one(session, name, method, url, kwargs)
        status = row.get("http") or row.get("error", "?")
        print(f"  {status} len={row.get('len', 0)} json={row.get('jsonish')} xml={row.get('xmlish')} waf={row.get('waf')}")
        results.append(row)
        time.sleep(0.35)
    out = {
        "probed_at": datetime.now(timezone.utc).isoformat(),
        "count": len(results),
        "results": results,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
