# ISZE automation register

**Job implementations:** `C:\Users\jerom\Documents\Claude\Scheduled\<job-name>\SKILL.md`  
**This file:** Canonical in-repo index (migrated from `00_docs/agent/NOTES.md`)  
**Last audited:** 2026-08-25 (overnight process audit; prior full audit 2026-07-26)
**Path contract:** `$env:ISZE_ROOT` + [`paths.yaml`](../paths.yaml) · preflight policy: audit-export `scheduled-path-fix-report.md`

### Model routing (2026-07-24)

| Tier | Use for | Jobs |
|------|---------|------|
| **CHEAP** | Routine hygiene / freshness / scrape wrappers | healthcheck, open-loops, memory-review, dashboard freshness, UIO staleness, pricing basket, AIM refresh, weekly intel, tender/ks scrape skills |
| **FRONTIER** | Judgment / coaching | `feedback`, `zondag-checkin-traject` |

Each `SKILL.md` states `**Model tier: …**` under the frontmatter. Prefer Haiku/Sonnet-class for CHEAP when the scheduler UI allows; Opus/Fable-class for FRONTIER.

---

## ISZE active skills

| Skill | Status | Cadence | Tier | Inputs | Outputs | Path Preflight | Owner Review | Notes |
|-------|--------|---------|------|--------|---------|----------------|--------------|-------|
| `isze-weekly-tender-scrape` | Active | Weekly | CHEAP | `04_tools/ISZE_Tender_Monitor_Install/tender_scraper_v3.py` | `01_data/dashboards/tender_data.json` | Script + `01_data/dashboards/` | Jerome | v3 scraper + publish |
| `isze-scraper-healthcheck-autofix` | Active | Sun 22:00 | CHEAP | Tender + `autodoc_scraper/` scripts | `scraper_health_report.md`, optional diff, `applied_patches_log.md` | Tender + KS scripts + `04_tools/` | Jerome (non-allowlist) | **Allowlist auto-apply** KS/Tranzparts/TMC/Mekonomen/Auto365 URL/selector fixes; Tender propose-only ([DECISIONS.md](../DECISIONS.md) § 2026-07-24) |
| `isze-weekly-open-loops` | Active | Monday | CHEAP | health report, memory_review_W*, briefs | `05_memory/briefs/open_loops_YYYY-MM-DD.md` | `04_tools`, `05_memory/briefs`, `02_dashboards` | Jerome | Merged digest — read existing artifacts only |
| `isze-weekly-ks-scrape` | Superseded | — | CHEAP | — | — | — | — | Replaced by `refresh_and_check_drift.py` + live Task `ISZE_PMS_IAM_Refresh` |
| `autodoc-monthly-refresh` | Retired | — | CHEAP | — | — | — | — | Autodoc permanently blocked |
| `isze-dashboard-freshness-check` | Active | Monday | CHEAP | `02_dashboards/`, `01_data/dashboards/` | Report only | Both input folders | Jerome | |
| `isze-uio-staleness-alert` | Active | Monthly | CHEAP | `06_uio/_CURRENT/…` | Report only | Canonical UIO + README | Jerome | |
| `isze-memory-review` | Active | Weekly | CHEAP | `05_memory/projects/*.md`, glossary, verify reports | `memory_review_W*.txt`, optional `memory_applied_log.md` | Input + `05_memory/briefs/` | Jerome | May apply high-confidence factual syncs |
| `isze-weekly-intelligence-brief` | Active | Weekly | CHEAP | WebSearch | `weekly_W*.txt` | `05_memory/briefs/` | Jerome | Never write `07_deploy/` |
| `isze-pricing-basket-monitor` | Active | 1st of month | CHEAP | `01_data/` price lists | Report only | Memory + `01_data/` | Jerome | |
| `isze-aim-classification-refresh` | Active | Monthly | CHEAP | AIM memory + data | Report only | All input paths | Jerome | |
| `isze-mailbox-intake` | **Stub** | 1st of month | CHEAP | Outlook COM (own Inbox+Sent); subjects UTIPartSales / Sales to Dealer / Business Analysis Masterdata Z2SDAB42 | Attachments → `01_data/90_INBOX/` + SCAN_LOG; never shared Sales/Parts until G0b | `90_INBOX/` + registry updates | Jerome | **Not implemented yet** — register slot from Full Project Audit 2026-08-25. Script TBD under `04_tools/interactions/` or `91_build/`. Human Save still required for Online Archive / sap4*. |

---

## P8 pipelines (roadmap §17 — four fields required)

| Pipeline | Status | Cadence | Tier | Owner | Inputs | Outputs | Monitor | Retirement condition |
|----------|--------|---------|------|-------|--------|---------|---------|----------------------|
| **action_ledger** | Active | After each derived refresh (or weekly Mon with open-loops) | CHEAP | Jerome | Nine §5 surfaces under `01_data/00_derived/` + `17_interactions/account_health_latest_flagged.csv`; human `action_ledger_decisions.csv` | `action_ledger.parquet`, `_history.parquet`, `_open.csv`, `_rejects.csv`, `.meta.json`, `ACTION_LEDGER_REVIEW_*.md`, `02_dashboards/ops/ISZE_Action_Ledger.html` | `verify_derived_pipeline.py` checks `action_ledger.*`; `verify_action_ledger.py` in ship gate; empty realised € past billing horizon is correct | Retire when a CRM/work-management system owns opportunity state end-to-end *and* every monetary row still carries source_file+column+as_of lineage into that system — until then the ledger stays |

**Path preflight:** abort if any of the nine source files is missing; never invent euros; never write `action_ledger_decisions.csv`.

**Builder:** `python 01_data/91_build/build_action_ledger.py --all --backfill`

---

## Non-ISZE / private / meta skills (2)

| Skill | Status | Cadence | Tier | Notes |
|-------|--------|---------|------|-------|
| `zondag-checkin-traject` | Active | Weekly (Sun) | FRONTIER | **Not ISZE** — personal recovery check-in |
| `feedback` | Active | Ad hoc | FRONTIER | **Meta** — Claude/ISZE usage feedback |

---

## Disabled / duplicate job directories

| Folder | Reason | Action |
|--------|--------|--------|
| `isze-weekly-intel-brief` | Empty duplicate of `isze-weekly-intelligence-brief` | **Deleted 2026-07-24** |
| `isze-tender-dashboard-refresh` | Empty; superseded by `isze-weekly-tender-scrape` | **Deleted 2026-07-24** |

---

## Windows Task Scheduler — live state (verified 2026-07-16)

| Live task name | Registered? | Cadence | Batch / script | Notes |
|----------------|-------------|---------|----------------|-------|
| `ISZE Tender Monitor` | ✅ registered + last result **0** (2026-07-20); next 2026-07-27 07:30 | Weekly Mon 07:30 | `run_tender_monitor.bat` | Publish step fixed (see below). |
| `ISZE_PMS_IAM_Refresh` | ✅ live — last scheduled 2026-07-20 result **`0xC000013A` (interrupted)**; manual refresh started 2026-07-26 ~21:28 | Weekly Mon 07:00 | `04_tools/autodoc_scraper/run_refresh_scheduled.bat` | This **is** the competitive-pricing refresh (KS/Tranzparts/TMC/Mekonomen/Auto365). The spare `ISZE_ScraperRefresh_WeeklyTask.xml` is **redundant — do NOT import it** (would double-run). |
| `ISZE_DiscountScanner_Weekly` | ✅ registered (verified 2026-08-25 overnight; personal promos, not core ISZE) | Thu 07:00 | `04_tools/run_discount_scraper.bat` | Live task name may be `ISZE_DiscountScanner_Weekly`. Not part of ISZE commercial quote gate. |
| `ISZE_CursorWeekDigest_Weekly` | ✅ registered 2026-07-26 | Sun 20:00 | `04_tools/workspace/run_cursor_week_digest.cmd` | Cross-tool bridge: summarises the week's local Cursor sessions into `05_memory/briefs/cursor_week_*.md` so the Claude Desktop weekly review sees work done in Cursor. Output is gitignored (spans private projects). |
| `ISZE_LiveStateAudit_Weekly` | ✅ registered 2026-07-26 | Mon 08:00 | `04_tools/workspace/run_live_state_audit.cmd` | Compares this register against Task Scheduler and the FACTS/pipeline reports; writes a numbered "waiting on Jerome" list to `05_memory/briefs/automation_drift_*.md`. Read-only — it reports drift, it never closes it. |

**Register a task from XML (no elevation needed for these LeastPrivilege tasks):**
`schtasks /create /tn "ISZE Discount Scanner" /xml "<full path to xml>" /f`

**Tender publish fix (2026-07-16):** `publish_live_tender_json.ps1` dot-sourced a helper `..\workspace\isze_root.ps1` (`Get-IszePath`/`Get-DataSubfolderPath`) that **does not exist** — so step 2/3 always exited 1 and `tender_data.json` went stale from 2026-05-30. Rewrote the script to resolve `01_data/dashboards/tender_data.json` directly. Full task re-run confirmed **Last Result 0**.

**Duplicate tasks removed (2026-07-26):** `import_isze_scheduled_tasks.ps1` had imported `ISZE_TenderMonitor_Weekly` and `ISZE_ScraperRefresh_Weekly`, which run the same batch files as `ISZE Tender Monitor` and `ISZE_PMS_IAM_Refresh` — the exact double-run this table warned against. Neither duplicate had ever run; both deleted. The originals are canonical. The import script now skips both entries unless `-Force`.

> **Editing an XML on disk does not update a live task** — re-register (delete + `schtasks /create /xml`) after editing.

---

All ISZE jobs include a **Path preflight (run first — abort if it fails)** block:

1. Verify required **input** paths exist.
2. Verify **output parent** folder exists (where applicable).
3. On any miss: print `"<skill> ABORTED — missing <input|output>: <path>"` and stop — **without** creating folders, running scrapers, or auto-fixing code.

Scrapers (`*-tender-scrape`, `*-ks-scrape`, `scraper-healthcheck-autofix`) abort before any network I/O if preflight fails.

---

## Open items (Jerome)

| Skill | Issue | Status 2026-08-25 |
|-------|-------|-------------------|
| `isze-weekly-intelligence-brief` | Confirm target for `latest_weekly_brief.txt` | **CLOSED** — file lives at `05_memory/briefs/latest_weekly_brief.txt` |
| `isze-dashboard-freshness-check` | Post-reorg paths for three XLSX + UIO HTML | **RESOLVED (paths found)** — update Scheduled `SKILL.md` then drop from open-items: |

**Freshness-check path map (overnight):**

| Watched file | Live path | Action |
|--------------|-----------|--------|
| `ISZE_Parts_Sales_Classification_Mar2026_v2.xlsx` | `01_data/01_Pricing/` | Point skill here (also legacy copy under `91_legacy/`) |
| `ISZE_FY2027_ActionPlan_v1.xlsx` | `90_archive/root_files/` only | Treat as **archived** — do not fail freshness; optional promote later |
| `ITUK_PMS_Analysis_Apr2026_v2.xlsx` | `03_analytics/Isuzu/pms-pilot/_archive/` only | **Archived** — Model B / FACTS is SSOT; skip as live |
| `ISUZU_UIO_Dashboard_2026_v17.html` | `02_dashboards/_archive/` | Superseded; live UIO = `06_uio/_CURRENT/` xlsx (not HTML) |

Junctions for `01_data/dashboards` **restored overnight** — freshness skill parent-folder preflight should pass again.

---

## Adding a new job

1. Add a row to this register **first**.
2. Create `SKILL.md` under `Documents\Claude\Scheduled\` using numbered paths from `paths.yaml`.
3. Add path preflight block.
4. Log in [CHANGELOG.md](../CHANGELOG.md).
5. If policy-level: add entry to [DECISIONS.md](../DECISIONS.md).

---

## PRISM analytics pages (not scheduled jobs)

Added 2026-08-20 as part of the BI-tools consolidation. Read-only Streamlit pages over existing derived files — no schedule, no egress, no new pipeline. Entry point: `03_analytics/Isuzu/prism/app.py` NAV sections.

| Page | Data source | Notes |
|------|-------------|-------|
| `pages/20_Warranty.py` | `00_derived/distributor_warranty_expense_fiscal.csv` | Warranty erodes net GPS; MIDI toggled off by default |
| `pages/21_Realization.py` | `00_derived/pr00_realization_*_cy.csv`, `zpr1_vs_pr00_by_payer_year.csv` | Net-only; `provisional_qa_pending` banner shown |
| `pages/22_Parc_Cohort.py` | `07_UIO/vin/VIN_register.csv` | JP cohort, ex ITUK/UTI — labelled NOT UIO v19 |
| `pages/23_Dealer_Sellout.py` | `00_derived/sellout_aim_network_mix_2025.csv`, `sellout_aim_by_subgroup_2025.csv` | IUK ≠ ITUK ≠ IMIE |
| `pages/24_VPACC.py` | `00_derived/vpacc_fy2027_action_plan_july.parquet`, `vpacc_fy2027_monthly_db_block.parquet` | Action plan = July update; monthly block = legacy sheet, directional only |

Static HTML twins: `02_dashboards/bi/{Warranty_Intelligence,Price_Realization,Parc_Cohorts,Dealer_Sellout}.html` — self-contained, rebuilt by `02_dashboards/bi/_build_bi_twins.py`.

## Cross-references

- Extended agent notes: [00_docs/agent/NOTES.md](agent/NOTES.md)
- Scheduled path fix detail: audit-export `scheduled-path-fix-report.md`
- Scheduled path check: `04_tools/workspace/verify_scheduled_paths.ps1`
- Monthly refresh (manual): [RUNBOOK_MONTHLY_REFRESH.md](RUNBOOK_MONTHLY_REFRESH.md)
- Monthly refresh (orchestrated, fail-closed): `04_tools/workspace/isze_monthly_refresh.ps1`
- Drift audit of this file vs live state: `04_tools/workspace/isze_live_state_audit.ps1`
