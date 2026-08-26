# P3 — TED detail enrichment

**Date:** 2026-08-25  
**Status:** **PARTIAL / NEXT** — safe capped code path landed; live detail GET **blocked on TED Authorization**

## Before (list search only — current gated snapshot)

| Metric | TED notices (n=192) |
|---|---:|
| Deadline populated | **12.5%** |
| Est. Value populated | **0.0%** |
| FleetSize populated | **7.8%** |

Source: `isze_dashboard_v4_data.json` notices with Source containing EU.

## What landed in code

`tender_scraper_v3.py`:

- `ISZE_TED_FETCH_DETAIL=1` enables detail enrichment (default **OFF** — weekly bat safe)
- `ISZE_TED_DETAIL_CAP` default **40** — only matched/gated thin rows, prefer missing deadline/value/fleet
- `ISZE_TED_DETAIL_DELAY` default **0.5s**
- Enrichment runs **after** keyword+CPV filter (never every TED hit)
- Does **not** touch Contracts Finder (no CF melt)

## Probe result (8 sample notice IDs)

```
GET https://api.ted.europa.eu/v3/notices/{ND}
→ HTTP 400 Missing Authorization header in request
```

List `POST /v3/notices/search` stays public (200). Detail endpoint requires API auth.

## After %

**Cannot measure** until a TED API key / Authorization header is available. Enabling the flag today would burn the cap on 400s.

## NEXT (crisp)

1. Register / obtain TED API v3 credentials (EU Publications Office developer portal).
2. Load key via env (e.g. `ISZE_TED_API_KEY`) — **never** commit.
3. Attach `Authorization` on `fetch_ted_detail` only.
4. Run one focused enrich: `set ISZE_TED_FETCH_DETAIL=1` + small cap → report before/after % again.
5. Keep default OFF in `run_tender_monitor.bat` until after % proves lift.
