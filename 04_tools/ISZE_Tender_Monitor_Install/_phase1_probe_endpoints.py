# -*- coding: utf-8 -*-
"""Phase 1 endpoint discovery — probe only; does not touch production scrapers."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import requests

OUT = Path(__file__).with_name("_phase1_probe_raw.json")
UA = {
    "User-Agent": "ISZE-Tender-Monitor-Discovery/1.0 (research; local)",
    "Accept": "application/json, application/xml, text/xml, */*",
}
CPV_CODES = [
    "34131000",
    "34113000",
    "34136000",
    "34130000",
    "34136200",
    "50110000",
    "50112000",
    "50116000",
    "50111000",
]


def summarize_body(text: str, j):
    has_item = "<item" in text.lower()
    has_entry = "<entry" in text.lower()
    looks_json = j is not None
    sample = None
    extra = {}
    if isinstance(j, dict):
        extra["json_keys"] = list(j.keys())[:25]
        res = j.get("result")
        if isinstance(res, dict):
            extra["result_keys"] = list(res.keys())[:25]
            if "records" in res:
                recs = res.get("records") or []
                extra["n_records"] = len(recs)
                extra["total"] = res.get("total")
                if recs:
                    sample = {k: recs[0].get(k) for k in list(recs[0].keys())[:15]}
            if "results" in res and isinstance(res["results"], list):
                pkgs = []
                for p in res["results"][:12]:
                    pkgs.append(
                        {
                            "name": p.get("name"),
                            "title": (p.get("title") or "")[:120],
                            "resources": [
                                {
                                    "format": r.get("format"),
                                    "id": r.get("id"),
                                    "url": (r.get("url") or "")[:160],
                                    "name": (r.get("name") or "")[:80],
                                }
                                for r in (p.get("resources") or [])[:6]
                            ],
                        }
                    )
                extra["packages"] = pkgs
        notices = j.get("notices")
        if isinstance(notices, list):
            extra["n_notices"] = len(notices)
            extra["totalNoticeCount"] = j.get("totalNoticeCount") or j.get("total")
            if notices:
                sample = notices[0]
        # generic list fields
        for key in ("data", "items", "content", "results", "hits"):
            if isinstance(j.get(key), list) and j[key]:
                extra[f"n_{key}"] = len(j[key])
                if sample is None:
                    sample = j[key][0]
    elif isinstance(j, list):
        extra["list_len"] = len(j)
        if j:
            sample = j[0]
    return {
        "has_item": has_item,
        "has_entry": has_entry,
        "looks_json": looks_json,
        "sample": sample,
        **extra,
    }


def probe(session, name, url, method="GET", **kw):
    row = {"name": name, "url": url, "method": method}
    try:
        if method == "POST":
            r = session.post(url, timeout=60, **kw)
        else:
            r = session.get(url, timeout=60, **kw)
        body = r.content
        text = body.decode("utf-8", errors="replace")
        j = None
        try:
            j = r.json()
        except Exception:
            j = None
        row.update(
            {
                "status": r.status_code,
                "content_type": r.headers.get("Content-Type", ""),
                "bytes": len(body),
                "preview": text[:300],
                **summarize_body(text, j),
            }
        )
        # keep full JSON for small successful payloads
        if j is not None and len(body) < 500_000:
            row["json"] = j
    except Exception as exc:
        row["error"] = str(exc)
    print(
        f"{row.get('status','ERR')} {row.get('bytes','?'):>8} "
        f"json={row.get('looks_json')} item={row.get('has_item')} | {name}",
        flush=True,
    )
    return row


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    session = requests.Session()
    session.headers.update(UA)
    results = []

    # --- Israel baseline ---
    results.append(
        probe(session, "IL_dead_RSS", "https://mr.gov.il/ilgstorefront/he/rss/Tenders.xml")
    )

    # --- data.gov.il package discovery ---
    for q in [
        "מכרזים",
        "tenders",
        "רכש ממשלתי",
        "התקשרויות בפטור",
        "מינהל הרכש",
        "procurement",
        "Government Procurement",
    ]:
        results.append(
            probe(
                session,
                f"CKAN_package_search:{q}",
                f"https://data.gov.il/api/3/action/package_search?q={quote(q)}&rows=15",
            )
        )

    # Also try package_list / organization
    results.append(
        probe(
            session,
            "CKAN_package_search_org",
            "https://data.gov.il/api/3/action/package_search?fq=organization:ministry_of_finance&rows=20",
        )
    )
    results.append(
        probe(
            session,
            "CKAN_package_search_title_tender",
            "https://data.gov.il/api/3/action/package_search?q=title:מכרז&rows=20",
        )
    )

    # Known resource IDs from community MCP / prior research (will verify live)
    known_resources = [
        # placeholders filled after package search; also try common names via resource_search
    ]
    results.append(
        probe(
            session,
            "CKAN_resource_search_tender",
            "https://data.gov.il/api/3/action/resource_search?query=name:מכרז",
        )
    )
    results.append(
        probe(
            session,
            "CKAN_resource_search_tenders_en",
            "https://data.gov.il/api/3/action/resource_search?query=description:tender",
        )
    )

    # mr.gov.il alternate paths / search API guesses
    il_candidates = [
        "https://mr.gov.il/ilgstorefront/he/rss",
        "https://mr.gov.il/ilgstorefront/en/rss/Tenders.xml",
        "https://mr.gov.il/ilgstorefront/he/rss/tenders.xml",
        "https://mr.gov.il/ilgstorefront/rss/Tenders.xml",
        "https://mr.gov.il/ilgstorefront/he/search/?s=TENDER&q=:&format=json",
        "https://mr.gov.il/ilgstorefront/he/search/searchJSON?s=TENDER",
        "https://mr.gov.il/ilgstorefront/he/search/?s=TENDER&ajax=true",
        "https://mr.gov.il/ilgstorefront/he/search/autocomplete?term=רכב",
        "https://mr.gov.il/ilgstorefront/he/api/tenders",
        "https://mr.gov.il/ilgstorefront/he/c/tenders",
    ]
    for url in il_candidates:
        results.append(probe(session, f"IL_cand:{url.split('ilgstorefront')[-1][:60]}", url))

    # Inspect HTML search page for embedded JSON / API hints
    html_url = "https://mr.gov.il/ilgstorefront/he/search/?s=TENDER"
    r = session.get(html_url, timeout=60)
    html = r.content.decode("utf-8", errors="replace")
    api_hints = sorted(
        set(
            re.findall(
                r"(?:https?:)?//[^\s\"']+|/[a-zA-Z0-9_./-]{8,}(?:json|api|search|rss|atom)[^\s\"']*",
                html,
                flags=re.I,
            )
        )
    )
    # tighter: script src + fetch/xhr-like strings
    script_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html, flags=re.I)
    json_blobs = re.findall(r"application/json[^>]*>(\{.*?\})</script>", html, flags=re.I | re.S)
    data_attrs = re.findall(r"data-[a-z-]+=[\"']([^\"']{20,200})[\"']", html, flags=re.I)
    # product cards / selectors
    selectors = {
        "product_class": len(re.findall(r'class=["\'][^"\']*product[^"\']*["\']', html, flags=re.I)),
        "tender_class": len(re.findall(r'tender', html, flags=re.I)),
        "search_result": len(re.findall(r'search-result|product-item|product__list', html, flags=re.I)),
        "deadline_he": len(re.findall(r'מועד אחרון|סגירה|deadline', html, flags=re.I)),
    }
    # extract a few product link patterns
    product_links = re.findall(
        r'href=["\']([^"\']*(?:/p/|/tender|/product)[^"\']*)["\']', html, flags=re.I
    )[:10]
    titles = re.findall(
        r'<[^>]+class=["\'][^"\']*product[^"\']*name[^"\']*["\'][^>]*>(.*?)</',
        html,
        flags=re.I | re.S,
    )[:5]
    results.append(
        {
            "name": "IL_HTML_search_analysis",
            "url": html_url,
            "status": r.status_code,
            "content_type": r.headers.get("Content-Type", ""),
            "bytes": len(r.content),
            "script_srcs": script_srcs[:40],
            "api_hint_count": len(api_hints),
            "api_hints_sample": api_hints[:40],
            "json_blob_count": len(json_blobs),
            "selectors": selectors,
            "product_links": product_links,
            "title_snippets": [re.sub(r"<[^>]+>", "", t).strip()[:120] for t in titles],
            "has_item": False,
            "looks_json": False,
        }
    )
    print(f"{r.status_code} {len(r.content):>8} HTML analysis done", flush=True)

    # Probe interesting script-relative APIs if any look like search endpoints
    for src in script_srcs:
        if any(x in src.lower() for x in ("search", "tender", "product", "api")):
            full = src if src.startswith("http") else f"https://mr.gov.il{src}"
            # don't download huge JS; just note
            results.append({"name": "IL_script_src", "url": full})

    # --- Belgium baselines ---
    for url, name in [
        ("https://www.publicprocurement.be/en/rss", "BE_dead_en_rss"),
        ("https://www.publicprocurement.be/supplier/feed/rss", "BE_dead_supplier_rss"),
        ("https://www.publicprocurement.be/nl/rss", "BE_dead_nl_rss"),
        ("https://enot.publicprocurement.be/", "BE_enot_home"),
        ("https://enot.publicprocurement.be/enot-war/home.do", "BE_enot_home_do"),
    ]:
        results.append(probe(session, name, url))

    # Belgium API / open-data candidates
    be_get = [
        "https://www.publicprocurement.be/api/notices",
        "https://www.publicprocurement.be/api/search",
        "https://www.publicprocurement.be/api/v1/notices",
        "https://www.publicprocurement.be/en/api/notices",
        "https://api.publicprocurement.be/notices",
        "https://api.publicprocurement.be/v1/notices",
        "https://enot.publicprocurement.be/api/notices",
        "https://enot.publicprocurement.be/api/search",
        "https://enot.publicprocurement.be/enot-war/search.do",
        "https://enot.publicprocurement.be/enot-war/rest/notices",
        "https://enot.publicprocurement.be/enot-war/secured/rest/notices",
        "https://opendata.bosa.be/",
        "https://opendata.belgium.be/api/3/action/package_search?q=procurement",
        "https://opendata.belgium.be/api/3/action/package_search?q=overheidsopdracht",
        "https://opendata.belgium.be/api/3/action/package_search?q=aanbesteding",
        "https://data.gov.be/api/3/action/package_search?q=procurement",
        "https://data.gov.be/api/3/action/package_search?q=public%20procurement",
        "https://www.publicprocurement.be/assets/config.json",
        "https://www.publicprocurement.be/en/search",
        "https://www.publicprocurement.be/env.js",
        "https://www.publicprocurement.be/config.js",
        "https://www.publicprocurement.be/main.js",
        # BOSA / eproc swagger guesses
        "https://api.eprocurement.belgium.be/swagger",
        "https://api.publicprocurement.be/swagger",
        "https://api.publicprocurement.be/v1/swagger.json",
        "https://enot.publicprocurement.be/v2/api-docs",
        "https://enot.publicprocurement.be/swagger-ui.html",
        # older BDA bulletin
        "https://enot.publicprocurement.be/enot-war/preViewNotice.do",
        "https://bda.publicprocurement.be/",
        "https://www.publicprocurement.be/.well-known/openid-configuration",
    ]
    for url in be_get:
        results.append(probe(session, f"BE_GET:{url[:70]}", url))

    # Analyze SPA shell for API base URLs
    spa = session.get("https://www.publicprocurement.be/en/rss", timeout=30)
    spa_text = spa.content.decode("utf-8", errors="replace")
    spa_hints = sorted(
        set(
            re.findall(
                r"https?://[a-zA-Z0-9._/-]*(?:api|enot|bosa|procurement)[a-zA-Z0-9._/-]*",
                spa_text,
                flags=re.I,
            )
        )
    )
    script_tags = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', spa_text, flags=re.I)
    results.append(
        {
            "name": "BE_SPA_shell_analysis",
            "url": "https://www.publicprocurement.be/en/rss",
            "status": spa.status_code,
            "bytes": len(spa.content),
            "preview": spa_text[:500],
            "spa_hints": spa_hints,
            "scripts": script_tags,
        }
    )

    # Fetch SPA JS bundles and mine for API paths
    for src in script_tags[:8]:
        full = src if src.startswith("http") else f"https://www.publicprocurement.be{src}"
        try:
            jr = session.get(full, timeout=60)
            jst = jr.content.decode("utf-8", errors="replace")
            apis = sorted(
                set(
                    re.findall(
                        r"[\"'](/[a-zA-Z0-9_./-]{3,}(?:api|notice|search|publication|tender)[a-zA-Z0-9_./-]*)[\"']",
                        jst,
                        flags=re.I,
                    )
                )
            )
            abs_apis = sorted(
                set(
                    re.findall(
                        r"https?://[a-zA-Z0-9._:-]+/[a-zA-Z0-9._/-]*(?:api|notice|search|publication)[a-zA-Z0-9._/-]*",
                        jst,
                        flags=re.I,
                    )
                )
            )[:50]
            results.append(
                {
                    "name": f"BE_JS:{full[-60:]}",
                    "url": full,
                    "status": jr.status_code,
                    "bytes": len(jr.content),
                    "api_paths": apis[:80],
                    "abs_apis": abs_apis,
                }
            )
            print(f"{jr.status_code} {len(jr.content):>8} JS mined paths={len(apis)} abs={len(abs_apis)}", flush=True)
            # probe unique promising absolute APIs
            for a in abs_apis[:15]:
                if any(x in a.lower() for x in ("api", "notice", "search", "publication")):
                    results.append(probe(session, f"BE_fromJS:{a[:70]}", a.split("?")[0]))
        except Exception as exc:
            results.append({"name": f"BE_JS_err", "url": full, "error": str(exc)})

    # Also try enot search page JS
    try:
        enot = session.get("https://enot.publicprocurement.be/", timeout=45)
        enot_html = enot.content.decode("utf-8", errors="replace")
        enot_scripts = re.findall(r'src=["\']([^"\']+)["\']', enot_html, flags=re.I)
        enot_apis = sorted(
            set(
                re.findall(
                    r"https?://[a-zA-Z0-9._:-]+/[a-zA-Z0-9._/-]*api[a-zA-Z0-9._/-]*",
                    enot_html,
                    flags=re.I,
                )
            )
        )
        results.append(
            {
                "name": "BE_enot_html_analysis",
                "url": "https://enot.publicprocurement.be/",
                "status": enot.status_code,
                "bytes": len(enot.content),
                "scripts": enot_scripts[:40],
                "api_hints": enot_apis[:40],
                "preview": enot_html[:400],
            }
        )
        for src in enot_scripts[:10]:
            if not src.lower().endswith((".js", ".mjs")) and "js" not in src.lower():
                continue
            full = src if src.startswith("http") else (
                f"https://enot.publicprocurement.be{src}" if src.startswith("/") else src
            )
            try:
                jr = session.get(full, timeout=45)
                jst = jr.content.decode("utf-8", errors="replace")
                abs_apis = sorted(
                    set(
                        re.findall(
                            r"https?://[a-zA-Z0-9._:-]+/[a-zA-Z0-9._/-]*(?:api|rest|notice|search)[a-zA-Z0-9._/-]*",
                            jst,
                            flags=re.I,
                        )
                    )
                )[:40]
                paths = sorted(
                    set(
                        re.findall(
                            r"[\"'](/[a-zA-Z0-9_./-]*(?:api|rest|notice|search)[a-zA-Z0-9_./-]*)[\"']",
                            jst,
                            flags=re.I,
                        )
                    )
                )[:60]
                results.append(
                    {
                        "name": f"BE_enot_JS:{full[-50:]}",
                        "url": full,
                        "status": jr.status_code,
                        "bytes": len(jr.content),
                        "abs_apis": abs_apis,
                        "paths": paths,
                    }
                )
                for a in abs_apis[:10]:
                    results.append(probe(session, f"BE_enot_fromJS:{a[:65]}", a.split("?")[0]))
            except Exception as exc:
                results.append({"name": "BE_enot_JS_err", "url": full, "error": str(exc)})
    except Exception as exc:
        results.append({"name": "BE_enot_html_err", "error": str(exc)})

    # --- TED CYP / MLT last 30 days ---
    date_from = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y%m%d")
    cpv_block = " OR ".join([f"PC={c}" for c in CPV_CODES])
    ted_url = "https://api.ted.europa.eu/v3/notices/search"
    for countries, label in [
        (["CYP"], "TED_CYP_30d"),
        (["MLT"], "TED_MLT_30d"),
        (["CYP", "MLT"], "TED_CYP_MLT_30d"),
        (["BEL"], "TED_BEL_30d_control"),
    ]:
        country_block = " OR ".join([f"CY={c}" for c in countries])
        query = f"({cpv_block}) AND ({country_block}) AND PD>={date_from}"
        payload = {
            "query": query,
            "fields": ["ND", "TI", "PD", "DD", "CY", "PC", "AU"],
            "limit": 100,
            "paginationMode": "ITERATION",
        }
        row = probe(session, label, ted_url, method="POST", json=payload)
        row["ted_query"] = query
        # also try to get total via page mode
        payload2 = {
            "query": query,
            "fields": ["ND", "TI", "PD", "DD", "CY", "PC", "AU"],
            "limit": 1,
            "page": 1,
            "paginationMode": "PAGE_NUMBER",
            "scope": "ALL",
            "onlyLatestVersions": True,
        }
        row2 = probe(session, f"{label}_page", ted_url, method="POST", json=payload2)
        row2["ted_query"] = query
        results.append(row)
        results.append(row2)

    # Strip huge json blobs for file size — keep samples
    slim = []
    for r in results:
        rr = dict(r)
        if "json" in rr:
            j = rr.pop("json")
            # keep small useful subsets
            if isinstance(j, dict) and "result" in j and isinstance(j["result"], dict):
                res = j["result"]
                if "records" in res:
                    rr["records_sample"] = (res.get("records") or [])[:2]
                    rr["total"] = res.get("total")
                if "results" in res:
                    rr["packages"] = rr.get("packages") or [
                        {"name": p.get("name"), "title": p.get("title")}
                        for p in (res.get("results") or [])[:15]
                    ]
            if "notices" in (j if isinstance(j, dict) else {}):
                rr["notices_sample"] = (j.get("notices") or [])[:2]
                rr["totalNoticeCount"] = j.get("totalNoticeCount") or j.get("total")
        slim.append(rr)

    OUT.write_text(json.dumps(slim, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {OUT} ({len(slim)} rows)", flush=True)


if __name__ == "__main__":
    main()
