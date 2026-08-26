#!/usr/bin/env python3
"""Probe whether order[createdAt]=desc + client filter can make CZ LIVE."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Origin": "https://vvz.nipez.cz",
    "Referer": "https://vvz.nipez.cz/",
}
OUT = Path(__file__).with_name("_probe_cz_live_path.json")
KW = (
    "nakladni",
    "nákladní",
    "užitkov",
    "uzitkov",
    "pickup",
    "pick-up",
    "podvozek",
    "isuzu",
    "d-max",
    "valník",
    "sklápěč",
    "dodávka",
    "automobil",
    "vozidel",
    "vozidla",
    "vozidlo",
    "chassis",
    "truck",
    "kamion",
    "kamión",
    "fleet",
    "servis vozidel",
    "oprava vozidel",
    "údržba vozidel",
    "motorov",
    "užitkové",
)


def main() -> None:
    s = requests.Session()
    out: dict = {"filter_tries": [], "scan": {}}

    tests = [
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 3, "order[createdAt]": "desc", "workflowPlace": "UVEREJNENO_VVZ"},
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 3, "order[createdAt]": "desc", "workflowPlaceCode": "UVEREJNENO_VVZ"},
        {"formGroup": "vz", "form": "hlavni", "page": 1, "limit": 3, "order[createdAt]": "desc"},
        {"formGroup": "vz", "form": "F02", "page": 1, "limit": 3, "order[createdAt]": "desc"},
        {"formGroup": "VZ", "form": "HLAVNI", "page": 1, "limit": 3, "order[createdAt]": "desc"},
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 3, "data.nazevZakazky": "nákladní"},
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 3, "data.druhFormulare": "F02"},
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 3, "druhFormulare": "F02"},
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 3, "order[createdAt]": "desc", "createdAt[gte]": "2026-08-01"},
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 3, "order[createdAt]": "desc", "createdAt": "2026-08-01"},
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 3, "order[createdAt]": "desc", "createdAt[strictly_after]": "2026-08-01"},
        {"formGroup": "vz", "form": "vz", "page": 1, "limit": 3, "order[createdAt]": "desc", "createdAt[after]": "2026-08-01T00:00:00+02:00"},
    ]
    for p in tests:
        r = s.get("https://api.vvz.nipez.cz/api/submissions/search", params=p, headers=UA, timeout=40)
        total = r.headers.get("X-Total-Count")
        items = r.json() if r.status_code == 200 and r.content[:1] == b"[" else []
        row = {
            "extra": {k: v for k, v in p.items() if k not in ("formGroup", "form", "page", "limit")},
            "form": p.get("form"),
            "http": r.status_code,
            "total": total,
            "n": len(items) if isinstance(items, list) else None,
            "snip": r.text[:180].replace("\n", " ") if r.status_code != 200 else None,
        }
        if items:
            d = items[0].get("data") or {}
            row["sample_title"] = str(d.get("nazevZakazky") or "")[:80]
            row["sample_wf"] = items[0].get("workflowPlaceCode")
            row["sample_created"] = items[0].get("createdAt")
            row["sample_keys"] = list(d.keys())[:20] if isinstance(d, dict) else []
        out["filter_tries"].append(row)
        print("TRY", row["extra"] or row["form"], "http", row["http"], "total", total)

    # Scan recent pages for vehicle KW + field shapes
    all_keys: Counter = Counter()
    titles = []
    cpv_hits = []
    wf_counts: Counter = Counter()
    dates = []
    for page in range(1, 11):
        r = s.get(
            "https://api.vvz.nipez.cz/api/submissions/search",
            params={"formGroup": "vz", "form": "vz", "page": page, "limit": 50, "order[createdAt]": "desc"},
            headers=UA,
            timeout=45,
        )
        items = r.json() if r.status_code == 200 else []
        print("page", page, "n", len(items), "total", r.headers.get("X-Total-Count"))
        for it in items:
            wf_counts[str(it.get("workflowPlaceCode") or "?")] += 1
            dates.append((it.get("createdAt") or "")[:10])
            data = it.get("data") or {}
            if not isinstance(data, dict):
                continue
            for k in data.keys():
                all_keys[k] += 1
            title = str(data.get("nazevZakazky") or "")
            blob = json.dumps(data, ensure_ascii=False).lower()
            if any(k in blob for k in KW):
                titles.append(
                    {
                        "title": title[:140],
                        "wf": it.get("workflowPlaceCode"),
                        "created": (it.get("createdAt") or "")[:19],
                        "keys": list(data.keys())[:30],
                        "druh": data.get("druhFormulare"),
                        "cpv_fields": {ck: data[ck] for ck in data if "cpv" in ck.lower() or "klasifik" in ck.lower()},
                    }
                )
            for ck in data:
                if "cpv" in ck.lower() or "klasifik" in ck.lower():
                    cpv_hits.append({"field": ck, "val": str(data[ck])[:80], "title": title[:80]})

    out["scan"] = {
        "pages": 10,
        "items": sum(wf_counts.values()),
        "wf_counts": dict(wf_counts.most_common(20)),
        "date_min": min(dates) if dates else None,
        "date_max": max(dates) if dates else None,
        "unique_data_keys": all_keys.most_common(50),
        "kw_hits": len(titles),
        "kw_sample": titles[:25],
        "cpv_field_hits": len(cpv_hits),
        "cpv_sample": cpv_hits[:15],
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("kw_hits", len(titles), "cpv_fields", len(cpv_hits), "date_range", out["scan"]["date_min"], "→", out["scan"]["date_max"])
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
