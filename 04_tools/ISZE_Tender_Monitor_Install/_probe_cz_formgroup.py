#!/usr/bin/env python3
"""CZ VVZ: submissions/search needs formGroup. Probe public form groups + BG CPV-tight hits."""
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
OUT = HERE / "_probe_cz_formgroup.json"
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://vvz.nipez.cz",
    "Referer": "https://vvz.nipez.cz/",
}


def main() -> None:
    s = requests.Session()
    out: dict = {"probed_at": datetime.now(timezone.utc).isoformat()}

    js = s.get("https://vvz.nipez.cz/static/js/main.e8045595.js", headers=UA, timeout=90).text
    # find formGroup enum values
    groups = sorted(set(re.findall(r'formGroup["\']?\s*[:=]\s*["\']([A-Za-z0-9_\-]+)["\']', js)))
    groups2 = sorted(set(re.findall(r'["\'](FORM_GROUP_[A-Z0-9_]+)["\']', js)))
    groups3 = sorted(set(re.findall(r'formGroup[=:]["\']?([A-Za-z0-9_\-]+)', js)))
    # Czech form codes F01 F02 CZ01 etc
    fcodes = sorted(set(re.findall(r'["\']((?:F|CZ)\d{2})["\']', js)))
    out["formGroup_hits"] = groups[:50]
    out["FORM_GROUP"] = groups2[:50]
    out["fcodes_sample"] = fcodes[:40]
    # context around formGroup
    ctx = []
    for m in re.finditer(r".{0,50}formGroup.{0,80}", js):
        ctx.append(m.group(0).replace("\n", " "))
        if len(ctx) >= 15:
            break
    out["formGroup_ctx"] = ctx

    # Try known eForms groups
    candidates = [
        "F02", "F01", "F03", "CN", "CONTRACT_NOTICE", "NOTICE", "PUBLICATION",
        "FORM", "SUBMISSION", "ZAKAZKA", "NOVE", "ALL", "1", "2",
        "ContractNotice", "PriorInformationNotice", "contract-notice",
    ] + fcodes[:20] + groups[:20] + groups2[:20]
    seen = set()
    tries = []
    for fg in candidates:
        if not fg or fg in seen:
            continue
        seen.add(fg)
        url = f"https://api.vvz.nipez.cz/api/submissions/search?formGroup={urllib.parse.quote(fg)}&page=1&size=5"
        try:
            r = s.get(url, headers=UA, timeout=25)
        except Exception as e:
            tries.append({"fg": fg, "error": str(e)[:120]})
            continue
        row = {"fg": fg, "http": r.status_code, "len": len(r.content), "snip": r.text[:220].replace("\n", " ")}
        if r.status_code == 200 and r.content[:1] in (b"{", b"["):
            try:
                data = r.json()
                row["type"] = type(data).__name__
                if isinstance(data, list):
                    row["n"] = len(data)
                    if data and isinstance(data[0], dict):
                        row["keys"] = list(data[0].keys())[:20]
                elif isinstance(data, dict):
                    row["keys"] = list(data.keys())[:20]
            except Exception:
                pass
            print("HIT", fg, r.status_code, len(r.content))
        elif r.status_code not in (400, 404):
            print("?", fg, r.status_code, r.text[:80])
        tries.append(row)
        if r.status_code == 200:
            break
    out["tries"] = tries

    # Also try forms?page=1
    r = s.get("https://api.vvz.nipez.cz/api/forms?page=1&size=20", headers=UA, timeout=25)
    out["forms_page1"] = {"http": r.status_code, "len": len(r.content), "snip": r.text[:400]}

    # BG CPV-tight recount
    day = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    list_url = f"https://storage.eop.bg/open-data-{day}/"
    lr = s.get(list_url, headers=UA, timeout=40)
    keys = re.findall(r"<Key>([^<]+)</Key>", lr.text)
    ocds_key = next((k for k in keys if "OCDS" in k.upper()), None)
    file_url = list_url + urllib.parse.quote(ocds_key)
    pkg = s.get(file_url, headers=UA, timeout=120).json()
    releases = pkg.get("releases") or []
    CPV = ("3410", "3411", "3413", "3414", "5011")
    KW = (
        "камион", "пикап", "шаси", "isuzu", "d-max", "n-series",
        "товарни автомобил", "лек товарн", "пикап", "шаси кабин",
        "бордова", "самосвал", "ремарке", "truck", "pickup", "chassis",
        "поддръжка на автопарк", "сервиз на автомобил",
    )
    hits_cpv, hits_kw = [], []
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
        # also tender classification
        tclas = tender.get("classification") or {}
        if isinstance(tclas, dict) and tclas.get("id"):
            cpvs.append(str(tclas["id"]))
        cpv_ok = any(any(c.startswith(p) for p in CPV) for c in cpvs)
        kw_ok = any(k in blob for k in KW)
        tid = tender.get("id") or ""
        if cpv_ok:
            hits_cpv.append({"title": title[:140], "cpvs": cpvs[:6], "id": tid})
        elif kw_ok:
            hits_kw.append({"title": title[:140], "cpvs": cpvs[:6], "id": tid})
    out["bg_tight"] = {
        "n_releases": len(releases),
        "cpv_hits": len(hits_cpv),
        "kw_only_hits": len(hits_kw),
        "cpv_sample": hits_cpv[:12],
        "kw_sample": hits_kw[:12],
    }
    print(f"BG tight CPV={len(hits_cpv)} KW={len(hits_kw)}")

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
