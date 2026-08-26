# Tender Engine v4 — release notes

**Date:** 2026-08-25  
**Baseline:** v3 audit `_AUDIT_v3_baseline.md` (778 notices / 680 opps on 2026-08-24 feed)  
**v4 extraction build:** 773 notices / 679 opportunities (pre-gate)  
**God-tier Isuzu gate (same day):** **193 notices / 172 opportunities** on rebuild from the same xlsx

---

## What changed

### Phase 1 — Source layer
- `_source_health.json` + `source_health.py`: OK / SUSPECT / BROKEN; loud end-of-run report.
- **Israel:** CKAN datastore on data.gov.il (RSS retired).
- **Belgium:** national feed still BROKEN (SPA); validation shouts instead of silent 0.
- **Doffin / HILMA:** keys via `nordics_keys.py` + `nordics_api_keys.env` (never commit keys). Also loads `isze_secrets.env` / `.env`.
- **TED:** CYP + MLT in country filter; CPV `50114000` truck R&M added.
- Empty Excel sheets no longer emit fake “No results…” notice rows.

### Phase 2 — Extraction
- Multilingual `extract_fleet_size` with guards; `fleet_size_confidence`.
- R&M flag = RM terms or CPV 501xx (high recall on notices that already passed the Isuzu gate).

### Phase 3 — GPS / PMS linkage
- `gps_addressable_per_year_eur` = fleet × (**max_spend / uio**).
- `capture_at_current_rate_eur` = fleet × **actual** spend_per_unit.
- Null when fleet or mapping missing — never averaged / never 0.

### Phase 4 — Dashboards
- v4 opportunity HTML offline, light-only, source-health banner, contract value + GPS headline.
- **Outcome dropdown removed** from v4 UI (store file remains for future use).
- v2 still builds; fields additive only.

### Phase 5 — Outcomes
- `tender_outcomes.json` survives rebuilds; win rate suppressed until 20 closed.

### God-tier loop (same day)
- Isuzu selection gate in `isze_core_v3.py`; wired into scraper `normalize_batch` + dashboard rebuild.
- SETUP / OPERATOR_INDEX aligned with env keys (no “paste into .py”).
- `CURSOR_PROMPTS_v4_engine.md` status → **SHIPPED**.
- Dutch `\bvan\b` false positive removed from LCV regex.

### Phase 6 — Validation
- No capture rate > 100%
- Keys not committed
- Spot-check 15 opportunities: pickups / tippers / chassis / truck R&M (see relevance audit)

---

## Before → after (completeness + relevance)

| Metric | v3 baseline | v4 pre-gate | After Isuzu gate |
|---|---:|---:|---:|
| Raw notices | 778 | 773 | **193** |
| Opportunities | 680 | 679 | **172** |
| CPV `60000000` | — | 54 | **0** |
| GPS-sized opportunities | 0 | 11 | **6** |
| Addressable GPS / year (sized) | — | €5,915* | **€30,410** (max-wallet SPU) |

\*Earlier €5,915 used actual SPU in error; addressable now correctly uses max_spend/uio.

---

## Still broken / limited
- Belgium national feed; Germany DTVP; Nordics until keys registered
- Israel inventory lag; TED detail enrichment off
- Most opportunities unsized → GPS total is a **floor**
- UK-CF volume thin after gate (passenger/route noise removed)

## Deliberately out of scope
- Fit/Win/Econ weight retuning
- Inventing fleet sizes or revenue forecasts
- MIDI/IMG hard-coded branding

---

## How to open
Double-click: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\OPEN_isze_dashboard_v4_opportunity.cmd`
