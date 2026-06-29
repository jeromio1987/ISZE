# ISZE automation register

**Job implementations:** `C:\Users\jerom\Documents\Claude\Scheduled\<job-name>\SKILL.md`  
**This file:** Canonical in-repo index (migrated from `00_docs/agent/NOTES.md`)  
**Last audited:** 2026-06-13  
**Path contract:** `$env:ISZE_ROOT` + [`paths.yaml`](../paths.yaml) · preflight policy: audit-export `scheduled-path-fix-report.md`

---

## ISZE active skills (10)

| Skill | Status | Cadence | Inputs | Outputs | Path Preflight | Owner Review | Notes |
|-------|--------|---------|--------|---------|----------------|--------------|-------|
| `isze-weekly-tender-scrape` | Active | Weekly | `04_tools/ISZE_Tender_Monitor_Install/tender_scraper_v3.py` | `01_data/dashboards/tender_data.json` | Script + `01_data/dashboards/` | Jerome | v3 scraper + publish; path-fixed 2026-06-13 |
| `isze-scraper-healthcheck-autofix` | Active | Sun 22:00 | `04_tools/ISZE_Tender_Monitor_Install/`, `04_tools/autodoc_scraper/` (read-only scripts) | `04_tools/scraper_health_report.md` (+ optional diff) | All three scraper scripts + `04_tools/` | Jerome (diff review) | **Propose-only** — never auto-applies patches ([DECISIONS.md](../DECISIONS.md)) |
| `isze-weekly-ks-scrape` | Active | Weekly | `04_tools/autodoc_scraper/ks_scraper.py` | `04_tools/autodoc_scraper/ks_results.csv` | Script + output dir | Jerome | Price diff vs prior run |
| `autodoc-monthly-refresh` | Active | Monthly | `04_tools/autodoc_scraper/` (`autodoc_results.csv`, `.bat`) | Reminder only | Scraper folder | Jerome | CSV may be absent — handled in-skill |
| `isze-dashboard-freshness-check` | Active | Monday | `02_dashboards/`, `01_data/dashboards/` | Report only | Both input folders | Jerome | Source HTML (`02_dashboards/`), not deploy mirror; 4 xlsx paths unresolved — see Notes § Open |
| `isze-uio-staleness-alert` | Active | Monthly | `06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx`, `06_uio/_CURRENT/README.md` | Report only | Canonical UIO + README | Jerome | Flags copy drift vs PRISM `data/UIO.xlsx` |
| `isze-memory-review` | Active | Weekly | `05_memory/projects/*.md`, `05_memory/glossary.md`, `03_analytics/Isuzu/prism/docs/metric_dictionary.md`, `01_data/derived/_verification_report.md` | `05_memory/briefs/weekly_W*.txt` | Input + `05_memory/briefs/` | Jerome | Hygiene vs green verify |
| `isze-weekly-intelligence-brief` | Active | Weekly | WebSearch (no local inputs) | `05_memory/briefs/weekly_W*.txt` + `latest_weekly_brief.txt` (pending) | `05_memory/briefs/` | Jerome | **Never** write to `07_deploy/`; output 1 (`latest_weekly_brief.txt`) disabled pending Jerome decision |
| `isze-pricing-basket-monitor` | Active | 1st of month | `01_data/` (price lists) | Report only | Memory + `01_data/` | Jerome | IE40/PR00 drift check |
| `isze-aim-classification-refresh` | Active | Monthly | `05_memory/projects/aftermarket-intelligence.md`, `01_data/`, `03_analytics/Isuzu/data/` | Report only | All input paths | Jerome | AIM completeness |

---

## Non-ISZE / private / meta skills (2)

| Skill | Status | Cadence | Inputs | Outputs | Path Preflight | Owner Review | Notes |
|-------|--------|---------|--------|---------|----------------|--------------|-------|
| `zondag-checkin-traject` | Active | Weekly (Sun) | `Prive/moi/HERSTEL_TRAJECT.md` | Same file (weeklog) | N/A (private path) | Jerome | **Not ISZE** — personal recovery check-in |
| `feedback` | Active | Ad hoc | — | — | N/A | Jerome | **Meta** — Claude product feedback; no ISZE paths |

---

## Disabled / duplicate job directories

| Folder | Reason | Action |
|--------|--------|--------|
| `isze-weekly-intel-brief` | Empty dir; duplicate name of `isze-weekly-intelligence-brief` | Delete when confirmed empty (Jerome approval) |
| `isze-tender-dashboard-refresh` | Empty dir; superseded by `isze-weekly-tender-scrape` | Delete when confirmed empty (Jerome approval) |

---

## Path preflight policy

All ISZE jobs include a **Path preflight (run first — abort if it fails)** block:

1. Verify required **input** paths exist.
2. Verify **output parent** folder exists (where applicable).
3. On any miss: print `"<skill> ABORTED — missing <input|output>: <path>"` and stop — **without** creating folders, running scrapers, or auto-fixing code.

Scrapers (`*-tender-scrape`, `*-ks-scrape`, `scraper-healthcheck-autofix`) abort before any network I/O if preflight fails.

---

## Open items (Jerome)

| Skill | Issue |
|-------|-------|
| `isze-weekly-intelligence-brief` | Confirm target for `latest_weekly_brief.txt` — recommended: `05_memory/briefs/latest_weekly_brief.txt` |
| `isze-dashboard-freshness-check` | Post-reorg paths for `ISZE_Parts_Sales_Classification_Mar2026_v2.xlsx`, `ISZE_FY2027_ActionPlan_v1.xlsx`, `ITUK_PMS_Analysis_Apr2026_v2.xlsx`; live UIO HTML replacement for archived v17 |

---

## Adding a new job

1. Add a row to this register **first**.
2. Create `SKILL.md` under `Documents\Claude\Scheduled\` using numbered paths from `paths.yaml`.
3. Add path preflight block.
4. Log in [CHANGELOG.md](../CHANGELOG.md).
5. If policy-level: add entry to [DECISIONS.md](../DECISIONS.md).

---

## Cross-references

- Extended agent notes: [00_docs/agent/NOTES.md](agent/NOTES.md)
- Scheduled path fix detail: audit-export `scheduled-path-fix-report.md`
- Scheduled path check: `04_tools/workspace/verify_scheduled_paths.ps1`
- Monthly refresh (manual): [RUNBOOK_MONTHLY_REFRESH.md](RUNBOOK_MONTHLY_REFRESH.md)
