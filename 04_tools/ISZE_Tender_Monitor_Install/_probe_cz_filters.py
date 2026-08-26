#!/usr/bin/env python3
"""Inspect CZ item shape + whether fulltext/CPV filters work."""
from __future__ import annotations

import json
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
OUT = Path(__file__).with_name("_cz_item_shape.json")


def main() -> None:
    s = requests.Session()
    tests = []
    for params in [
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 2, "fulltext": "isuzu"},
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 2, "fulltext": "nákladní automobil"},
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 2, "cpv": "34100000"},
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 2, "data.cpv": "34100000"},
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 2, "variableId": "3410"},
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 2, "workflowPlace": "UVEREJNENO_VVZ"},
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 2, "workflowPlaceCode": "UVEREJNENO_VVZ"},
    ]:
        r = s.get("https://api.vvz.nipez.cz/api/submissions/search", params=params, headers=UA, timeout=40)
        total = r.headers.get("X-Total-Count")
        items = r.json() if r.status_code == 200 else []
        titles = []
        if isinstance(items, list):
            for it in items[:2]:
                data = it.get("data") or {}
                titles.append({
                    "publicId": it.get("publicId"),
                    "id": it.get("id"),
                    "variableId": it.get("variableId"),
                    "workflow": it.get("workflowPlaceCode"),
                    "data_keys": list(data.keys())[:40] if isinstance(data, dict) else type(data).__name__,
                    "data_sample": {k: data.get(k) for k in list(data.keys())[:15]} if isinstance(data, dict) else None,
                })
        tests.append({"params": params, "http": r.status_code, "total": total, "n": len(items) if isinstance(items, list) else None, "titles": titles})
        print(params.get("fulltext") or params.get("cpv") or params.get("workflowPlace") or params.get("workflowPlaceCode"), "total=", total)

    OUT.write_text(json.dumps(tests, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
