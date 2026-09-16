#!/usr/bin/env python3
"""Deep probe feasible dark sources: BG OCDS storage, SK RSS/HTML, EE API, CZ VVZ, GR."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
OUT = HERE / "_probe_dark_deep.json"
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
}


def main() -> None:
    s = requests.Session()
    out: dict = {"probed_at": datetime.now(timezone.utc).isoformat(), "sections": {}}

    # --- BG OCDS daily storage ---
    bg = []
    for d in range(0, 10):
        day = (datetime.now(timezone.utc) - timedelta(days=d)).strftime("%Y-%m-%d")
        url = f"https://storage.eop.bg/open-data-{day}/"
        try:
            r = s.get(url, headers=UA, timeout=45)
        except Exception as e:
            bg.append({"day": day, "error": str(e)[:200]})
            continue
        row = {"day": day, "http": r.status_code, "len": len(r.content), "ct": r.headers.get("Content-Type", "")}
        if r.status_code == 200:
            text = r.text
            row["snip"] = text[:500]
            hrefs = re.findall(r'href="([^"]+)"', text)
            keys = re.findall(r"<Key>([^<]+)</Key>", text)
            row["hrefs"] = hrefs[:40]
            row["keys"] = keys[:40]
            # fetch first release-like object
            candidates = [h for h in (hrefs + keys) if h and not h.endswith("/") and h not in ("../",)]
            for h in candidates[:5]:
                fu = h if h.startswith("http") else url + h.lstrip("/")
                try:
                    rr = s.get(fu, headers=UA, timeout=90)
                except Exception as e:
                    row.setdefault("files", []).append({"path": h, "error": str(e)[:120]})
                    continue
                finfo = {
                    "path": h,
                    "http": rr.status_code,
                    "len": len(rr.content),
                    "ct": rr.headers.get("Content-Type", "")[:60],
                    "head": rr.content[:200].decode("utf-8", errors="replace"),
                }
                if rr.status_code == 200 and ("json" in (rr.headers.get("Content-Type") or "").lower() or rr.content[:1] in (b"{", b"[")):
                    try:
                        data = rr.json()
                        finfo["json_type"] = type(data).__name__
                        if isinstance(data, dict):
                            finfo["keys"] = list(data.keys())[:30]
                            # OCDS release package?
                            if "releases" in data:
                                finfo["n_releases"] = len(data.get("releases") or [])
                            if "compiledRelease" in data:
                                finfo["has_compiled"] = True
                    except Exception as e:
                        finfo["json_err"] = str(e)[:100]
                row.setdefault("files", []).append(finfo)
            bg.append(row)
            break
        bg.append(row)
    out["sections"]["BG"] = bg
    print("BG done", [x.get("day") for x in bg if x.get("http") == 200])

    # --- SK RSS + vestnik scripts ---
    sk = {}
    r = s.get("https://www.uvo.gov.sk/rss", headers=UA, timeout=30)
    sk["rss"] = {"http": r.status_code, "ct": r.headers.get("Content-Type"), "snip": r.text[:800], "len": len(r.content)}
    r2 = s.get("https://www.uvo.gov.sk/vyhladavanie/vyhladavanie-zakaziek", headers=UA, timeout=45)
    sk["vestnik_http"] = r2.status_code
    sk["vestnik_len"] = len(r2.content)
    sk["script_srcs"] = re.findall(r'src="([^"]+)"', r2.text)[:40]
    # search for XHR endpoints in page
    sk["api_mentions"] = list(set(re.findall(r'https?://[^"\']+api[^"\']*', r2.text, re.I)))[:20]
    sk["ajax_paths"] = list(set(re.findall(r'["\'](/[^"\']*(?:ajax|api|search|vestnik)[^"\']*)["\']', r2.text, re.I)))[:30]
    out["sections"]["SK"] = sk
    print("SK rss", sk["rss"]["http"], sk["rss"]["ct"])

    # --- EE ---
    ee = []
    for u in [
        "https://riigihanked.riik.ee/rhr/api/public/v1/opendata",
        "https://riigihanked.riik.ee/rhr/api/public/v1/opendata?page=0&size=5",
        "https://riigihanked.riik.ee/rhr/api/public/v1/notices?page=0&size=5",
        "https://riigihanked.riik.ee/rhr/api/public/v1/procurements?page=0&size=5",
        "https://riigihanked.riik.ee/rhr/api/public/v1/search?keyword=veok&page=0&size=5",
        "https://avahanked.ee/en",
        "https://api.riigihanked.eu/openapi.json",
    ]:
        try:
            r = s.get(u, headers={**UA, "Accept": "application/json, text/html"}, timeout=30)
            ee.append({"url": u, "http": r.status_code, "len": len(r.content), "snip": r.text[:200].replace("\n", " ")})
        except Exception as e:
            ee.append({"url": u, "error": str(e)[:200]})
    out["sections"]["EE"] = ee
    print("EE probed", len(ee))

    # --- CZ VVZ SPA ---
    cz = {}
    r = s.get("https://vvz.nipez.cz/", headers=UA, timeout=30)
    cz["home"] = {"http": r.status_code, "len": len(r.content), "snip": r.text[:400]}
    assets = re.findall(r'(?:src|href)="(/[^"]+)"', r.text)
    cz["assets"] = assets[:40]
    api_hits = []
    for a in assets:
        if not any(x in a for x in (".js", "main", "chunk", "app", "static")):
            continue
        if a.endswith(".css") or a.endswith(".svg") or a.endswith(".png"):
            continue
        try:
            jr = s.get("https://vvz.nipez.cz" + a, headers=UA, timeout=60)
        except Exception as e:
            api_hits.append({"asset": a, "error": str(e)[:100]})
            continue
        apis = sorted(set(re.findall(r'["\'](/api/[^"\']+)["\']', jr.text)))
        hosts = sorted(set(re.findall(r'https?://[^"\']*(?:vvz|nipez)[^"\']*', jr.text, re.I)))[:15]
        if apis or "api" in jr.text.lower():
            api_hits.append({"asset": a, "http": jr.status_code, "len": len(jr.content), "apis": apis[:40], "hosts": hosts})
    cz["js_api"] = api_hits
    # try common backend
    for u in [
        "https://vvz.nipez.cz/api/Formulare/Search",
        "https://vvz.nipez.cz/api/vyhledat",
        "https://vvz.nipez.cz/api/Search/Formulare",
        "https://api.vvz.nipez.cz/",
    ]:
        try:
            rr = s.get(u, headers={**UA, "Accept": "application/json"}, timeout=25)
            cz.setdefault("api_try", []).append({"url": u, "http": rr.status_code, "len": len(rr.content), "snip": rr.text[:150]})
        except Exception as e:
            cz.setdefault("api_try", []).append({"url": u, "error": str(e)[:150]})
    out["sections"]["CZ"] = cz
    print("CZ assets", len(assets), "js_api", len(api_hits))

    # --- GR ---
    gr = {}
    r = s.get("https://cerpp.eprocurement.gov.gr/kimdis/opendata", headers=UA, timeout=30)
    gr["kimdis_page"] = {"http": r.status_code, "len": len(r.content), "snip": r.text[:600], "links": re.findall(r'href="([^"]+)"', r.text)[:30]}
    # Diavgeia with proper params
    for u in [
        "https://diavgeia.gov.gr/luminapi/api/search?q=%CE%A6%CE%BF%CF%81%CF%84%CE%B7%CE%B3&page=0&size=5",
        "https://diavgeia.gov.gr/luminapi/api/search.json?q=truck&page=0&size=5",
        "https://diavgeia.gov.gr/api/search?q=φορτηγ&page=0",
    ]:
        try:
            rr = s.get(u, headers={**UA, "Accept": "application/json"}, timeout=30)
            gr.setdefault("diavgeia", []).append({"url": u, "http": rr.status_code, "len": len(rr.content), "snip": rr.text[:250]})
        except Exception as e:
            gr.setdefault("diavgeia", []).append({"url": u, "error": str(e)[:150]})
    out["sections"]["GR"] = gr
    print("GR done")

    # --- HR / SI / LV HTML feasibility snips ---
    misc = {}
    for name, url in [
        ("HR_eojn", "https://eojn.nn.hr/"),
        ("SI_enarocanje", "https://www.enarocanje.si/"),
        ("LV_eis", "https://www.eis.gov.lv/EIS/Procurement/Procurements.aspx"),
        ("CY_eproc", "https://www.eprocurement.gov.cy/ceproc/home.do"),
        ("MT_etenders", "https://www.etenders.gov.mt/epps/home.do"),
    ]:
        try:
            r = s.get(url, headers=UA, timeout=35)
            misc[name] = {
                "http": r.status_code,
                "len": len(r.content),
                "loginish": any(x in r.text.lower() for x in ("login", "sign in", "password", "captcha")),
                "snip": r.text[:300].replace("\n", " "),
            }
        except Exception as e:
            misc[name] = {"error": str(e)[:200]}
    out["sections"]["MISC"] = misc

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
