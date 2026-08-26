# Source health fix — before → after

Date: 2026-08-25  
Install: `ISZE_Tender_Monitor_Install`  
Product-fit / GPS max-wallet maths were **not** reverted (GPS sum still ~€1,488; segments + “No fleet count” KPI intact).  
Coverage context: [`_MARKET_COVERAGE_DARK_MAP.md`](_MARKET_COVERAGE_DARK_MAP.md) (verdict **~35–55%** of Isuzu-relevant notices visible; top gaps DE national, NO/FI keys, below-threshold FR/PL/IT/ES). Chip: [`_coverage_chip_snippet.html`](_coverage_chip_snippet.html) → integrated in v4 KPI strip.

## Banner model

| Status | Banner |
|--------|--------|
| `BROKEN` | Red alarm |
| `AWAITING_KEY` | Warn (not broken endpoint) |
| `SUSPECT` | Warn secondary note |
| `RETIRED` / `WONTFIX` / `SKIPPED` | Muted note — never red BROKEN |
| `OK` | Counted as healthy |

---

## Per source

### Germany DTVP/NRW
- **Before:** `BROKEN` — HTTP 404 / no public feed (scary silent failure)
- **After:** `RETIRED` — TED-only honesty for that portal; not an active fetcher. Paid DTVP Professional Edition would be required to revive it.
- Aligns with dark map gap #1 (DE national below-threshold still partially dark; service.bund is a free supplement, not full DTVP replacement).

### Germany service.bund (new)
- **Before:** absent
- **After:** `OK` — 12 keyword matches from  
  `https://www.service.bund.de/SiteGlobals/Functions/RSSFeed/RSSGenerator_Ausschreibungen.xml`
- **Fix:** RSS title parser no longer uses `el or …` (ElementTree text-only nodes are falsy and wiped every title).
- **Note:** oeffentlichevergabe eForms ZIP also works but was not wired this pass (heavier ZIP/XML path).

### Belgium RSS
- **Before:** `BROKEN` — HTML SPA / endpoint retired
- **After:** `RETIRED` — ignored; live SEA is primary (not on alarming BROKEN list)

### Belgium publicprocurement.be
- **Before:** `OK` (14) — already live
- **After:** `OK` (14) — unchanged; health honesty restored so RSS no longer alarms beside it

### Israel RSS
- **Before:** `BROKEN` — HTML SPA, 0 items
- **After:** `RETIRED` — ignored; live mr.gov.il is primary

### Israel mr.gov.il
- **Before:** `OK` (18)
- **After:** `OK` (18) — Hebrew AC keep-signals preserved

### Israel data.gov.il
- **Before:** `SUSPECT` — frozen inventory (competing visually with live OK)
- **After:** `SUSPECT` secondary only — banner labels “SUSPECT (secondary)”; note says not competing with live OK

### Norway Doffin
- **Before:** `BROKEN` — missing `ISZE_DOFFIN_API_KEY`
- **After:** `AWAITING_KEY` — points at `nordics_api_keys.env` + `NORDICS_API_KEYS.md` (not a broken endpoint)
- **Env:** `nordics_api_keys.env` present; keys **DONE** (2026-08-25). Do not re-ask Jerome. Dark map note below is historical for pre-key coverage bands.


### Finland HILMA
- **Before:** `BROKEN` — missing `ISZE_HILMA_API_KEY`
- **After:** `AWAITING_KEY` — same pattern as Doffin

---

## Rebuild evidence

- Focused scrape: `python tender_scraper_v3.py --only de,bel,isr,nordics` (+ `--only de` after parser fix)
- Dashboard: `python build_dashboard_v4.py --json-input isze_dashboard_v4_data.json`
- Preserved after rebuild: product segments (`lcv_van=41, pickup=40, truck=70, …`), GPS sum **€1,488.22**, “No fleet count in notice” KPI, unsized banner
- Added: **Coverage vs dark ~35–55%** KPI chip (navy/terracotta hover tooltip)

## Operator next step (Nordics)

1. Confirm keys in `nordics_api_keys.env` (or wait for parallel capture agent)
2. `python verify_nordics_keys.py`
3. Re-run scrape with `--only nordics` (or full weekly bat)
4. Refresh dark-map Nordics band after first keyed scrape
