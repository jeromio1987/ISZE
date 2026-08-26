# Operator index — ISZE Tender Engine

**Folder:** `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\`  
**Updated:** 2026-08-25 (paper deep review)

## Start here (5 minutes)

1. SteerCo one-pager → double-click `OPEN_00_EXEC_ONE_PAGER.cmd`
2. Working dashboard → double-click `OPEN_isze_dashboard_v4_opportunity.cmd`
3. Deep paper audit → `_PAPER_DEEP_REVIEW.md`

## What it is

Weekly European tender radar for Isuzu LCV + fleet R&M, scored and framed as GPS addressable opportunity (if won) — never as expected revenue.

## How to run

| Action | How |
|---|---|
| Full weekly job | Double-click `run_tender_monitor.bat` |
| Open v4 dashboard | Double-click `OPEN_isze_dashboard_v4_opportunity.cmd` |
| Exec one-pager | Double-click `OPEN_00_EXEC_ONE_PAGER.cmd` |
| Nordics keys | **DONE** — `_NORDICS_BLOCKED.md` · never re-ask Jerome · diagnose silently if health flips |
| Ops detail | `01_OPERATOR_RUNBOOK.md` · install `SETUP.txt` |

## Live snapshot (2026-08-25)

| Figure | Value |
|---|---:|
| Notices / opportunities | **211 / 186** |
| GPS floor € / yr (sized pickup/truck) | **€1,488.22** (3 rows) |
| With fleet in notice | **13** |
| Coverage vs dark (band) | **~35–55%** Medium |

## What is limited right now

See v4 banner / `_source_health.json`:

- Norway Doffin / Finland HILMA → **OK / LIVE** (keys DONE — `_NORDICS_BLOCKED.md`; **never re-ask Jerome for keys**)
- Germany DTVP → **RETIRED** (TED + service.bund only)
- Belgium RSS / Israel RSS → **RETIRED** (live SEA + mr.gov.il are OK)
- Most opportunities unsized for GPS (no fleet and/or no SPU map and/or van product-fit)

## What the headline numbers mean

| Figure | Meaning |
|---|---|
| Addressable GPS / year (sized floor) | Sum of `fleet × (max_spend/uio)` on **pickup/truck** sized rows only |
| Published contract value | Sum of known Est. Values only; missing excluded |
| Unsized for GPS | Count with null GPS — honest, not zeroed |

## Paper tree (god-tier path)

| Doc | Role |
|---|---|
| `00_EXEC_ONE_PAGER.html` | SteerCo five-minute story |
| `01_OPERATOR_RUNBOOK.md` | Run / keys / health vocabulary |
| `02_METHOD_GPS_PRODUCT_FIT.md` | GPS + product-fit definitions |
| `_NOT_FOR_US_GATE.md` | Why postal/courier panel vans leave the desk |
| `_PRODUCT_FIT_GATE.md` | GPS € only on pickup/truck; vans hard-dropped |
| `03_COVERAGE_DARK_MAP.md` | Coverage band + gaps |
| `_PAPER_DEEP_REVIEW.md` | Full truth audit of the paper pack |
| `_IDS_DEALER_MODULE.md` | IDS dealer ↔ MAP (sources, fields, match methods) |
| `_OPEN_BACKLOG_ARRANGED.md` | Eng P0–P4 status |
| `_GODTIER_CHECKLIST.md` | Quality bar (re-measure before trusting PASS) |
| `CURSOR_PROMPTS_v4_engine.md` | Design pack (SHIPPED — historical body OK) |
| `_phase1_*` / `_AUDIT_*` / `CURSOR_WORKFILE_*` | **Historical** — not current headlines |

## IDS dealer / MAP

**DONE (engine).** Module: `ids_dealer_linkage.py` · facts: `_IDS_DEALER_MODULE.md`

| Live fact (same snapshot as GPS floor) | Value |
|---|---|
| IDS dealers loaded | **519** from `IDS_2026_all_country_rankings.xlsx` |
| Opps with IDS dealer assigned | **113** / 186 (`country_primary` 72 · `geo_nearest` 41) |
| Opps dealer-unmapped | **73** (no IDS country sheet and/or no yaml distributor) |
| Romania example | Distributor `ROMANIA` (ROM Auto) · dealer e.g. `RODAV` (rank #1) or city hit |
| Germany example | Distributor `GERMANY` (ISUZU SALES DEUTSCHLAND GMBH) · **dealer unmapped** — no DE IDS tab on disk |

No invented dealers. Germany stays distributor-only until a `Germany_dealer_ranking.xlsx` / DE tab lands. Dashboard column: **Dealer / IDS** (hover = match method).
