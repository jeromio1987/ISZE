# -*- coding: utf-8 -*-
"""Read the vehicle list in the tender documents (2026-10-01, on Jerome's go).

The fleet-brand gate (`isze_core_v3.apply_fleet_brand_gate`) parks a repair / maintenance /
parts tender that does not name Isuzu on Watch with "check the vehicle list in the tender
documents". This step does that check by machine:

  1. take the tenders in that group (same selection as section 1b of the tender review)
  2. find each notice's procurement documents from the links already in the feed
     (TED notice XML, Romanian SEAP, Belgian BOSA, Irish eTenders, Doffin, Portuguese DRE /
     acinGov, Slovenian e-narocanje)
  3. download ONLY what the portal publishes to anonymous visitors. No login, no account,
     no CAPTCHA. robots.txt is checked per host before every fetch; a host that disallows
     it is recorded as "blocked by robots.txt" and skipped. A portal that needs registration
     is recorded as "needs registration" and skipped.
  4. extract text (PDF per page, DOCX paragraphs + table rows, XLSX/XLS rows, DOC via
     antiword, ZIP members, signed .p7s/.p7m envelopes) and look for vehicle brands with the
     same word-bounded Isuzu patterns the scorer uses (`isze_core_v3._BRAND_STRICT_RE`), plus
     a word-bounded list of other makes used only as evidence that a vehicle list exists
  5. verdict per tender: isuzu_in_fleet / isuzu_mentioned_outside_list / not_in_fleet /
     no_vehicle_list_found / documents_not_available
  6. with --apply: attach the result to the feed as `fleet_doc_check` and re-run the gate.
     The gate re-scores an Isuzu-confirmed tender through the normal brand-signal points
     (the same +40 fit / +10 econ a brand word in the notice earns) and derive_decision;
     nothing is hand-set. Every other verdict stays Watch with the reason updated.

Evidence: tender_docs/<notice id>/{files/, text/, manifest.json}
Summary:  tender_docs/tender_doc_check_summary.json

Idempotent: a document already in a manifest is not downloaded again (unless --refresh);
the feed is only written, after a timestamped backup, when its content changes.

    python tender_doc_reader.py                 # read + report, feed untouched
    python tender_doc_reader.py --apply         # read + write the result into the feed
    python tender_doc_reader.py --only 7a368d0302e4 --refresh
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.robotparser
import uuid
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import isze_core_v3 as core  # noqa: E402
import build_rm_digest as digest  # noqa: E402  (same selection as the tender review)

FEED = ROOT / "01_data" / "14_dashboards" / "tender_data.json"
DOCS = HERE / "tender_docs"
SUMMARY = DOCS / "tender_doc_check_summary.json"

UA = "Mozilla/5.0 (compatible; ISZE-tender-doc-reader/1.0; public tender documents only)"
ROBOTS_AGENT = "ISZE-tender-doc-reader"
MAX_FILE_BYTES = 80 * 1024 * 1024
HOST_PAUSE_S = 1.0
TIMEOUT = 60

# ---------------------------------------------------------------------------
# Brand matching
# ---------------------------------------------------------------------------
# Isuzu: exactly the scorer's word-bounded patterns (no "d max" inside "...und max",
# no "Bond-Max"). Other makes: word-bounded, used only to show that a vehicle list exists
# and what is in it. Short or ambiguous names are case-sensitive (MAN, DAF, VW, BMW, SEAT,
# LADA) so "man", "seat" or the Romanian "ladă" do not count.
ISUZU_RE = core._BRAND_STRICT_RE

OTHER_BRAND_RE: Dict[str, re.Pattern] = {
    "Ford": re.compile(r"(?i)\bford\b"),
    "Mercedes-Benz": re.compile(r"(?i)\bmercedes(?:[- ]benz)?\b"),
    "Unimog": re.compile(r"(?i)\bunimog\b"),
    "Volkswagen": re.compile(r"(?i)\bvolkswagen\b|\bVW\b"),
    "Renault": re.compile(r"(?i)\brenault\b"),
    "Dacia": re.compile(r"(?i)\bdacia\b"),
    "Peugeot": re.compile(r"(?i)\bpeugeot\b"),
    "Citroen": re.compile(r"(?i)\bcitro[eë]n\b"),
    "Opel": re.compile(r"(?i)\bopel\b"),
    "Fiat": re.compile(r"(?i)\bfiat\b"),
    "Iveco": re.compile(r"(?i)\biveco\b"),
    "Toyota": re.compile(r"(?i)\btoyota\b"),
    "Nissan": re.compile(r"(?i)\bnissan\b"),
    "Mitsubishi": re.compile(r"(?i)\bmitsubishi\b"),
    "Fuso": re.compile(r"(?i)\bfuso\b"),
    "Hyundai": re.compile(r"(?i)\bhyundai\b"),
    "Kia": re.compile(r"(?i)\bkia\b"),
    "Skoda": re.compile(r"(?i)\b[sš]koda\b"),
    "Suzuki": re.compile(r"(?i)\bsuzuki\b"),
    "Mazda": re.compile(r"(?i)\bmazda\b"),
    "Subaru": re.compile(r"(?i)\bsubaru\b"),
    "Volvo": re.compile(r"(?i)\bvolvo\b"),
    "Scania": re.compile(r"(?i)\bscania\b"),
    "DAF": re.compile(r"\bDAF\b"),
    "MAN": re.compile(r"\bMAN\b(?![-/])"),
    "Land Rover": re.compile(r"(?i)\bland[- ]?rover\b"),
    "Jeep": re.compile(r"(?i)\bjeep\b"),
    "SsangYong/KGM": re.compile(r"(?i)\bssang ?yong\b|\bKGM\b"),
    "Mahindra": re.compile(r"(?i)\bmahindra\b"),
    "Hino": re.compile(r"(?i)\bhino\b"),
    "Tesla": re.compile(r"(?i)\btesla\b"),
    "BMW": re.compile(r"\bBMW\b"),
    "Audi": re.compile(r"(?i)\baudi\b"),
    "SEAT": re.compile(r"\bSEAT\b"),
    "LADA": re.compile(r"\bLADA\b|\bLada Niva\b"),
    "Great Wall": re.compile(r"(?i)\bgreat wall\b"),
    "Piaggio": re.compile(r"(?i)\bpiaggio\b"),
    "Multicar": re.compile(r"(?i)\bmulticar\b"),
    "Aebi": re.compile(r"(?i)\baebi\b"),
    "Honda": re.compile(r"(?i)\bhonda\b"),
    "Chevrolet": re.compile(r"(?i)\bchevrolet\b"),
    "Dodge": re.compile(r"(?i)\bdodge\b"),
    "Maxus": re.compile(r"(?i)\bmaxus\b"),
}

# Words that mark a vehicle list row (make / model / plate / year / VIN), several languages.
LIST_MARKER_RE = re.compile(
    r"(?i)\b(marc[aă]|marque|merk|marke|make|modell?|model[eo]?|modèle|tip(?:ul)?|type|"
    r"[îi]nmatricul\w*|immatricul\w*|registrering\w*|reg\.? ?nr|kenteken|kennzeichen|"
    r"registration|matr[ií]cula|VIN|[sș]asiu|chassis|an(?:ul)? (?:de )?fabrica\w*|"
    r"year of manufacture|årsmodell|cilindree|capacitate cilindric\w*|kilometraj|"
    r"parc(?:ul)? auto|vehicle list|lista (?:autovehiculelor|vehiculelor|mijloacelor)|"
    r"liste des véhicules|kjøretøyliste|wagenpark|viaturas?|tonaj|masa maxim\w*)\b"
)
PLATE_RE = re.compile(r"\b[A-Z]{1,2}[- ]?\d{2,3}[- ]?[A-Z]{2,3}\b")
YEAR_RE = re.compile(r"\b(19[89]\d|20[0-2]\d)\b")
VIN_RE = re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b")

VERDICT_LABELS = {
    "isuzu_in_fleet": "Isuzu in the vehicle list of the tender documents",
    "isuzu_mentioned_outside_list": "Isuzu named in the tender documents, but not in a vehicle list",
    "not_in_fleet": "Vehicle list found in the tender documents: no Isuzu in it",
    "no_vehicle_list_found": "Tender documents read: no vehicle list in them",
    "documents_not_available": "Tender documents not read",
}


def ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def safe_name(name: str, limit: int = 110) -> str:
    name = re.sub(r"[^\w .()+-]", "_", name or "file", flags=re.UNICODE).strip(" .")
    if len(name) > limit:
        stem, dot, ext = name.rpartition(".")
        name = (stem[: limit - len(ext) - 1] + "." + ext) if dot and len(ext) <= 6 else name[:limit]
    return name or "file"


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


# ---------------------------------------------------------------------------
# Polite HTTP: robots.txt per host, pause per host, size cap
# ---------------------------------------------------------------------------
class Fetcher:
    def __init__(self) -> None:
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": UA})
        self.robots: Dict[str, Optional[urllib.robotparser.RobotFileParser]] = {}
        self.last: Dict[str, float] = {}
        self.log: List[str] = []

    def allowed(self, url: str) -> bool:
        p = urllib.parse.urlsplit(url)
        host = f"{p.scheme}://{p.netloc}"
        if host not in self.robots:
            rp: Optional[urllib.robotparser.RobotFileParser] = urllib.robotparser.RobotFileParser()
            try:
                r = self.s.get(host + "/robots.txt", timeout=20, allow_redirects=True)
                ctype = (r.headers.get("content-type") or "").lower()
                if r.status_code == 200 and "html" not in ctype and "user-agent" in r.text.lower():
                    rp.parse(r.text.splitlines())
                else:
                    rp = None  # no robots.txt published (404 / HTML page) -> no rules
            except Exception:
                rp = None
            self.robots[host] = rp
        rp = self.robots[host]
        return True if rp is None else rp.can_fetch(ROBOTS_AGENT, url)

    def _pause(self, url: str) -> None:
        host = urllib.parse.urlsplit(url).netloc
        wait = HOST_PAUSE_S - (time.time() - self.last.get(host, 0))
        if wait > 0:
            time.sleep(wait)
        self.last[host] = time.time()

    def get(self, url: str, **kw) -> requests.Response:
        if not self.allowed(url):
            raise RobotsBlocked(url)
        self._pause(url)
        kw.setdefault("timeout", TIMEOUT)
        r = self.s.get(url, stream=True, **kw)
        size = int(r.headers.get("content-length") or 0)
        if size > MAX_FILE_BYTES:
            r.close()
            raise TooLarge(f"{size} bytes")
        buf = io.BytesIO()
        for chunk in r.iter_content(256 * 1024):
            buf.write(chunk)
            if buf.tell() > MAX_FILE_BYTES:
                r.close()
                raise TooLarge(f">{MAX_FILE_BYTES} bytes")
        r._content = buf.getvalue()
        r._content_consumed = True
        self.log.append(f"GET {r.status_code} {url}")
        return r

    def post(self, url: str, **kw) -> requests.Response:
        if not self.allowed(url):
            raise RobotsBlocked(url)
        self._pause(url)
        kw.setdefault("timeout", TIMEOUT)
        r = self.s.post(url, **kw)
        self.log.append(f"POST {r.status_code} {url}")
        return r


class RobotsBlocked(Exception):
    pass


class TooLarge(Exception):
    pass


def filename_from(r: requests.Response, fallback: str) -> str:
    cd = r.headers.get("content-disposition") or ""
    m = re.search(r"filename\*\s*=\s*(?:UTF-8|utf-8)''([^;]+)", cd)
    if m:
        return urllib.parse.unquote(m.group(1).strip().strip('"'))
    m = re.search(r'filename\s*=\s*"?([^";]+)"?', cd)
    if m:
        raw = m.group(1).strip()
        try:
            raw = raw.encode("latin-1").decode("utf-8")
        except Exception:
            pass
        return raw
    return fallback


# ---------------------------------------------------------------------------
# Portal resolvers. Each returns (documents, notes). A document is
#   {"url", "name", "fetch": callable -> (bytes, filename)}  or a status-only entry.
# ---------------------------------------------------------------------------
class Doc(dict):
    pass


def doc_direct(f: Fetcher, url: str, name: str = "", method: str = "GET", **kw) -> Doc:
    def fetch():
        r = f.get(url, **kw) if method == "GET" else f.post(url, **kw)
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}: {ws(r.text[:160]) if r.text else ''}")
        return r.content, filename_from(r, name or url.rstrip("/").rsplit("/", 1)[-1])
    return Doc(url=url, name=name, fetch=fetch)


def status_entry(url: str, status: str, note: str) -> Doc:
    return Doc(url=url, name="", status=status, note=note)


def resolve_ted(f: Fetcher, url: str, nid: str) -> Tuple[List[Doc], List[str]]:
    m = re.search(r"(\d{4,8}-\d{4})", url)
    tid = m.group(1) if m else nid
    xml_url = f"https://ted.europa.eu/en/notice/{tid}/xml"
    docs: List[Doc] = [doc_direct(f, xml_url, f"TED_notice_{tid}.xml")]
    docs[0]["kind"] = "notice"
    notes: List[str] = []
    try:
        r = f.get(xml_url)
        uris = []
        for tag in ("URI",):
            uris += re.findall(r"<cbc:%s[^>]*>([^<]+)</cbc:%s>" % (tag, tag), r.text)
        seen = set()
        for u in uris:
            u = u.strip().replace("&amp;", "&")
            if u in seen:
                continue
            seen.add(u)
            sub, sub_notes = resolve_url(f, u, nid, from_ted=True)
            docs += sub
            notes += sub_notes
        if not uris:
            notes.append("TED notice names no document link")
    except RobotsBlocked:
        notes.append("TED blocked by robots.txt")
    except Exception as exc:
        notes.append(f"TED notice XML not fetched: {exc}")
    return docs, notes


SEAP = "https://www.e-licitatie.ro/"


def resolve_seap(f: Fetcher, url: str, nid: str) -> Tuple[List[Doc], List[str]]:
    m = re.search(r"c-notice/(?:v2/view/)?(\d{6,})", url)
    if not m:
        return [status_entry(url, "portal_not_supported", "SEAP link without a notice id")], []
    cid = m.group(1)
    ref = f"https://www.e-licitatie.ro/pub/notices/c-notice/{cid}/view"
    hdr = {"Referer": ref, "Accept": "application/json, text/plain, */*"}
    listing = None
    err = ""
    for st in (2, 17, 3, 1, 9, 10):
        try:
            r = f.get(SEAP + "api-pub/NoticeCommon/GetDfNoticeSectionFiles/",
                      params={"initNoticeId": cid, "sysNoticeTypeId": st}, headers=hdr)
            if r.status_code == 200:
                listing = r.json()
                break
            err = f"HTTP {r.status_code} {ws(r.text[:120])}"
        except Exception as exc:
            err = str(exc)
    if listing is None:
        return [status_entry(ref, "listing_failed", f"SEAP document list not returned ({err})")], []
    docs: List[Doc] = []
    for d in listing.get("dfNoticeDocs") or []:
        durl = SEAP + d["noticeDocumentUrl"]

        def fetch(durl=durl, name=d.get("noticeDocumentName") or ""):
            f.post(durl, headers=hdr)  # the portal's own "verify file" call before download
            r = f.get(durl, headers=hdr)
            if r.status_code != 200:
                raise RuntimeError(f"HTTP {r.status_code}: {ws(r.text[:160])}")
            return r.content, filename_from(r, name)
        # The download link is a fresh token on every listing; the document code is stable,
        # so the code (on the public notice page) is what identifies the file in the cache.
        docs.append(Doc(url=f"{ref}#doc={d.get('noticeDocumentCode') or d['noticeDocumentUrl']}",
                        name=d.get("noticeDocumentName") or "", fetch=fetch))
    skipped = len(listing.get("duaeDocs") or [])
    notes = [f"SEAP notice {cid}: {len(docs)} documentation files listed"
             + (f"; {skipped} ESPD/DUAE request XML not downloaded (no vehicle data)" if skipped else "")]
    return docs, notes


def resolve_be(f: Fetcher, url: str, nid: str) -> Tuple[List[Doc], List[str]]:
    m = re.search(r"publication-workspaces/([0-9a-f-]{36})", url)
    if not m:
        return [status_entry(url, "portal_not_supported", "BOSA link without a workspace id")], []
    wsid = m.group(1)
    import tender_scraper_v3 as ts  # public SPA client, the same one the scraper uses

    cid, sec, err = ts._be_load_spa_client_credentials(f.s)
    tok, err2 = ts._be_get_token(f.s, cid, sec) if not err else (None, err)
    if not tok:
        return [status_entry(url, "listing_failed", f"BOSA public token not issued: {err2}")], []
    api = "https://www.publicprocurement.be/api/dos/"

    def H():
        return {"Authorization": "Bearer " + tok, "Accept": "application/json",
                "BelGov-Trace-Id": str(uuid.uuid4())}
    r = f.get(api + f"publication-workspaces/{wsid}/documents", headers=H())
    if r.status_code != 200:
        return [status_entry(url, "listing_failed", f"BOSA documents HTTP {r.status_code}")], []
    docs: List[Doc] = []
    skipped_espd = 0
    for d in r.json():
        vers = d.get("versions") or []
        if not vers:
            continue
        if d.get("type") == "ESPD_REQUEST":  # generated ESPD form: no vehicle data, not served
            skipped_espd += 1
            continue
        v = vers[-1]
        name = ((v.get("document") or {}).get("originalFileName")
                or ((d.get("titles") or [{}])[0].get("text")) or v["id"])

        def fetch(vid=v["id"], name=name):
            rr = f.get(api + f"publication-workspace-document-versions/{vid}/download-url", headers=H())
            if rr.status_code != 200:
                raise RuntimeError(f"download-url HTTP {rr.status_code}")
            body = rr.text.strip()
            try:
                j = rr.json()
                link = j if isinstance(j, str) else (j.get("value") or j.get("url") or j.get("downloadUrl") or "")
            except Exception:
                link = body.strip('"')
            fr = f.get(link)
            if fr.status_code != 200:
                raise RuntimeError(f"file HTTP {fr.status_code}")
            return fr.content, name
        docs.append(Doc(url=f"{url}#doc={v['id']}", name=name, fetch=fetch))
    # The workspace also carries the full eForms notice text: read it as a document.
    def fetch_notice(wsid=wsid):
        rr = f.get(api + f"publication-workspaces/{wsid}", headers=H())
        xmls = re.findall(r'"xmlContent":"((?:[^"\\]|\\.)*)"', rr.text)
        return (json.loads('"' + xmls[0] + '"').encode("utf-8") if xmls else rr.content), f"BOSA_notice_{wsid[:8]}.xml"
    docs.append(Doc(url=url + "#notice", name="BOSA notice", fetch=fetch_notice, kind="notice"))
    notes = [f"BOSA workspace {wsid[:8]}: {len(docs) - 1} documents listed"
             + (f"; {skipped_espd} generated ESPD form(s) not downloaded" if skipped_espd else "")]
    # Documents the notice says are kept on another platform.
    try:
        xml, _ = fetch_notice()
        for u in sorted(set(re.findall(r"<cbc:URI>([^<]+)</cbc:URI>", xml.decode("utf-8", "replace")))):
            if wsid in u:
                continue
            sub, sn = resolve_url(f, u.replace("&amp;", "&"), nid, from_ted=True)
            docs += sub
            notes += sn
    except Exception as exc:
        notes.append(f"BOSA notice links not read: {exc}")
    return docs, notes


def resolve_doffin(f: Fetcher, url: str, nid: str) -> Tuple[List[Doc], List[str]]:
    m = re.search(r"notices/(\d{4}-\d+)", url)
    did = m.group(1) if m else nid
    api = f"https://api.doffin.no/webclient/api/v2/notices-api/notices/{did}"
    docs: List[Doc] = [doc_direct(f, api, f"doffin_{did}.json", headers={"Accept": "application/json"})]
    docs[0]["kind"] = "notice"
    notes: List[str] = []
    try:
        j = f.get(api, headers={"Accept": "application/json"}).json()
        notes.append(f"Doffin {did}: {j.get('noticeType')}")
        cu = j.get("competitionDocsUrl")
        if cu:
            sub, sn = resolve_url(f, cu, nid)
            docs += sub
            notes += sn
        elif str(j.get("noticeType") or "").startswith("ANNOUNCEMENT_OF_CONCLUSION"):
            notes.append("award notice: no competition documents are published with it")
        else:
            notes.append("Doffin gives no competition-documents link")
    except Exception as exc:
        notes.append(f"Doffin notice not fetched: {exc}")
    return docs, notes


def resolve_ie(f: Fetcher, url: str, nid: str) -> Tuple[List[Doc], List[str]]:
    m = re.search(r"resourceId=(\d+)", url)
    if not m:
        return [status_entry(url, "portal_not_supported", "eTenders link without resourceId")], []
    rid = m.group(1)
    lst = f"https://www.etenders.gov.ie/epps/cft/listContractDocuments.do?resourceId={rid}"
    r = f.get(lst)
    ids = list(dict.fromkeys(re.findall(r"downloadDocForAnonymous\('(\d+)'\)", r.text)))
    docs = [doc_direct(f, f"https://www.etenders.gov.ie/epps/cft/downloadContractDocument.do?documentId={d}&resourceId={rid}",
                       f"ie_{d}") for d in ids]
    return docs, [f"eTenders {rid}: {len(ids)} documents offered to anonymous visitors"]


def resolve_pt_dre(f: Fetcher, url: str, nid: str) -> Tuple[List[Doc], List[str]]:
    docs: List[Doc] = [doc_direct(f, url, url.rsplit("/", 1)[-1])]
    docs[0]["kind"] = "notice"
    notes: List[str] = []
    try:
        import fitz
        r = f.get(url)
        d = fitz.open(stream=r.content, filetype="pdf")
        text = "\n".join(p.get_text() for p in d)
        links = sorted(set(re.findall(r"https?://\S+", text)))
        for u in links:
            u = u.rstrip(").,;")
            if "donwloadProcedurePiece" in u or "downloadProcedurePiece" in u:
                docs.append(doc_direct(f, u, "pecas_procedimento.zip"))
            elif any(k in u for k in ("vortal", "saphety", "anogov", "comprasnaturais", "ebuyforum")):
                docs.append(status_entry(u, "needs_registration",
                                         "platform link with no public download piece in the notice"))
        if len(docs) == 1:
            notes.append("DRE notice names no public document download")
    except Exception as exc:
        notes.append(f"DRE notice not read: {exc}")
    return docs, notes


def resolve_mercell(f: Fetcher, url: str, nid: str) -> Tuple[List[Doc], List[str]]:
    try:
        r = f.get(url, allow_redirects=True)
        code = r.status_code
    except RobotsBlocked:
        return [status_entry(url, "blocked_robots", "Mercell disallows this path in robots.txt")], []
    except Exception as exc:
        code = str(exc)
    if code != 200:
        return [status_entry(url, "unreachable",
                             f"Mercell permalink answers HTTP {code}; Mercell shows documents only "
                             "after a supplier login, so it was not pursued further")], []
    shown = "Show interest" in r.text or "Sign in" in r.text
    return [status_entry(url, "needs_registration",
                         "Mercell lists the files but gives access only after 'Show interest' (supplier sign-in)"
                         if shown else "Mercell: documents only after supplier sign-in")], []


def resolve_url(f: Fetcher, url: str, nid: str, from_ted: bool = False) -> Tuple[List[Doc], List[str]]:
    u = url.strip()
    host = urllib.parse.urlsplit(u).netloc.lower()
    try:
        if not f.allowed(u):
            return [status_entry(u, "blocked_robots", f"{host} disallows automated access in robots.txt")], []
        if "ted.europa.eu" in host and not from_ted:
            return resolve_ted(f, u, nid)
        if "e-licitatie.ro" in host:
            if re.search(r"c-notice/(?:v2/view/)?\d{6,}", u):
                return resolve_seap(f, u, nid)
            return [], [f"generic SEAP link {u} (no notice id) - covered by the SEAP twin if one exists"]
        if "publicprocurement.be" in host:
            return resolve_be(f, u, nid)
        if "doffin.no" in host:
            return resolve_doffin(f, u, nid)
        if "etenders.gov.ie" in host and "listContractDocuments" in u:
            return resolve_ie(f, u, nid)
        if "etenders.gov.ie" in host:
            return [], []  # viewTenders endpoint duplicate of the documents list
        if "diariodarepublica.pt" in host:
            return resolve_pt_dre(f, u, nid)
        if "mercell.com" in host:
            return resolve_mercell(f, u, nid)
        if "enarocanje.si" in host and "/api/datoteka/" in u:
            return [doc_direct(f, u, "")], []
        if "ejn.gov.si" in host:
            return [], []  # the bidder portal page; the file link is read from TED
        if "3p.eu" in host:
            return [status_entry(u, "portal_not_supported",
                                 "3P Cloud asks for a country choice and cookie consent before it shows "
                                 "documents; not automated, open by hand")], []
        if "boamp.fr" in host:
            return [status_entry(u, "blocked_robots",
                                 "BOAMP serves the notice and buyer-profile link only through /api/, "
                                 "which robots.txt disallows for automated agents")], []
        if re.search(r"\.(pdf|zip|docx?|xlsx?|rtf|odt|ods)(\?|$)", u, re.I):
            return [doc_direct(f, u, "")], []
        if from_ted and re.match(r"https?://[^/]+/?$", u):
            return [], []  # a bare portal home page, not a document link
        return [status_entry(u, "portal_not_supported", "document portal not supported by this reader")], []
    except RobotsBlocked:
        return [status_entry(u, "blocked_robots", f"{host} disallows automated access in robots.txt")], []
    except Exception as exc:
        return [status_entry(u, "listing_failed", f"{type(exc).__name__}: {exc}")], []


# ---------------------------------------------------------------------------
# Text extraction -> list of units (location, text, is_row)
# ---------------------------------------------------------------------------
def ber_octets(data: bytes) -> bytes:
    """Largest OCTET STRING content in a BER/DER blob (the signed content of a .p7s/.p7m)."""
    best = b""

    def walk(buf: bytes, pos: int, end: int, depth: int) -> None:
        nonlocal best
        while pos < end and depth < 12:
            tag = buf[pos]
            pos += 1
            if tag & 0x1F == 0x1F:
                while pos < end and buf[pos] & 0x80:
                    pos += 1
                pos += 1
            if pos >= end:
                return
            ln = buf[pos]
            pos += 1
            indefinite = False
            if ln == 0x80:
                indefinite = True
                length = None
            elif ln & 0x80:
                n = ln & 0x7F
                length = int.from_bytes(buf[pos:pos + n], "big")
                pos += n
            else:
                length = ln
            constructed = bool(tag & 0x20)
            if tag == 0x00 and ln == 0x00:
                return
            if constructed:
                sub_end = end if indefinite else min(end, pos + length)
                if tag == 0x24:  # constructed OCTET STRING: concatenate chunks
                    chunks = []
                    p = pos
                    while p < sub_end:
                        if buf[p] == 0 and p + 1 < sub_end and buf[p + 1] == 0:
                            p += 2
                            break
                        t2 = buf[p]
                        l2 = buf[p + 1]
                        p += 2
                        if l2 & 0x80:
                            n = l2 & 0x7F
                            l2 = int.from_bytes(buf[p:p + n], "big")
                            p += n
                        if t2 == 0x04:
                            chunks.append(buf[p:p + l2])
                        p += l2
                    blob = b"".join(chunks)
                    if len(blob) > len(best):
                        best = blob
                    pos = p if indefinite else sub_end
                    continue
                walk(buf, pos, sub_end, depth + 1)
                if indefinite:
                    return  # cannot know where an indefinite block ends without full parse
                pos = sub_end
            else:
                if length is None:
                    return
                if tag == 0x04 and length > len(best):
                    best = buf[pos:pos + length]
                pos += length

    try:
        walk(data, 0, len(data), 0)
    except Exception:
        pass
    if not best:
        a, b = data.find(b"%PDF"), data.rfind(b"%%EOF")
        if a >= 0 and b > a:
            best = data[a:b + 5]
    return best


def sniff_ext(data: bytes, name: str) -> str:
    if data[:4] == b"%PDF":
        return ".pdf"
    if data[:2] == b"PK":
        try:
            names = zipfile.ZipFile(io.BytesIO(data)).namelist()
            if "word/document.xml" in names:
                return ".docx"
            if "xl/workbook.xml" in names:
                return ".xlsx"
            if "content.xml" in names:
                return ".odt" if any(n.endswith("styles.xml") for n in names) and name.lower().endswith(".odt") else ".odf"
            return ".zip"
        except Exception:
            return ".zip"
    if data[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        low = name.lower()
        return ".xls" if low.endswith((".xls", ".xlt")) else ".doc"
    if data[:5] == b"{\\rtf":
        return ".rtf"
    if data[:1] == b"\x30" and name.lower().endswith((".p7s", ".p7m")):
        return ".p7s"
    head = data[:400].lstrip()
    if head[:1] == b"<":
        return ".xml" if head[:5] == b"<?xml" or b"xmlns" in head else ".html"
    if head[:1] in (b"{", b"["):
        return ".json"
    low = name.lower()
    for ext in (".p7s", ".p7m", ".txt", ".csv"):
        if low.endswith(ext):
            return ext
    return ""


def strip_markup(s: str) -> str:
    s = re.sub(r"(?s)<(script|style)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    return s


OCR_CACHE = DOCS / "_ocr_cache"
OCR_MAX_PAGES = 300
_OCR_ENGINE: Any = None


def ocr_pages(doc: Any, pages: List[int], sha: str) -> Dict[int, str]:
    """Windows' built-in OCR (en-US engine, via winsdk) on pages that have no text layer.
    Cached per document hash and page, so a re-run does not OCR again. Returns {} when
    the OCR engine is not available on this machine."""
    global _OCR_ENGINE
    out: Dict[int, str] = {}
    todo = []
    OCR_CACHE.mkdir(parents=True, exist_ok=True)
    for i in pages[:OCR_MAX_PAGES]:
        c = OCR_CACHE / f"{sha[:16]}_p{i}.txt"
        if c.exists():
            out[i] = c.read_text(encoding="utf-8")
        else:
            todo.append(i)
    if not todo:
        return out
    try:
        import asyncio
        from winsdk.windows.media.ocr import OcrEngine
        from winsdk.windows.globalization import Language
        from winsdk.windows.graphics.imaging import BitmapDecoder
        from winsdk.windows.storage.streams import InMemoryRandomAccessStream, DataWriter
    except Exception:
        return out

    async def run() -> None:
        global _OCR_ENGINE
        if _OCR_ENGINE is None:
            _OCR_ENGINE = OcrEngine.try_create_from_language(Language("en-US"))
        for i in todo:
            png = doc[i - 1].get_pixmap(dpi=200).tobytes("png")
            st = InMemoryRandomAccessStream()
            w = DataWriter(st)
            w.write_bytes(png)
            await w.store_async()
            await w.flush_async()
            st.seek(0)
            dec = await BitmapDecoder.create_async(st)
            bmp = await dec.get_software_bitmap_async()
            res = await _OCR_ENGINE.recognize_async(bmp)
            txt = "\n".join(line.text for line in res.lines)
            out[i] = txt
            (OCR_CACHE / f"{sha[:16]}_p{i}.txt").write_text(txt, encoding="utf-8")

    try:
        asyncio.run(run())
    except Exception:
        pass
    return out


def extract_units(data: bytes, name: str, depth: int = 0, outdir: Optional[Path] = None
                  ) -> Tuple[List[Tuple[str, str, bool]], Dict[str, Any]]:
    """Return ([(location, text, is_table_row)], info)."""
    ext = sniff_ext(data, name)
    info: Dict[str, Any] = {"type": ext.lstrip(".") or "unknown"}
    units: List[Tuple[str, str, bool]] = []
    try:
        if ext == ".pdf":
            import fitz
            d = fitz.open(stream=data, filetype="pdf")
            texts = [p.get_text() for p in d]
            empty = [i for i, t in enumerate(texts, 1) if len(t.strip()) < 25]
            ocr = ocr_pages(d, empty, hashlib.sha256(data).hexdigest()) if empty else {}
            for i, t in enumerate(texts, 1):
                if i in ocr:
                    units.append((f"p.{i} (OCR)", ocr[i], False))
                else:
                    units.append((f"p.{i}", t, False))
            info.update(pages=d.page_count, pages_without_text=len(empty), pages_ocr=len(ocr))
            unread = len(empty) - len([i for i in empty if len((ocr.get(i) or "").strip()) >= 25])
            if d.page_count and unread == d.page_count:
                info["note"] = "scanned PDF: no text layer and OCR returned no text"
            elif ocr:
                info["note"] = f"scanned pages read by OCR: {len(ocr)} of {d.page_count}"
        elif ext == ".docx":
            import docx
            doc = docx.Document(io.BytesIO(data))
            paras = [p.text for p in doc.paragraphs]
            for i in range(0, len(paras), 15):
                units.append((f"para {i + 1}-{min(i + 15, len(paras))}", "\n".join(paras[i:i + 15]), False))
            for ti, t in enumerate(doc.tables, 1):
                for ri, row in enumerate(t.rows, 1):
                    cells = []
                    for c in row.cells:
                        if not cells or cells[-1] != c.text:
                            cells.append(c.text)
                    units.append((f"table {ti} row {ri}", " | ".join(cells), True))
            info.update(paragraphs=len(paras), tables=len(doc.tables))
        elif ext == ".xlsx":
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
            for sh in wb.worksheets:
                for ri, row in enumerate(sh.iter_rows(values_only=True), 1):
                    vals = [str(v) for v in row if v not in (None, "")]
                    if vals:
                        units.append((f"sheet '{sh.title}' row {ri}", " | ".join(vals), True))
            info["sheets"] = len(wb.worksheets)
        elif ext == ".xls":
            import xlrd
            wb = xlrd.open_workbook(file_contents=data)
            for sh in wb.sheets():
                for ri in range(sh.nrows):
                    vals = [str(v) for v in sh.row_values(ri) if v not in (None, "")]
                    if vals:
                        units.append((f"sheet '{sh.name}' row {ri + 1}", " | ".join(vals), True))
            info["sheets"] = wb.nsheets
        elif ext == ".doc":
            tmp = (outdir or DOCS) / f"_tmp_{hashlib.md5(data).hexdigest()[:10]}.doc"
            tmp.write_bytes(data)
            try:
                out = subprocess.run(["antiword", "-m", "UTF-8.txt", str(tmp)], capture_output=True, timeout=120)
                txt = out.stdout.decode("utf-8", "replace")
            finally:
                tmp.unlink(missing_ok=True)
            lines = txt.splitlines()
            for i in range(0, len(lines), 40):
                chunk = "\n".join(lines[i:i + 40])
                units.append((f"lines {i + 1}-{min(i + 40, len(lines))}", chunk, "|" in chunk))
            info["lines"] = len(lines)
            if not txt.strip():
                info["note"] = "legacy .doc: antiword returned no text"
        elif ext == ".rtf":
            t = re.sub(r"\\'[0-9a-f]{2}", " ", data.decode("latin-1", "replace"))
            t = re.sub(r"\\[a-z]+-?\d* ?|[{}]", " ", t)
            units.append(("text", t, False))
        elif ext in (".odt", ".odf"):
            z = zipfile.ZipFile(io.BytesIO(data))
            units.append(("content", strip_markup(z.read("content.xml").decode("utf-8", "replace")), False))
        elif ext in (".p7s", ".p7m"):
            inner = ber_octets(data)
            inner_name = re.sub(r"\.(p7s|p7m)$", "", name, flags=re.I)
            if inner:
                u2, i2 = extract_units(inner, inner_name, depth, outdir)
                units += u2
                info.update(i2)
                info["signed_envelope"] = True
            else:
                info["note"] = "signed envelope: content not found"
        elif ext == ".zip":
            if depth >= 2:
                info["note"] = "nested archive deeper than 2 levels not opened"
            else:
                z = zipfile.ZipFile(io.BytesIO(data))
                members = []
                for zi in z.infolist():
                    if zi.is_dir() or zi.file_size > MAX_FILE_BYTES:
                        continue
                    raw = zi.filename
                    if not (zi.flag_bits & 0x800):
                        try:
                            raw = zi.filename.encode("cp437").decode("utf-8")
                        except Exception:
                            pass
                    mdata = z.read(zi)
                    if outdir is not None:
                        mdir = outdir / (safe_name(name) + "_unzipped")
                        mdir.mkdir(parents=True, exist_ok=True)
                        (mdir / safe_name(raw.replace("/", "__"))).write_bytes(mdata)
                    u2, i2 = extract_units(mdata, raw, depth + 1, outdir)
                    units += [(f"{raw} > {loc}", t, row) for loc, t, row in u2]
                    members.append({"name": raw, **{k: v for k, v in i2.items() if k != "members"}})
                info["members"] = members
        elif ext in (".xml", ".html", ".json", ".txt", ".csv", ""):
            t = data.decode("utf-8", "replace")
            if ext in (".xml", ".html"):
                t = strip_markup(t)
            if ext == ".json":
                t = t.replace("\\n", "\n")
            units.append(("text", t, ext == ".csv"))
        else:
            info["note"] = f"format {ext} not read"
    except Exception as exc:
        info["error"] = f"{type(exc).__name__}: {exc}"
    return units, info


# ---------------------------------------------------------------------------
# Brand detection with location and list context
# ---------------------------------------------------------------------------
def list_context(text: str, start: int, end: int, is_row: bool) -> Tuple[bool, List[str]]:
    win = text[max(0, start - 220): end + 220]
    signs = []
    if LIST_MARKER_RE.search(win):
        signs.append("make/model/plate words")
    if PLATE_RE.search(win):
        signs.append("registration plate")
    if YEAR_RE.search(win):
        signs.append("year")
    if VIN_RE.search(win):
        signs.append("VIN")
    if is_row:
        signs.append("table row")
    # A row with any second sign, or prose with two different signs, reads as a list entry.
    return (is_row and len(signs) >= 2) or (not is_row and len(set(signs)) >= 2), signs


def scan_units(units: List[Tuple[str, str, bool]], file_label: str) -> List[Dict[str, Any]]:
    hits = []
    for loc, text, is_row in units:
        if not text:
            continue
        for brand, rx in [("Isuzu:" + k, v) for k, v in ISUZU_RE.items()] + list(OTHER_BRAND_RE.items()):
            for m in rx.finditer(text):
                in_list, signs = list_context(text, m.start(), m.end(), is_row)
                snippet = ws(text[max(0, m.start() - 110): m.end() + 110])
                hits.append({
                    "brand": "Isuzu" if brand.startswith("Isuzu:") else brand,
                    "term": m.group(0),
                    "file": file_label,
                    "where": loc,
                    "in_vehicle_list": in_list,
                    "list_signs": signs,
                    "snippet": snippet,
                })
    # one Isuzu occurrence can match two patterns ("isuzu" and "isuzu n-series")
    out, seen = [], set()
    for h in hits:
        k = (h["brand"], h["file"], h["where"], h["snippet"])
        if k not in seen:
            seen.add(k)
            out.append(h)
    return out


# ---------------------------------------------------------------------------
# Per-notice processing with a manifest cache
# ---------------------------------------------------------------------------
def notice_key(n: Dict[str, Any]) -> str:
    nid = str(n.get("source_notice_id") or "").strip()
    if not nid:
        nid = "url_" + hashlib.md5(str(n.get("url") or "").encode()).hexdigest()[:10]
    return re.sub(r"[^A-Za-z0-9._-]+", "_", nid.replace("/", "-")).strip("_")[:60]


def process_notice(f: Fetcher, n: Dict[str, Any], refresh: bool, fetched_urls: Dict[str, Any]) -> Dict[str, Any]:
    key = notice_key(n)
    ndir = DOCS / key
    fdir, tdir = ndir / "files", ndir / "text"
    fdir.mkdir(parents=True, exist_ok=True)
    tdir.mkdir(parents=True, exist_ok=True)
    man_path = ndir / "manifest.json"
    old = json.loads(man_path.read_text(encoding="utf-8")) if man_path.exists() else {}
    old_docs = {d["url"]: d for d in old.get("documents", []) if d.get("status") == "read"}

    docs, notes = resolve_url(f, str(n.get("url") or ""), key)
    entries: List[Dict[str, Any]] = []
    all_hits: List[Dict[str, Any]] = []
    for d in docs:
        if d.get("status"):
            entries.append({"url": d["url"], "status": d["status"], "note": d.get("note", "")})
            continue
        url = d["url"]
        cached = old_docs.get(url)
        if cached and not refresh and (ndir / cached["file"]).exists():
            data = (ndir / cached["file"]).read_bytes()
            fname = cached["name"]
        elif url in fetched_urls:
            data, fname = fetched_urls[url]
        else:
            try:
                data, fname = d["fetch"]()
                fetched_urls[url] = (data, fname)
            except RobotsBlocked:
                entries.append({"url": url, "status": "blocked_robots", "note": "robots.txt disallows"})
                continue
            except TooLarge as exc:
                entries.append({"url": url, "status": "too_large", "note": str(exc)})
                continue
            except Exception as exc:
                entries.append({"url": url, "status": "download_failed", "note": f"{type(exc).__name__}: {exc}"})
                continue
        fname = fname or d.get("name") or "document"
        stored = fdir / safe_name(fname)
        if stored.exists() and stored.read_bytes() != data:
            stored = fdir / safe_name(f"{hashlib.sha256(data).hexdigest()[:8]}_{fname}")
        stored.write_bytes(data)
        units, info = extract_units(data, fname, 0, fdir)
        txt = "\n".join(f"===== {loc} =====\n{t}" for loc, t, _ in units)
        (tdir / (safe_name(fname) + ".txt")).write_text(txt, encoding="utf-8")
        label = f"{key}/files/{stored.name}"
        hits = scan_units(units, label)
        all_hits += hits
        entries.append({
            "url": url, "status": "read", "kind": d.get("kind", "document"), "name": fname, "file": f"files/{stored.name}",
            "text": f"text/{safe_name(fname)}.txt", "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(), "chars": sum(len(t) for _, t, _ in units),
            **{k: v for k, v in info.items() if k != "members"},
            **({"members": len(info["members"])} if "members" in info else {}),
            "brand_hits": len(hits),
        })
    manifest = {
        "notice_key": key, "source": n.get("source"), "source_notice_id": n.get("source_notice_id"),
        "notice_url": n.get("url"), "title": n.get("title"), "checked_at": now_iso(),
        "notes": notes, "documents": entries, "hits": all_hits,
    }
    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return manifest


# ---------------------------------------------------------------------------
# Verdict per tender
# ---------------------------------------------------------------------------
def verdict_for(manifests: List[Dict[str, Any]]) -> Dict[str, Any]:
    hits = [h for m in manifests for h in m["hits"]]
    docs = [d for m in manifests for d in m["documents"]]
    read = [d for d in docs if d.get("status") == "read"]
    readable = [d for d in read if d.get("kind", "document") == "document" and (d.get("chars") or 0) > 200
                and not str(d.get("note", "")).startswith("scanned PDF: no text")]
    unreadable = [d for d in read if d.get("kind", "document") == "document"
                  and str(d.get("note", "")).startswith("scanned PDF: no text")]
    isuzu = [h for h in hits if h["brand"] == "Isuzu"]
    isuzu_list = [h for h in isuzu if h["in_vehicle_list"]]
    others_list = [h for h in hits if h["brand"] != "Isuzu" and h["in_vehicle_list"]]
    brands_list = Counter(h["brand"] for h in hits if h["in_vehicle_list"])
    list_found = len(others_list) + len(isuzu_list) >= 3 or len(brands_list) >= 2
    blocked = [d for d in docs if d.get("status") in ("needs_registration", "blocked_robots", "unreachable")]
    if isuzu_list:
        v = "isuzu_in_fleet"
    elif isuzu:
        v = "isuzu_mentioned_outside_list"
    elif list_found:
        v = "not_in_fleet"
    elif readable and not unreadable:
        v = "no_vehicle_list_found"
    else:
        v = "documents_not_available"
    say = {"needs_registration": "needs registration", "blocked_robots": "blocked by robots.txt",
           "unreachable": "link unreachable", "download_failed": "download failed",
           "listing_failed": "document list not returned", "portal_not_supported": "portal not automated",
           "too_large": "file over size cap"}
    host = lambda d: urllib.parse.urlsplit(d["url"]).netloc.replace("www.", "")
    bits = sorted({f"{say[d['status']]}: {host(d)}" for d in blocked})
    failed = [d for d in docs if d.get("status") in ("download_failed", "listing_failed", "portal_not_supported", "too_large")]
    bits += sorted({f"{say[d['status']]}: {host(d)}" for d in failed})
    if unreadable:
        bits.append(f"{len(unreadable)} scanned PDF(s) unreadable even by OCR")
    award = [n for m in manifests for n in m["notes"] if n.startswith("award notice")]
    if v == "documents_not_available" and not bits:
        bits.append(award[0] if award else "the notice names no document link")
    # Not-read parts matter even when a list was found: say so rather than imply completeness.
    reason = "; ".join(bits)
    evidence = (isuzu_list or isuzu or sorted(others_list, key=lambda h: h["brand"]))[:6]
    return {
        "verdict": v,
        "label": VERDICT_LABELS[v],
        "reason": reason,
        "documents_listed": len([d for d in docs]),
        "documents_read": len(read),
        "documents_with_text": len(readable),
        "isuzu_hits": len(isuzu),
        "isuzu_hits_in_list": len(isuzu_list),
        "brands_in_list": dict(brands_list.most_common()),
        "evidence": [{k: h[k] for k in ("brand", "term", "file", "where", "in_vehicle_list", "snippet")}
                     for h in evidence],
    }


def select_candidates(feed: Dict[str, Any], run_date: dt.date, only: List[str]) -> List[Dict[str, Any]]:
    dated, _undated, _stats = digest.select_rows(feed, run_date)
    out = [o for o in dated if str(o.get("fleet_brand") or "").startswith("unknown")
           or o.get("fleet_doc_check") or o.get("fleet_brand") == "isuzu_in_fleet_docs"]
    if only:
        out = [o for o in feed["opportunities"] if o["opportunity_id"] in only]
    return out


def apply_to_feed(feed: Dict[str, Any], results: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    changed = Counter()
    moved = 0

    def same(x: Any, y: Any) -> bool:  # equal apart from the run timestamp
        strip = lambda d: {k: v for k, v in (d or {}).items() if k != "checked_at"}
        return isinstance(x, dict) and strip(x) == strip(y)

    for o in feed["opportunities"]:
        r = results.get(o["opportunity_id"])
        if not r:
            continue
        if same(o.get("fleet_doc_check"), r):
            r = o["fleet_doc_check"]  # keep the original timestamp: a re-run changes nothing
            results[o["opportunity_id"]] = r
        else:
            moved += 1
        o["fleet_doc_check"] = r
        text = " ".join(str(x.get("title") or "") for x in (o.get("notices") or []))
        core.apply_fleet_brand_gate(o, text)
        changed[r["verdict"]] += 1
    for n in feed["notices"]:
        r = results.get(n.get("opportunity_id"))
        if r:
            n["fleet_doc_check"] = r
            core.apply_fleet_brand_gate(n, str(n.get("Description") or ""))
    feed["opportunities"].sort(key=lambda o: (
        core.DECISION_ORDER.get(o.get("decision"), 9),
        core.URGENCY_ORDER.get(o.get("urgency"), 9),
        -(int(o.get("opportunity_score") or 0)),
    ))
    old_meta = feed.setdefault("meta", {}).get("fleet_doc_check") or {}
    if moved or old_meta.get("verdicts") != dict(changed):
        feed["meta"]["fleet_doc_check"] = {
            "checked_at": now_iso(), "tenders": len(results), "verdicts": dict(changed),
            "summary": str(SUMMARY.relative_to(ROOT)).replace("\\", "/"),
        }
    return dict(changed)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write the result into tender_data.json")
    ap.add_argument("--refresh", action="store_true", help="download documents again even if cached")
    ap.add_argument("--only", nargs="*", default=[], help="opportunity ids")
    ap.add_argument("--date", default=None)
    args = ap.parse_args(argv)
    run_date = digest.parse_date(args.date) or dt.date.today()

    raw = FEED.read_text(encoding="utf-8")
    feed = json.loads(raw)
    cands = select_candidates(feed, run_date, args.only)
    DOCS.mkdir(exist_ok=True)
    f = Fetcher()
    fetched: Dict[str, Any] = {}
    results: Dict[str, Dict[str, Any]] = {}
    rows = []
    print(f"tenders to check: {len(cands)}")
    for o in cands:
        manifests = []
        for n in o.get("notices") or [{"url": o.get("url"), "source_notice_id": o.get("opportunity_id")}]:
            manifests.append(process_notice(f, n, args.refresh, fetched))
        v = verdict_for(manifests)
        v.update({
            "checked_at": now_iso(),
            "notice_dirs": [f"04_tools/ISZE_Tender_Monitor_Install/tender_docs/{m['notice_key']}" for m in manifests],
            "notes": [x for m in manifests for x in m["notes"]],
            "documents": [{"notice": m["notice_key"], "url": d["url"], "status": d["status"],
                           **({"file": f"{m['notice_key']}/{d['file']}"} if d.get("file") else {}),
                           **({"note": d.get("note")} if d.get("note") else {}),
                           **({"pages": d.get("pages")} if d.get("pages") else {})}
                          for m in manifests for d in m["documents"]],
        })
        results[o["opportunity_id"]] = v
        rows.append({"opportunity_id": o["opportunity_id"], "country": o.get("country"),
                     "title": o.get("title"), "deadline": o.get("deadline_date"),
                     "decision_in_feed_when_read": o.get("decision"), "fleet_brand_in_feed_when_read": o.get("fleet_brand"), **v})
        print(f"  {o['opportunity_id']} {str(o.get('country')):<9} {v['verdict']:<30} "
              f"read {v['documents_read']}/{v['documents_listed']}  isuzu {v['isuzu_hits']} "
              f"(list {v['isuzu_hits_in_list']})  {v['reason'][:80]}")

    summary = {"generated_at": now_iso(), "feed": str(FEED.relative_to(ROOT)).replace("\\", "/"),
               "feed_generated_at": feed.get("meta", {}).get("generated_at"),
               "verdict_counts": dict(Counter(r["verdict"] for r in rows)), "tenders": rows,
               "http_log": f.log}
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"summary: {SUMMARY}")
    print("verdicts:", summary["verdict_counts"])

    if args.apply:
        before = Counter(o.get("decision") for o in feed["opportunities"])
        apply_to_feed(feed, results)
        new = json.dumps(feed, ensure_ascii=False, indent=2)
        if new != raw:
            stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            bak = FEED.with_name(f"tender_data.json.bak_before_doc_check_{stamp}")
            shutil.copy2(FEED, bak)
            FEED.write_text(new, encoding="utf-8")
            after = Counter(o.get("decision") for o in feed["opportunities"])
            print(f"feed written; backup {bak.name}")
            print(f"decisions before {dict(before)}")
            print(f"decisions after  {dict(after)}")
        else:
            print("feed unchanged (nothing new to write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
