#!/usr/bin/env python3
"""Probe CZ VVZ api.vvz.nipez.cz submissions/search + BG OCDS vehicle filter sample."""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
OUT = HERE / "_probe_cz_bg_wire.json"
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://vvz.nipez.cz",
    "Referer": "https://vvz.nipez.cz/",
}


def main() -> None:
    s = requests.Session()
    out: dict = {"probed_at": datetime.now(timezone.utc).isoformat()}

    # Discover CZ API from JS for search payload shape
    js = s.get("https://vvz.nipez.cz/static/js/main.e8045595.js", headers=UA, timeout=90).text
    # snippets around submissions/search
    ctx = []
    for m in re.finditer(r".{0,80}submissions/search.{0,120}", js):
        ctx.append(m.group(0).replace("\n", " "))
        if len(ctx) >= 8:
            break
    out["cz_js_search_ctx"] = ctx

    base = "https://api.vvz.nipez.cz"
    # Try several roots that appear in hosts
    roots = [
        "",
        "/vvz2-json-formulare",
        "/vvz-export",
    ]
    tries = []
    payloads = [
        {"method": "GET", "path": "/api/submissions/search?page=0&size=5", "json": None},
        {"method": "POST", "path": "/api/submissions/search", "json": {"page": 0, "size": 5}},
        {"method": "POST", "path": "/api/submissions/search", "json": {"pageNumber": 0, "pageSize": 5}},
        {"method": "GET", "path": "/api/forms?page=0&size=5", "json": None},
        {"method": "GET", "path": "/api/organizations?page=0&size=5", "json": None},
        {"method": "POST", "path": "/api/submissions/search", "json": {
            "fulltext": "nákladní",
            "page": 0,
            "size": 10,
        }},
    ]
    for root in ["", "/vvz2-json-formulare"]:
        for t in payloads:
            url = base + root + t["path"]
            try:
                if t["method"] == "GET":
                    r = s.get(url, headers=UA, timeout=35)
                else:
                    r = s.post(url, headers={**UA, "Content-Type": "application/json"}, json=t["json"], timeout=35)
                row = {
                    "url": url,
                    "method": t["method"],
                    "http": r.status_code,
                    "len": len(r.content),
                    "snip": r.text[:300].replace("\n", " "),
                }
                if r.status_code == 200 and r.content[:1] in (b"{", b"["):
                    try:
                        data = r.json()
                        row["type"] = type(data).__name__
                        if isinstance(data, dict):
                            row["keys"] = list(data.keys())[:25]
                            # common page shapes
                            for k in ("content", "items", "results", "data", "submissions"):
                                if isinstance(data.get(k), list):
                                    row[f"n_{k}"] = len(data[k])
                                    if data[k] and isinstance(data[k][0], dict):
                                        row["item_keys"] = list(data[k][0].keys())[:30]
                    except Exception as e:
                        row["json_err"] = str(e)[:80]
                tries.append(row)
                print(t["method"], r.status_code, url[-70:], len(r.content))
            except Exception as e:
                tries.append({"url": url, "error": str(e)[:200]})
    out["cz_tries"] = tries

    # Also try public "nove-zakazky" HTML list API if any XHR
    for u in [
        "https://vvz.nipez.cz/nove-zakazky",
        "https://api.vvz.nipez.cz/vvz2-json-formulare/api/submissions/search",
    ]:
        pass

    # BG: download OCDS notices for yesterday, filter vehicle keywords/CPV
    day = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    list_url = f"https://storage.eop.bg/open-data-{day}/"
    lr = s.get(list_url, headers=UA, timeout=40)
    keys = re.findall(r"<Key>([^<]+)</Key>", lr.text)
    ocds_key = next((k for k in keys if "OCDS" in k.upper() or "обявления" in k.lower()), None)
    bg = {"day": day, "list_http": lr.status_code, "keys": keys, "ocds_key": ocds_key}
    if ocds_key:
        # URL-encode path segments carefully
        file_url = list_url + urllib.parse.quote(ocds_key)
        fr = s.get(file_url, headers=UA, timeout=120)
        bg["file_http"] = fr.status_code
        bg["file_len"] = len(fr.content)
        if fr.status_code == 200:
            pkg = fr.json()
            releases = pkg.get("releases") or []
            bg["n_releases"] = len(releases)
            KW = (
                "камион", "пикап", "шаси", "isuzu", "товарни", "автомобил",
                "превозн", "ремонт", "поддръжка", "truck", "pickup", "chassis",
                "van", "lcv", "d-max", "n-series",
            )
            CPV = ("3410", "3413", "3414", "5011", "3400")
            hits = []
            for rel in releases:
                tender = rel.get("tender") or {}
                title = str(tender.get("title") or "")
                desc = str(tender.get("description") or "")
                blob = (title + " " + desc).lower()
                items = tender.get("items") or []
                cpvs = []
                for it in items:
                    clas = it.get("classification") or {}
                    if isinstance(clas, dict) and clas.get("id"):
                        cpvs.append(str(clas["id"]))
                    for ac in it.get("additionalClassifications") or []:
                        if isinstance(ac, dict) and ac.get("id"):
                            cpvs.append(str(ac["id"]))
                kw_ok = any(k in blob for k in KW)
                cpv_ok = any(any(c.startswith(p) for p in CPV) for c in cpvs)
                if kw_ok or cpv_ok:
                    buyer = ""
                    parties = rel.get("parties") or []
                    for p in parties:
                        roles = p.get("roles") or []
                        if "buyer" in roles:
                            buyer = p.get("name") or ""
                            break
                    tid = tender.get("id") or rel.get("ocid") or ""
                    hits.append({
                        "ocid": rel.get("ocid"),
                        "tender_id": tid,
                        "title": title[:180],
                        "buyer": buyer[:120],
                        "cpvs": cpvs[:8],
                        "kw": kw_ok,
                        "cpv": cpv_ok,
                        "url": f"https://app.eop.bg/today/{tid}" if tid else "",
                    })
            bg["vehicle_hits"] = len(hits)
            bg["sample_hits"] = hits[:15]
            print(f"BG OCDS releases={len(releases)} vehicle_hits={len(hits)}")
    out["bg"] = bg

    # SK vestnik ajax without captcha?
    sk_url = (
        "https://www.uvo.gov.sk/vestnik-a-registre/vestnik"
        "?tx_tempestvestnik_vestnik%5Baction%5D=ajaxGetCode"
        "&tx_tempestvestnik_vestnik%5Bcontroller%5D=Vestnik&type=199900"
    )
    try:
        sr = s.get(sk_url, headers={**UA, "X-Requested-With": "XMLHttpRequest", "Referer": "https://www.uvo.gov.sk/"}, timeout=30)
        out["sk_ajax"] = {"http": sr.status_code, "len": len(sr.content), "snip": sr.text[:400]}
    except Exception as e:
        out["sk_ajax"] = {"error": str(e)[:200]}

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
