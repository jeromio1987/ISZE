#!/usr/bin/env python3
"""Find CZ VVZ date/sort filter params from SPA JS + probe."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Origin": "https://vvz.nipez.cz",
    "Referer": "https://vvz.nipez.cz/",
}
OUT = Path(__file__).with_name("_probe_cz_date_filter.json")


def main() -> None:
    s = requests.Session()
    js = s.get("https://vvz.nipez.cz/static/js/main.e8045595.js", headers=UA, timeout=90).text
    # params near getSubmissionsSearch
    ctx = []
    for m in re.finditer(r".{0,30}getSubmissionsSearch.{0,200}", js):
        ctx.append(m.group(0).replace("\n", " "))
        if len(ctx) >= 12:
            break
    # filter field names
    fields = sorted(set(re.findall(
        r"(?:createdAt|updatedAt|published|datum|dateFrom|dateTo|from|to|order|sort|fulltext|cpv|workflowPlace)[A-Za-z0-9_]*",
        "\n".join(ctx),
        flags=re.I,
    )))
    # broader search for date filter keys in JS
    date_keys = sorted(set(re.findall(
        r'["\']([a-zA-Z]*[Dd]ate[a-zA-Z]*|[a-zA-Z]*[Ff]rom[a-zA-Z]*|[a-zA-Z]*[Tt]o[a-zA-Z]*)["\']',
        js,
    )))
    out = {"ctx": ctx, "fields_near_search": fields, "date_keys_sample": [k for k in date_keys if any(x in k.lower() for x in ("date", "from", "to", "pub", "uvere")) ][:60]}

    # Probe date-ish params
    tries = []
    for params in [
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 5, "order[createdAt]": "desc"},
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 5, "order[updatedAt]": "desc"},
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 5, "createdAt[after]": "2026-07-01"},
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 5, "updatedAt[after]": "2026-07-01"},
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 5, "createdAt.from": "2026-07-01"},
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 5, "dateFrom": "2026-07-01", "dateTo": "2026-08-25"},
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 5, "publicId": "Z2026"},
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 5, "variableId": "Z2026-032036"},
    ]:
        r = s.get("https://api.vvz.nipez.cz/api/submissions/search", params=params, headers=UA, timeout=40)
        total = r.headers.get("X-Total-Count")
        items = r.json() if r.status_code == 200 and r.content[:1] == b"[" else []
        dates = []
        for it in items[:3]:
            dates.append({"createdAt": it.get("createdAt"), "updatedAt": it.get("updatedAt"), "publicId": it.get("publicId")})
        tries.append({"params": params, "http": r.status_code, "total": total, "dates": dates})
        print("total", total, "params", {k: v for k, v in params.items() if k not in ("formGroup", "form", "page", "limit")})

    out["tries"] = tries
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
