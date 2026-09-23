#!/usr/bin/env python3
"""Focused ES + IT + DE national scrape → side xlsx + dated probe JSON + health.

Does not overwrite main isuzu_tenders_v3.xlsx. Does not invent fleet/SPU.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import openpyxl
import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
SIDE = HERE / "isuzu_tenders_v3_es_it_de.xlsx"
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
PROBE_JSON = HERE / f"_probe_es_it_de_{TODAY}.json"


def main() -> None:
    from national_fetchers_de import fetch_germany_ov
    from national_fetchers_es import fetch_spain_placsp
    from national_fetchers_it import fetch_italy_pncp
    from source_health import (
        load_health,
        persist_and_report,
        record_source_result,
        record_source_status,
    )
    from tender_scraper_v3 import EXPORT_HEADERS, LOOKBACK_DAYS, normalize_batch

    from_dt = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    session = requests.Session()
    errors: dict = {}

    es_raw = fetch_spain_placsp(session, from_dt, errors=errors)
    it_raw = fetch_italy_pncp(session, from_dt, max_pages=15, errors=errors)
    de_raw = fetch_germany_ov(session, from_dt, errors=errors)

    es_gated = normalize_batch(es_raw, "🇪🇸 ES-PLACSP")
    it_gated = normalize_batch(it_raw, "🇮🇹 IT-PNCP")
    de_gated = normalize_batch(de_raw, "🇩🇪 DE-OV")

    print(
        f"[ES] raw={len(es_raw)} gated={len(es_gated)} | "
        f"[IT] raw={len(it_raw)} gated={len(it_gated)} | "
        f"[DE] raw={len(de_raw)} gated={len(de_gated)}"
    )

    wb = openpyxl.Workbook()
    sheets = [
        ("Spain PLACSP", es_gated, "No ES PLACSP results"),
        ("Italy PNCP", it_gated, "No IT PNCP results"),
        ("Germany OV", de_gated, "No DE OV results"),
    ]
    first = True
    for title, rows, empty_msg in sheets:
        ws = wb.active if first else wb.create_sheet(title)
        if first:
            ws.title = title
            first = False
        ws.append(list(EXPORT_HEADERS))
        if not rows:
            ws.append([empty_msg] + [""] * (len(EXPORT_HEADERS) - 1))
        else:
            for row in rows:
                ws.append([row.get(h, "") for h in EXPORT_HEADERS])
    wb.save(SIDE)
    print(f"Wrote {SIDE}")

    health = load_health()
    es_err = errors.get("Spain PLACSP")
    if es_err and "WAF_BLOCKED" in str(es_err):
        record_source_status(
            health,
            "Spain PLACSP",
            "CODE_READY",
            count=0,
            last_error=es_err,
            note=(
                "Official Atom/ZIP syndication documented; this runner is WAF-denied. "
                "Not BROKEN — retry when egress/session allows."
            ),
        )
    else:
        record_source_result(health, "Spain PLACSP", len(es_raw), es_err)
        # Clear stale WAF note when live
        if health.get("Spain PLACSP") and not es_err:
            health["Spain PLACSP"]["note"] = (
                "Atom syndication LIVE (rel=next walk); vehicle stem/CPV client filter"
            )
    record_source_result(health, "Italy PNCP", len(it_raw), errors.get("Italy PNCP"))
    record_source_result(
        health,
        "Germany oeffentlichevergabe",
        len(de_raw),
        errors.get("Germany oeffentlichevergabe"),
    )
    persist_and_report(health)

    probe = {
        "probed_at": datetime.now(timezone.utc).isoformat(),
        "lookback_days": LOOKBACK_DAYS,
        "from_dt": from_dt.isoformat(),
        "counts": {
            "Spain PLACSP": {
                "raw": len(es_raw),
                "gated": len(es_gated),
                "error": errors.get("Spain PLACSP"),
            },
            "Italy PNCP": {
                "raw": len(it_raw),
                "gated": len(it_gated),
                "error": errors.get("Italy PNCP"),
            },
            "Germany oeffentlichevergabe": {
                "raw": len(de_raw),
                "gated": len(de_gated),
                "error": errors.get("Germany oeffentlichevergabe"),
            },
        },
        "sample_titles": {
            "ES": [(r.get("Title") or "")[:120] for r in es_raw[:5]],
            "IT": [(r.get("Title") or "")[:120] for r in it_raw[:5]],
            "DE": [(r.get("Title") or "")[:120] for r in de_raw[:5]],
        },
        "side_xlsx": str(SIDE),
        "modules": [
            "national_fetchers_es.py",
            "national_fetchers_it.py",
            "national_fetchers_de.py",
        ],
    }
    PROBE_JSON.write_text(json.dumps(probe, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {PROBE_JSON}")


if __name__ == "__main__":
    main()
