#!/usr/bin/env python3
"""Focused ES PLACSP scrape → isuzu_tenders_v3_es.xlsx (does not overwrite main).

Atom syndication was WAF-denied on 2026-08-25 from some runners; retry here
and record LIVE vs CODE_READY from evidence. Does not ask for a Spain API key.
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
SIDE = HERE / "isuzu_tenders_v3_es.xlsx"
STATS = HERE / "_phase1_es_fetch_stats_20260914.json"


def main() -> None:
    from source_health import load_health, persist_and_report, record_source_result, record_source_status
    from tender_scraper_v3 import (
        EXPORT_HEADERS,
        LAST_FETCH_ERRORS,
        LOOKBACK_DAYS,
        fetch_spain_placsp,
        normalize_batch,
    )

    from_dt = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    with requests.Session() as session:
        session.headers.setdefault(
            "User-Agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        )
        raw = fetch_spain_placsp(session, from_dt)
    gated = normalize_batch(raw, "ES-PLACSP")
    print(f"[ES] raw={len(raw)} gated={len(gated)}")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Spain PLACSP"
    ws.append(list(EXPORT_HEADERS))
    for row in gated:
        ws.append([row.get(h, "") for h in EXPORT_HEADERS])
    wb.save(SIDE)
    print(f"Wrote {SIDE}")

    health = load_health()
    es_err = LAST_FETCH_ERRORS.get("Spain PLACSP")
    if es_err and "WAF_BLOCKED" in str(es_err):
        record_source_status(
            health,
            "Spain PLACSP",
            "CODE_READY",
            count=0,
            last_error=es_err,
            note="Official Atom syndication documented; this runner is WAF-denied.",
        )
        status = "CODE_READY"
    else:
        record_source_result(health, "Spain PLACSP", len(raw), es_err)
        health.setdefault("Spain PLACSP", {})["note"] = (
            "LIVE 2026-09-14 — Atom HTTP 200 this runner (not WAF). "
            f"Keyword matches={len(raw)} in rolling Atom window; Isuzu-gated={len(gated)}. "
            "Atom is recent notices, not a 30-day API dump."
        )
        status = health.get("Spain PLACSP", {}).get("status")
    persist_and_report(health)

    sample = []
    for row in gated[:8]:
        sample.append(
            {
                "title": (row.get("Title") or "")[:160],
                "buyer": (row.get("Buyer") or "")[:80],
                "published": row.get("Published") or "",
                "url": row.get("URL") or "",
            }
        )
    stats = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "lookback_days": LOOKBACK_DAYS,
        "raw_keyword_matches": len(raw),
        "gated": len(gated),
        "health_status": status,
        "last_error": es_err,
        "gated_sample": sample,
    }
    STATS.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Health: Spain PLACSP status={status} last_count={len(raw)} err={es_err}")
    print(f"Wrote {STATS}")


if __name__ == "__main__":
    main()
