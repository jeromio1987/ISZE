#!/usr/bin/env python3
"""Record remaining dark/CODE_READY health — CZ is LIVE (do not reset)."""
from source_health import load_health, persist_and_report, record_source_status

h = load_health()
# Czechia VVZ is LIVE via national_fetchers_cz.py — leave OK status from scrape_cz_side.
record_source_status(
    h,
    "Lithuania CVP IS",
    "CODE_READY",
    count=0,
    last_error="POST cft-details-export returns 401 without VPT apiKey — CODE_READY",
)
record_source_status(
    h,
    "Estonia RHR",
    "BLOCKED",
    count=0,
    last_error="rhr/api/public/v1/opendata HTTP 500 — wait for ministry fix",
)
record_source_status(
    h,
    "Slovakia UVO",
    "BLOCKED",
    count=0,
    last_error="Vestnik HTML recaptcha; no free list API",
)
record_source_status(
    h,
    "Greece KIMDIS",
    "BLOCKED",
    count=0,
    last_error="Open-data URL is login shell; need Promitheus credentials",
)
persist_and_report(h)
print("ok")
