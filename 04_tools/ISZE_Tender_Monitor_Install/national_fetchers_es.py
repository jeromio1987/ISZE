#!/usr/bin/env python3
"""Spain PLACSP national syndication — Atom (with rel=next) + optional monthly ZIP.

Official OpenPLACSP / Hacienda syndication. No inventing notices.
Importable by tender_scraper_v3 or runnable alone.
"""
from __future__ import annotations

import io
import re
import sys
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from xml.etree import ElementTree as ET

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Live rolling Atom + host aliases (both currently serve XML when egress is clean).
ES_PLACSP_ATOM_SEEDS = [
    "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom",
    "https://contrataciondelestado.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom",
]
# Aggregated platforms feed (excludes contratos menores) — secondary.
ES_PLACSP_ATOM_AGG = [
    "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_1044/PlataformasAgregadasSinMenores.atom",
]

ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}

# Vehicle stems — bare "mantenimiento" alone must NOT pass.
ES_VEHICLE_STEMS = (
    "vehiculo",
    "vehículo",
    "vehiculos",
    "vehículos",
    "camion",
    "camión",
    "camiones",
    "furgon",
    "furgón",
    "furgoneta",
    "pickup",
    "pick-up",
    "pick up",
    "todoterreno",
    "4x4",
    "chasis",
    "chassis",
    "volquete",
    "flota",
    "parque movil",
    "parque móvil",
    "isuzu",
    "d-max",
    "d max",
    "utilitario",
    "autocaravana",  # rare; kept for completeness
    "camioneta",
    "todos terreno",
)

ES_CPV_RE = re.compile(r"\b(3413\d{4}|3411\d{4}|34136\d{2}|34130\d{2}|5011\d{4})\b")


def _waf_body(body: bytes) -> bool:
    head = (body or b"")[:800].lower()
    return (
        b"web application firewall" in head
        or b"has denied your transaction" in head
        or (b"<html" in head and b"denied" in head)
    )


def _match_vehicle(blob: str) -> bool:
    b = (blob or "").lower()
    if ES_CPV_RE.search(b):
        return True
    return any(s in b for s in ES_VEHICLE_STEMS)


def _entry_text(entry: ET.Element) -> Tuple[str, str, str, str, str]:
    """Return title, description/blob, published, link, id."""
    title = (
        entry.findtext("a:title", default="", namespaces=ATOM_NS)
        or entry.findtext("{http://www.w3.org/2005/Atom}title")
        or ""
    ).strip()
    summary = (
        entry.findtext("a:summary", default="", namespaces=ATOM_NS)
        or entry.findtext("{http://www.w3.org/2005/Atom}summary")
        or ""
    ).strip()
    content_el = entry.find("a:content", ATOM_NS) or entry.find(
        "{http://www.w3.org/2005/Atom}content"
    )
    content = ""
    if content_el is not None:
        content = (
            "".join(content_el.itertext())
            if list(content_el)
            else (content_el.text or "")
        )
    published = (
        entry.findtext("a:updated", default="", namespaces=ATOM_NS)
        or entry.findtext("a:published", default="", namespaces=ATOM_NS)
        or entry.findtext("{http://www.w3.org/2005/Atom}updated")
        or entry.findtext("{http://www.w3.org/2005/Atom}published")
        or ""
    ).strip()
    link = ""
    for link_el in entry.findall("a:link", ATOM_NS) or entry.findall(
        "{http://www.w3.org/2005/Atom}link"
    ):
        href = link_el.get("href") or ""
        rel = (link_el.get("rel") or "alternate").lower()
        if href and rel in ("alternate", "self", ""):
            link = href
            break
    nid = (
        entry.findtext("a:id", default="", namespaces=ATOM_NS)
        or entry.findtext("{http://www.w3.org/2005/Atom}id")
        or link
        or title[:60]
    ).strip()
    desc = (summary or content or title)[:2000]
    blob = f"{title} {summary} {content}"
    return title, desc, published, link, nid


def _parse_atom_bytes(
    body: bytes,
    *,
    cutoff: str,
    seen: Set[str],
) -> Tuple[List[Dict[str, Any]], Optional[str], int]:
    """Parse one Atom document. Returns (rows, next_href, entry_count)."""
    results: List[Dict[str, Any]] = []
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        return [], None, 0
    next_href = None
    for link in root.findall("a:link", ATOM_NS) or root.findall(
        "{http://www.w3.org/2005/Atom}link"
    ):
        if (link.get("rel") or "").lower() == "next" and link.get("href"):
            next_href = link.get("href")
            break
    entries = root.findall("a:entry", ATOM_NS) or root.findall(
        "{http://www.w3.org/2005/Atom}entry"
    )
    for entry in entries:
        title, desc, published, link, nid = _entry_text(entry)
        pub_day = (published or "")[:10]
        if pub_day and pub_day < cutoff:
            continue
        blob = f"{title} {desc}".lower()
        if not _match_vehicle(blob):
            continue
        key = (nid or link or title).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        cpv = ""
        m = ES_CPV_RE.search(blob)
        if m:
            cpv = m.group(1)
        results.append(
            {
                "Source": "🇪🇸 ES-PLACSP",
                "Source Notice ID": nid[:120],
                "Lifecycle": "",
                "Notice Type": "",
                "Procedure Type": "",
                "Buyer Type": "",
                "Score": "",
                "FleetSize": "",
                "Title": title or nid[:80],
                "Buyer": "",
                "CPV Code": cpv,
                "CPV Desc": "",
                "Description": desc[:500],
                "Est. Value": "",
                "Currency": "EUR",
                "Published": pub_day,
                "Deadline": "",
                "Country": "Spain",
                "Country Code": "ESP",
                "URL": link or "https://contrataciondelsectorpublico.gob.es/",
            }
        )
    return results, next_href, len(entries)


def _headers() -> Dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "application/atom+xml, application/xml, text/xml, */*",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Referer": (
            "https://www.hacienda.gob.es/es-ES/GobiernoAbierto/"
            "Datos%20Abiertos/Paginas/LicitacionesAgregacion.aspx"
        ),
    }


def fetch_spain_placsp(
    session: Optional[requests.Session] = None,
    from_dt: Optional[datetime] = None,
    *,
    max_pages: int = 40,
    also_aggregated: bool = True,
    errors: Optional[Dict[str, Optional[str]]] = None,
) -> List[Dict[str, Any]]:
    """National ES notices via PLACSP Atom syndication (vehicle stem / CPV gate).

    Walks atom:link@rel=next until lookback cutoff or max_pages.
    On WAF deny sets CODE_READY-style error string (caller maps health).
    """
    print("\n[ES PLACSP] Fetching Atom syndication (vehicle stem/CPV, follow next)...")
    own = session is None
    session = session or requests.Session()
    from_dt = from_dt or datetime.now(timezone.utc)
    cutoff = from_dt.strftime("%Y-%m-%d")
    results: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    last_err: Optional[str] = None
    pages_ok = 0
    entries_scanned = 0

    seeds = list(ES_PLACSP_ATOM_SEEDS)
    if also_aggregated:
        seeds.extend(ES_PLACSP_ATOM_AGG)

    try:
        started = False
        for seed in seeds:
            if started and results:
                break  # one channel family is enough when live
            url: Optional[str] = seed
            for page in range(max_pages):
                if not url:
                    break
                try:
                    resp = session.get(url, headers=_headers(), timeout=90)
                except Exception as exc:
                    last_err = str(exc)
                    print(f"  [ES PLACSP] page {page}: {exc}")
                    break
                body = resp.content or b""
                if _waf_body(body):
                    last_err = (
                        "WAF_BLOCKED — PLACSP Atom denied from this runner "
                        "(contrataciondelestado.es / contrataciondelsectorpublico.gob.es); "
                        "official syndication still documented — CODE_READY"
                    )
                    print(f"  [ES PLACSP] page {page}: WAF deny (HTTP {resp.status_code})")
                    break
                if resp.status_code != 200:
                    last_err = f"HTTP {resp.status_code}"
                    print(f"  [ES PLACSP] page {page}: {last_err}")
                    break
                if b"<entry" not in body[:20000].lower() and b":entry" not in body[:20000].lower():
                    last_err = f"no Atom entries (ctype={(resp.headers.get('Content-Type') or '')[:40]})"
                    print(f"  [ES PLACSP] page {page}: {last_err}")
                    break
                rows, next_href, n_entries = _parse_atom_bytes(body, cutoff=cutoff, seen=seen)
                entries_scanned += n_entries
                pages_ok += 1
                started = True
                results.extend(rows)
                print(
                    f"  [ES PLACSP] page {page}: entries={n_entries} "
                    f"hits+={len(rows)} url=…/{url.split('/')[-1][:60]}"
                )
                # Stop walking when this page's newest entries are all older than cutoff
                # (next pages are older chronologically in PLACSP chain).
                if n_entries and not rows:
                    # Still may have newer non-vehicle; check min date on page
                    try:
                        root = ET.fromstring(body)
                        dates = []
                        for e in root.findall("a:entry", ATOM_NS) or []:
                            d = (
                                e.findtext("a:updated", default="", namespaces=ATOM_NS)
                                or ""
                            )[:10]
                            if d:
                                dates.append(d)
                        if dates and max(dates) < cutoff:
                            print(f"  [ES PLACSP] reached lookback floor ({max(dates)} < {cutoff})")
                            url = None
                            break
                    except ET.ParseError:
                        pass
                url = next_href
                if not url:
                    break
            if pages_ok:
                break  # do not also walk aggregated unless primary failed

        if results:
            last_err = None
        elif not last_err:
            last_err = (
                f"zero vehicle-ish Atom rows "
                f"(pages={pages_ok} entries≈{entries_scanned})"
            )
        print(
            f"[ES PLACSP] Matches: {len(results)} "
            f"(pages={pages_ok} entries≈{entries_scanned})"
        )
    except Exception as exc:
        last_err = str(exc)
        print(f"  [ES PLACSP] exception: {exc}")
    finally:
        if own:
            session.close()

    if errors is not None:
        errors["Spain PLACSP"] = last_err
    return results


def fetch_spain_placsp_zip_month(
    session: Optional[requests.Session] = None,
    *,
    yyyymm: str,
    from_dt: Optional[datetime] = None,
    errors: Optional[Dict[str, Optional[str]]] = None,
) -> List[Dict[str, Any]]:
    """Optional heavy path: one monthly ZIP (often 100MB+). Prefer Atom walk."""
    print(f"\n[ES PLACSP ZIP] Fetching monthly {yyyymm}…")
    own = session is None
    session = session or requests.Session()
    from_dt = from_dt or datetime.now(timezone.utc)
    cutoff = from_dt.strftime("%Y-%m-%d")
    url = (
        "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/"
        f"licitacionesPerfilesContratanteCompleto3_{yyyymm}.zip"
    )
    results: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    last_err: Optional[str] = None
    try:
        resp = session.get(url, headers=_headers(), timeout=300)
        body = resp.content or b""
        if _waf_body(body):
            last_err = "WAF_BLOCKED — monthly ZIP denied — CODE_READY"
        elif resp.status_code != 200 or body[:2] != b"PK":
            last_err = f"HTTP {resp.status_code} or non-ZIP ({len(body)} bytes)"
        else:
            with zipfile.ZipFile(io.BytesIO(body)) as zf:
                for name in zf.namelist():
                    if not name.lower().endswith(".atom"):
                        continue
                    rows, _, _ = _parse_atom_bytes(
                        zf.read(name), cutoff=cutoff, seen=seen
                    )
                    results.extend(rows)
            print(f"[ES PLACSP ZIP] {yyyymm}: matches={len(results)} zip={len(body)} bytes")
    except Exception as exc:
        last_err = str(exc)
        print(f"  [ES PLACSP ZIP] {exc}")
    finally:
        if own:
            session.close()
    if errors is not None and last_err:
        errors["Spain PLACSP"] = last_err
    elif errors is not None and results:
        errors["Spain PLACSP"] = None
    return results


if __name__ == "__main__":
    from datetime import timedelta

    err: Dict[str, Optional[str]] = {}
    lookback = datetime.now(timezone.utc) - timedelta(days=30)
    rows = fetch_spain_placsp(from_dt=lookback, errors=err)
    print("error:", err.get("Spain PLACSP"))
    print("sample titles:")
    for r in rows[:8]:
        print(" -", (r.get("Title") or "")[:100])
