# 01 — Operator runbook

**Audience:** Jerome / eng  
**Updated:** 2026-08-25  
**Install:** `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\`

## Weekly run

1. Double-click `run_tender_monitor.bat`
2. Open v4: double-click `OPEN_isze_dashboard_v4_opportunity.cmd`
3. If Nordics still warn: see `NORDICS_API_KEYS.md` and `_NORDICS_BLOCKED.md`

## Keys (never into `.py`)

| Need | File |
|---|---|
| Norway / Finland | `nordics_api_keys.env` from `nordics_api_keys.env.example` |
| Verify | `python verify_nordics_keys.py` (never prints secrets) |
| Optional BE SPA client | `isze_secrets.env` from example |

## What “broken” means now

| Status | Meaning |
|---|---|
| `OK` | Feed returning data |
| `AWAITING_KEY` | Endpoint fine — Jerome must register keys (Nordics) |
| `RETIRED` / `WONTFIX` | Portal abandoned on purpose (BE RSS, IL RSS, DTVP) — not a red failure |
| `SUSPECT` | Secondary / thin (e.g. IL CKAN frozen) |
| `BROKEN` | Unexpected failure of an *active* fetcher |

Live health: `_source_health.json` + v4 banner.

## Install detail

Full pip / troubleshooting: `SETUP.txt`.  
SteerCo five-minute story: `00_EXEC_ONE_PAGER.html` (double-click `OPEN_00_EXEC_ONE_PAGER.cmd`).  
Quality bar: `_GODTIER_CHECKLIST.md` (re-measure figures against live before trusting PASS).  
Eng backlog: `_OPEN_BACKLOG_ARRANGED.md`.
