#!/usr/bin/env python3
"""Deep-probe CZ date+form filters and vehicle hit yield over lookback."""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
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
OUT = Path(__file__).with_name("_probe_cz_yield.json")

# Tight CV / LCV / R&M — avoid bare automobil noise where possible
CZ_TIGHT = (
    "nákladní",
    "nakladni",
    "užitkov",
    "uzitkov",
    "pickup",
    "pick-up",
    "podvozek",
    "isuzu",
    "d-max",
    "d max",
    "valník",
    "valnik",
    "sklápěč",
    "sklapec",
    "dodávka",
    "dodavka",
    "kamion",
    "kamión",
    "chassis",
    "truck",
    "lcv",
    "fleet",
    "vozový park",
    "vozovy park",
    "servis vozidel",
    "oprava vozidel",
    "údržba vozidel",
    "udrzba vozidel",
    "údržba automobil",
    "servis automobil",
    "oprava automobil",
    "motorových vozidel",
    "motorovych vozidel",
    "služební automobil",
    "sluzebni automobil",
    "užitkové vozidlo",
    "uzitkove vozidlo",
    "nákladní automobil",
    "nakladni automobil",
    "nákladní vozidlo",
    "přípojné vozidlo",
    "prives",
    "přívěs",
    "návěs",
    "naves",
)

# Broader (may need noise filter)
CZ_BROAD = (
    "automobil",
    "vozidel",
    "vozidla",
    "vozidlo",
    "vozový",
)

NOISE = (
    "stavebn",
    "rekonstrukc",
    "silnic",
    "asfalt",
    "vodovod",
    "kanaliz",
    "softwar",
    "informačn",
    "informacn",
    "nábytek",
    "nabytek",
    "potravin",
    "léčiv",
    "leciv",
    "zdravotn",
    "úklid",
    "uklid",
)


def _hit(blob: str) -> str | None:
    b = blob.lower()
    if any(t in b for t in CZ_TIGHT):
        return "tight"
    if any(t in b for t in CZ_BROAD):
        if any(n in b for n in NOISE):
            return None
        return "broad"
    return None


def main() -> None:
    s = requests.Session()
    lookback = 30
    since = (datetime.now(timezone.utc) - timedelta(days=lookback)).strftime("%Y-%m-%d")
    out: dict = {"since": since, "lookback_days": lookback}

    # Filter matrix
    matrix = []
    for params in [
        {"formGroup": "vz", "form": "vz", "createdAt[gte]": since, "order[createdAt]": "desc"},
        {"formGroup": "vz", "form": "vz", "createdAt[gte]": since, "order[createdAt]": "desc", "workflowPlace": "UVEREJNENO_VVZ"},
        {"formGroup": "vz", "form": "vz", "createdAt[gte]": since, "data.druhFormulare": "F02"},
        {"formGroup": "vz", "form": "vz", "createdAt[gte]": since, "data.druhFormulare": "F01"},
        {"formGroup": "vz", "form": "vz", "createdAt[gte]": since, "data.druhFormulare": "CZ02"},
        {"formGroup": "vz", "form": "vz", "createdAt[gte]": since, "data.druhFormulare": "B2"},
        {"formGroup": "vz", "form": "vz", "createdAt[gte]": since, "data.druhFormulare": "CN"},
        {"formGroup": "vz", "form": "vz", "createdAt[gte]": since + "T00:00:00+02:00", "order[createdAt]": "desc"},
    ]:
        r = s.get("https://api.vvz.nipez.cz/api/submissions/search", params={**params, "page": 1, "limit": 5}, headers=UA, timeout=40)
        items = r.json() if r.status_code == 200 and r.content[:1] == b"[" else []
        matrix.append({
            "params": {k: v for k, v in params.items() if k not in ("formGroup", "form")},
            "http": r.status_code,
            "total": r.headers.get("X-Total-Count"),
            "sample_created": (items[0].get("createdAt") if items else None),
            "sample_druh": (items[0].get("data") or {}).get("druhFormulare") if items else None,
            "sample_title": str((items[0].get("data") or {}).get("nazevZakazky") or "")[:80] if items else None,
        })
        print("matrix", matrix[-1]["params"], "→", matrix[-1]["http"], matrix[-1]["total"])
    out["matrix"] = matrix

    # Page through date-filtered window and count vehicle hits
    base = {
        "formGroup": "vz",
        "form": "vz",
        "createdAt[gte]": since,
        "order[createdAt]": "desc",
        "limit": 50,
    }
    hits = []
    druhs: Counter = Counter()
    wfs: Counter = Counter()
    pages_done = 0
    max_pages = 80  # 4000 items max
    total_items = 0
    oldest = None
    newest = None
    for page in range(1, max_pages + 1):
        r = s.get(
            "https://api.vvz.nipez.cz/api/submissions/search",
            params={**base, "page": page},
            headers=UA,
            timeout=45,
        )
        if r.status_code != 200:
            print("stop http", r.status_code, r.text[:120])
            break
        items = r.json()
        if not items:
            break
        pages_done += 1
        total_items += len(items)
        if page == 1:
            print("window total header", r.headers.get("X-Total-Count"))
            out["window_total"] = r.headers.get("X-Total-Count")
        for it in items:
            data = it.get("data") if isinstance(it.get("data"), dict) else {}
            druhs[str(data.get("druhFormulare") or "?")] += 1
            wfs[str(it.get("workflowPlaceCode") or "?")] += 1
            created = (it.get("createdAt") or "")[:19]
            if created:
                oldest = created if oldest is None or created < oldest else oldest
                newest = created if newest is None or created > newest else newest
            title = str(data.get("nazevZakazky") or "")
            buyer = ""
            z = data.get("zadavatele")
            if isinstance(z, list) and z and isinstance(z[0], dict):
                buyer = str(z[0].get("nazev") or "")
            blob = json.dumps(data, ensure_ascii=False)
            kind = _hit(blob)
            if not kind:
                continue
            hits.append({
                "kind": kind,
                "title": title[:160],
                "buyer": buyer[:80],
                "created": created,
                "druh": data.get("druhFormulare"),
                "wf": it.get("workflowPlaceCode"),
                "id": it.get("id"),
                "variableId": it.get("variableId"),
                "pub": str(data.get("datumUverejneniVvz") or "")[:10],
            })
        if len(items) < 50:
            break
        if page % 10 == 0:
            print(f"  page {page} items={total_items} hits={len(hits)}")

    out["scan"] = {
        "pages": pages_done,
        "items": total_items,
        "oldest": oldest,
        "newest": newest,
        "druh_top": druhs.most_common(25),
        "wf_top": wfs.most_common(15),
        "hits_n": len(hits),
        "hits_tight": sum(1 for h in hits if h["kind"] == "tight"),
        "hits_broad": sum(1 for h in hits if h["kind"] == "broad"),
        "hits": hits[:40],
    }
    print(f"DONE items={total_items} hits={len(hits)} tight={out['scan']['hits_tight']} broad={out['scan']['hits_broad']}")
    print("druh top", druhs.most_common(12))
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
