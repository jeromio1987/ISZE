#!/usr/bin/env python3
"""Italy PNCP / Pubblicità a valore legale — public JSON avvisi API.

Below-threshold national home. No PDND required for list+detail.
Importable by tender_scraper_v3 or runnable alone.
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

IT_PNCP_AVVISI_URL = "https://pubblicitalegale.anticorruzione.it/api/v0/avvisi"
IT_PNCP_CODICE_SCHEDA = "1,3,5a,5b,6,8b,10"

KEYWORDS_IT = [
    "autocarro", "autocarri", "automezzo", "automezzi", "autoveicol",
    "camion", "furgone", "furgoni", "pickup", "pick-up", "pick up",
    "veicoli commerciali", "veicolo commerciale", "veicoli", "veicolo",
    "parco auto", "parco mezzi", "parco automezzi", "parco autovetture",
    "noleggio veicoli", "noleggio auto", "noleggio automez",
    "chassis", "cassone", "cabina", "isuzu", "d-max", "d max",
    "manutenzione", "riparazione", "officina", "flotta",
]
IT_PNCP_NOISE = [
    "telaio pieghevole", "carrozzina", "studio del traffico",
    "fluidificazione del traffic", "autorimessa", "strati bituminosi",
    "pneumatici", "ventilatore",
]
IT_VEHICLE_STEMS = (
    "autocar", "automez", "autoveicol", "camion", "furgon", "pickup",
    "pick-up", "pick up", "veicol", "parco auto", "parco mezzi",
    "parco automez", "noleggio auto", "noleggio veicol", "isuzu",
    "d-max", "chassis", "cassone", "4x4",
)


def _match_any(blob: str, kws: List[str]) -> bool:
    b = (blob or "").lower()
    return any(k.lower() in b for k in kws)


def _walk_text(obj: Any, out: List[str], depth: int = 0) -> None:
    if depth > 8:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            lk = str(k).lower()
            if isinstance(v, (str, int, float)) and any(
                x in lk
                for x in (
                    "titolo", "descr", "oggetto", "cpv", "cig",
                    "denominazione", "valore", "importo",
                )
            ):
                out.append(str(v))
            else:
                _walk_text(v, out, depth + 1)
    elif isinstance(obj, list):
        for item in obj[:40]:
            _walk_text(item, out, depth + 1)


def _extract_list_fields(row: Dict[str, Any]) -> Dict[str, str]:
    title = ""
    desc = ""
    buyer = ""
    cpv = ""
    value = ""
    for t in row.get("templates") or []:
        tmpl = (t.get("template") or {}) if isinstance(t, dict) else {}
        meta = tmpl.get("metadata") or {}
        if meta.get("titolo"):
            title = str(meta.get("titolo") or "")
        if meta.get("descrizione"):
            desc = str(meta.get("descrizione") or "")
        for sec in tmpl.get("sections") or []:
            fields = (sec.get("fields") or {}) if isinstance(sec, dict) else {}
            for sa in fields.get("soggetti_sa") or []:
                if isinstance(sa, dict) and sa.get("denominazione_amministrazione"):
                    buyer = str(sa.get("denominazione_amministrazione") or buyer)
            for item in sec.get("items") or []:
                if not isinstance(item, dict):
                    continue
                if item.get("cpv") and not cpv:
                    raw = str(item.get("cpv") or "")
                    m = re.search(r"\b([0-9]{8})\b", raw)
                    cpv = m.group(1) if m else raw[:80]
                if item.get("valore_complessivo_stimato") not in (None, "") and not value:
                    value = str(item.get("valore_complessivo_stimato"))
                if item.get("descrizione") and not title:
                    title = str(item.get("descrizione") or "")
    blob_parts: List[str] = []
    _walk_text(row, blob_parts)
    blob = " ".join(blob_parts)
    if not title:
        title = (desc or blob)[:240]
    return {
        "title": title.strip(),
        "description": (desc or title).strip(),
        "buyer": buyer.strip(),
        "cpv": cpv.strip(),
        "value": value.strip(),
        "blob": blob.lower(),
    }


def _enrich_detail(session: requests.Session, nid: str) -> Dict[str, str]:
    out = {"cpv": "", "url": "", "buyer": "", "value": ""}
    try:
        resp = session.get(
            f"{IT_PNCP_AVVISI_URL}/{nid}",
            headers={
                "Accept": "application/json",
                "Referer": "https://pubblicitalegale.anticorruzione.it/",
                "User-Agent": "Mozilla/5.0 (compatible; ISZE-TenderMonitor/3.0)",
            },
            timeout=30,
        )
        if resp.status_code != 200 or not (resp.content or b"").startswith((b"{", b"[")):
            return out
        data = resp.json() or {}
        fields = _extract_list_fields(data)
        out["cpv"] = fields["cpv"]
        out["buyer"] = fields["buyer"]
        out["value"] = fields["value"]
        for m in re.finditer(r"https?://[^\s\"'\\]+", json.dumps(data, ensure_ascii=False)):
            link = m.group(0).rstrip(".,);")
            if "anticorruzione" in link:
                continue
            out["url"] = link
            break
        if not out["url"]:
            out["url"] = f"https://pubblicitalegale.anticorruzione.it/dettaglio-avviso/{nid}"
        if out["cpv"] and not re.fullmatch(r"[0-9]{8}", out["cpv"]):
            nums = re.findall(r"\b(34[0-9]{6}|50[0-9]{6})\b", json.dumps(data))
            if nums:
                out["cpv"] = nums[0]
    except Exception:
        pass
    return out


def fetch_italy_pncp(
    session: Optional[requests.Session] = None,
    from_dt: Optional[datetime] = None,
    *,
    page_size: int = 100,
    max_pages: int = 20,
    enrich_detail: bool = True,
    errors: Optional[Dict[str, Optional[str]]] = None,
) -> List[Dict[str, Any]]:
    """National IT notices via PNCP Pubblicità a valore legale public JSON API."""
    print("\n[IT PNCP] Fetching pubblicitalegale avvisi (vehicle keyword filter)...")
    own = session is None
    session = session or requests.Session()
    from_dt = from_dt or datetime.now(timezone.utc)
    results: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    date_from = from_dt.strftime("%d/%m/%Y")
    last_err: Optional[str] = None
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Referer": "https://pubblicitalegale.anticorruzione.it/",
        "Origin": "https://pubblicitalegale.anticorruzione.it",
    }
    try:
        total_scanned = 0
        for page in range(max_pages):
            params = {
                "dataPubblicazioneStart": date_from,
                "page": page,
                "size": page_size,
                "codiceScheda": IT_PNCP_CODICE_SCHEDA,
                "sortField": "dataPubblicazione",
                "sortDirection": "DESC",
            }
            resp = session.get(IT_PNCP_AVVISI_URL, params=params, headers=headers, timeout=45)
            if resp.status_code != 200:
                last_err = f"HTTP {resp.status_code}"
                print(f"  [IT PNCP] page {page}: {last_err}")
                break
            if not (resp.content or b"").startswith((b"{", b"[")):
                last_err = "non-JSON response (portal/WAF?)"
                print("  [IT PNCP] non-JSON response")
                break
            data = resp.json() or {}
            content = data.get("content") or []
            if page == 0:
                print(f"  [IT PNCP] API totalElements≈{data.get('totalElements')}")
            if not content:
                break
            total_scanned += len(content)
            page_hits = 0
            for row in content:
                nid = str(row.get("idAvviso") or "")
                if not nid or nid in seen:
                    continue
                fields = _extract_list_fields(row)
                blob = f"{fields['title']} {fields['description']} {fields['blob']}".lower()
                if any(n in blob for n in IT_PNCP_NOISE):
                    continue
                if not _match_any(blob, KEYWORDS_IT):
                    continue
                if not any(s in blob for s in IT_VEHICLE_STEMS):
                    continue
                seen.add(nid)
                page_hits += 1
                detail = _enrich_detail(session, nid) if enrich_detail else {}
                cpv = detail.get("cpv") or fields["cpv"]
                buyer = detail.get("buyer") or fields["buyer"]
                value = detail.get("value") or fields["value"]
                url = detail.get("url") or (
                    f"https://pubblicitalegale.anticorruzione.it/dettaglio-avviso/{nid}"
                )
                title = fields["title"] or fields["description"][:200]
                pub = str(row.get("dataPubblicazione") or "")[:10]
                deadline = str(row.get("dataScadenza") or "")
                results.append(
                    {
                        "Source": "🇮🇹 IT-PNCP",
                        "Source Notice ID": nid,
                        "Lifecycle": "",
                        "Notice Type": str(row.get("tipologia") or ""),
                        "Procedure Type": str(row.get("codiceScheda") or ""),
                        "Buyer Type": "",
                        "Score": "",
                        "FleetSize": "",
                        "Title": title,
                        "Buyer": buyer,
                        "CPV Code": cpv if re.fullmatch(r"[0-9]{8}", cpv or "") else "",
                        "CPV Desc": "" if re.fullmatch(r"[0-9]{8}", cpv or "") else (cpv or ""),
                        "Description": fields["description"][:500],
                        "Est. Value": value,
                        "Currency": "EUR",
                        "Published": pub,
                        "Deadline": deadline,
                        "Country": "Italy",
                        "Country Code": "ITA",
                        "URL": url,
                    }
                )
                if enrich_detail:
                    time.sleep(0.15)
            print(f"  [IT PNCP] page {page}: scanned={len(content)} hits+={page_hits}")
            if data.get("last"):
                break
            time.sleep(0.25)
        last_err = (
            None if results else f"zero vehicle-ish rows in {total_scanned} scanned notices"
        )
        print(f"[IT PNCP] Unique matches: {len(results)} (scanned≈{total_scanned})")
    except Exception as exc:
        last_err = str(exc)
        print(f"  [IT PNCP] exception: {exc}")
    finally:
        if own:
            session.close()
    if errors is not None:
        errors["Italy PNCP"] = last_err
    return results


if __name__ == "__main__":
    from datetime import timedelta

    err: Dict[str, Optional[str]] = {}
    lookback = datetime.now(timezone.utc) - timedelta(days=30)
    rows = fetch_italy_pncp(from_dt=lookback, max_pages=5, enrich_detail=False, errors=err)
    print("error:", err.get("Italy PNCP"), "n=", len(rows))
    for r in rows[:5]:
        print(" -", (r.get("Title") or "")[:100])
