# Agent notes — extended reference

**Not bootstrap.** Read `INDEX.md` + `AGENTS.md` first. Open this file only when the task needs scheduled-task paths, decision-model caveats, or PMS context.

**Agent sync:** 2026-06-13 (split from `INDEX.md` to cut Cursor token burn)

---

## Path conventions (scheduled skills + agents)

| Convention | Value |
|------------|-------|
| Workspace root | `$env:ISZE_ROOT` (default `C:\Users\jerom\Desktop\claude\ISZE` if unset) |
| Folder contract | `paths.yaml` at ISZE root |
| Local data spine | `01_data/derived/` |
| Dashboard JSON | `01_data/dashboards/` |
| HTML source | `02_dashboards/` |
| PRISM / pipeline | `03_analytics/Isuzu/prism/` |
| Scrapers / tools | `04_tools/` |
| Memory / briefs | `05_memory/` |
| UIO workbook | `06_uio/_CURRENT/` |
| Deploy mirror | `07_deploy/Master Dashboard/` — generated only |
| GPT upload pack | `08_gpt/` |

**Deploy-side compatibility paths** (GitHub Pages runtime — do not use as local edit targets): `../Data/...`, deploy-side `Data/dashboards/`, deploy-side `Projects/`. Label these explicitly when documenting fetch URLs or sync rewrites.

**Rule:** Do not introduce new absolute `C:\Users\jerom\...` paths in docs or skills. Use `$env:ISZE_ROOT` + numbered folders.

---

## Scheduled automations

Skills live under `C:\Users\jerom\Documents\Claude\Scheduled\`. Each ISZE skill sets or assumes `$env:ISZE_ROOT` and runs a **path preflight** before work.

| Skill | Status | Canonical inputs | Canonical outputs | Path preflight | Notes |
|-------|--------|------------------|-------------------|----------------|-------|
| `isze-weekly-tender-scrape` | Active | `04_tools/ISZE_Tender_Monitor_Install/tender_scraper_v3.py` | `01_data/dashboards/tender_data.json` | Script + output dir | Runs v3 scraper + publish; weekly |
| `isze-scraper-healthcheck-autofix` | Active | `04_tools/…` scraper scripts (read-only) | `04_tools/scraper_health_report.md` (+ optional diff) | Input scripts + `04_tools/` | **Propose-only** — never auto-applies patches |
| `isze-weekly-ks-scrape` | Active | `04_tools/autodoc_scraper/ks_scraper.py` | `04_tools/autodoc_scraper/ks_results.csv` | Script + output dir | Weekly price diff vs prior run |
| `autodoc-monthly-refresh` | Active | `04_tools/autodoc_scraper/autodoc_results.csv` | (reminder only) | Scraper folder | Monthly freshness reminder |
| `isze-dashboard-freshness-check` | Active | `02_dashboards/`, `01_data/dashboards/` | (report only) | Parent folders | Monday staleness table |
| `isze-uio-staleness-alert` | Active | `06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx` | (report only) | Canonical UIO + README | Monthly; flags copy drift |
| `isze-memory-review` | Active | `05_memory/projects/`, `05_memory/glossary.md` | `05_memory/briefs/weekly_W*.txt` | Input + output dirs | Weekly hygiene |
| `isze-weekly-intelligence-brief` | Active | WebSearch (no local inputs) | `05_memory/briefs/latest_weekly_brief.txt` + archive | `05_memory/briefs/` | **Never** write to `07_deploy/` |
| `isze-pricing-basket-monitor` | Active | `01_data/` price lists | (report only) | Memory + data root | Monthly IE40 check |
| `isze-aim-classification-refresh` | Active | `05_memory/projects/aftermarket-intelligence.md`, `01_data/`, `03_analytics/Isuzu/data/` | (report only) | Input paths | Monthly AIM completeness |
| `zondag-checkin-traject` | Active | `Prive/moi/HERSTEL_TRAJECT.md` | Same file (weeklog) | N/A | Private — not ISZE |
| `feedback` | Active | — | — | N/A | Meta feedback — not ISZE |

---

## Decision-model layer notes (2026-06-10)

- ITUK 2025–2030 UIO forecast cells in the v17 workbook are **uncached formulas** — Python readers (openpyxl) get None. `build_revenue_runway.py` reads computed values once via Excel COM (read-only) and caches to `03_analytics/Isuzu/prism/data/ituk_uio_projection_cache.csv`. **Delete that cache after any UIO workbook update** so it re-reads.
- Wallets are age-flat (GPS max targets). The genuine-€-by-age curve from IML plugs into `03_analytics/Isuzu/prism/data/decision_model_assumptions.yaml` when it lands.
- Elasticity output is LOW POWER by construction — direction only, never quote betas externally.

---

## PMS capture metrics

**Canonical:** `03_analytics/Isuzu/prism/docs/metric_dictionary.md` and `01_data/derived/pms_capture_by_db_year.csv`.

Do not use legacy single-PN / 1.5×UIO denominators in old HTML or `91_legacy/Isuzu/Divers/` docs without checking PRISM first.

Headline figures: `FACTS.md` + `01_data/derived/metrics_snapshot.json` (after green verify).

---

## Cursor vs Claude Desktop

| Tool | What ignores deploy mirror |
|------|----------------------------|
| **Cursor** | `.cursorignore` hides `07_deploy/Master Dashboard/context/` from index/search |
| **Claude Desktop** | Unaffected — reads canonical paths at `$env:ISZE_ROOT` (`05_memory/`, `INDEX.md`, etc.) |
| **GitHub context sync** | Unaffected — `sync_context_to_github.ps1` copies whitelist (`00_docs/context_sync_whitelist.txt`) to `07_deploy/Master Dashboard/context/` |

Never edit markdown in `07_deploy/Master Dashboard/context/`; it is regenerated on sync.
