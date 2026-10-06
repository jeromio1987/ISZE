# ISZE automation register

**Job implementations:** `C:\Users\jerom\Documents\Claude\Scheduled\<job-name>\SKILL.md`  
**This file:** Canonical in-repo index (migrated from `00_docs/agent/NOTES.md`)  
**Last audited:** 2026-10-06 (brief F3)
**Path contract:** `$env:ISZE_ROOT` + [`paths.yaml`](../paths.yaml) · preflight policy: audit-export `scheduled-path-fix-report.md`

### Model routing (2026-07-24)

| Tier | Use for | Jobs |
|------|---------|------|
| **CHEAP** | Routine hygiene / freshness / scrape wrappers | healthcheck, open-loops, memory-review, dashboard freshness, UIO staleness, pricing basket, AIM refresh, weekly intel, tender/ks scrape skills |
| **FRONTIER** | Judgment / coaching | `feedback`, `zondag-checkin-traject` |

Each `SKILL.md` states `**Model tier: …**` under the frontmatter. Prefer Haiku/Sonnet-class for CHEAP when the scheduler UI allows; Opus/Fable-class for FRONTIER.

---

## ISZE active skills

| Skill | Status | Runs in | Cadence | Output | Notes |
|---|---|---|---|---|---|
| `isze-scraper-healthcheck-autofix` | Active | claude.ai routine (since 23 Sep) | Sun 22:00 | `04_tools/scraper_health_report.md` | Allowlist auto-apply ([DECISIONS.md](../DECISIONS.md) § 2026-07-24). Still watches the 3 scrapers retired 24 Sep. |
| `isze-memory-review` | Active | claude.ai routine (since 23 Sep) | Mon 08:00 | `05_memory/briefs/memory_review_W*.txt`, phone push | Push carries the scorecard headline (brief E1). |
| `isze-dashboard-freshness-check` | Paused | desktop app | Mon | chat only | Jerome 5 Oct: "stop this schedule". |
| `isze-uio-staleness-alert` | Paused | desktop app | 1st of month | chat only | Jerome 3 Oct: "stop please". |
| `isze-pricing-basket-monitor` | Paused | desktop app | 1st of month | chat only | Jerome 3 Oct: "stop". |
| `isze-aim-classification-refresh` | Paused | desktop app | 1st of month | chat only | Jerome 3 Oct: "stop please". |
| `isze-weekly-intelligence-brief` | Paused | desktop app | - | `05_memory/briefs/weekly_W*.txt` | Not run since 17 Aug (last file W34). |
| `isze-weekly-open-loops` | Paused | desktop app | - | none | Never ran: no `open_loops_*.md` exists. |
| `isze-weekly-tender-scrape` | Paused | desktop app | - | - | Superseded by Windows task `ISZE Tender Monitor`; last run 10 Aug. |
| `isze-weekly-ks-scrape` | Superseded | - | - | - | Replaced by `refresh_and_check_drift.py` + Windows task `ISZE_PMS_IAM_Refresh`. |
| `autodoc-monthly-refresh` | Retired | - | - | - | Autodoc permanently blocked; last run 1 Sep. |
| `isze-delegator-watch` | Retired | - | - | - | Windows task disabled 18 Sep; its queue archived 5 Oct (brief A2). |
| `isze-mailbox-intake` | Stub | - | - | - | Not implemented. |
---

## P8 pipelines (roadmap §17 — four fields required)

| Pipeline | Status | Cadence | Tier | Owner | Inputs | Outputs | Monitor | Retirement condition |
|----------|--------|---------|------|-------|--------|---------|---------|----------------------|
| **action_ledger** | Active | After each derived refresh (or weekly Mon with open-loops) | CHEAP | Jerome | Nine §5 surfaces under `01_data/00_derived/` + `17_interactions/account_health_latest_flagged.csv`; human `action_ledger_decisions.csv` | `action_ledger.parquet`, `_history.parquet`, `_open.csv`, `_rejects.csv`, `.meta.json`, `ACTION_LEDGER_REVIEW_*.md`, `02_dashboards/ops/ISZE_Action_Ledger.html` | `verify_derived_pipeline.py` checks `action_ledger.*`; `verify_action_ledger.py` in ship gate; empty realised € past billing horizon is correct | Retire when a CRM/work-management system owns opportunity state end-to-end *and* every monetary row still carries source_file+column+as_of lineage into that system — until then the ledger stays |

**Path preflight:** abort if any of the nine source files is missing; never invent euros; never write `action_ledger_decisions.csv`.

**Builder:** `python 01_data/91_build/build_action_ledger.py --all --backfill`

---

## Non-ISZE / private / meta skills

| Skill | Status | Runs in | Cadence | Notes |
|---|---|---|---|---|
| `zondag-checkin-traject` | Active | desktop app | Sun | **Not ISZE**, personal check-in. |
| `feedback` | Paused | desktop app | weekly | Jerome 3 Oct: "stop this session"; each run stopped at its first check. |
---

## Disabled / duplicate job directories

| Folder | Reason | Action |
|--------|--------|--------|
| `isze-weekly-intel-brief` | Empty duplicate of `isze-weekly-intelligence-brief` | **Deleted 2026-07-24** |
| `isze-tender-dashboard-refresh` | Empty; superseded by `isze-weekly-tender-scrape` | **Deleted 2026-07-24** |

---

## Claude Code tab and claude.ai schedules (checked 2026-10-05)

| Job | Scheduler | State | Notes |
|---|---|---|---|
| isze-scraper-monthly-refresh | Claude Code tab | Disabled | Ran the same script as ISZE_PMS_IAM_Refresh; the 1 Sep and 1 Oct runs did nothing. |
| isze-facts-drift-check | Claude Code tab | Disabled since 2026-08-17 | |
| isze-pms-facts-reconcile, vdpj-liquidation-reminder, weekly-retro-review | Claude Code tab folders | Not scheduled | Folders kept. The scorecard (brief E1) replaces weekly-retro-review. |
| Morning brief | claude.ai routine | Disabled | Jerome 5 Oct: "stop this schdule". |
| Techno Tokio 23-29 okt checken | claude.ai routine | One-off 2026-10-09 | Personal. |
---

## Windows Task Scheduler — live state (checked 2026-10-06)

| Live task name | State | Cadence | Batch / script | Produces | Notes |
|---|---|---|---|---|---|
| `ISZE Tender Monitor` | Ready | Mon 07:30 | `run_tender_monitor.bat` | `01_data/14_dashboards/tender_data.json` | Last run 2026-10-05 07:30, result 0 |
| `ISZE_PMS_IAM_Refresh` | Ready | Mon 07:00 | `run_refresh_scheduled.bat` | KS and TMC prices, drift history, executive dashboards | Mekonomen, Auto365, Tranzparts retired 24 Sep. Last run 2026-10-05 07:00, result 0 |
| `ISZE_LiveStateAudit_Weekly` | Ready | Mon 08:00 | `run_live_state_audit.cmd` | `05_memory/briefs/automation_drift_*.md` | Last run 2026-10-05 08:00, result 0 |
| `ISZE_PriceLedger_Weekly` | Ready | Mon 09:00 | `04_tools/delegation/run_price_ledger_hidden.pyw` | price-observation ledger for the parts price dashboard | Windowless pythonw launcher so the scheduler gets the real exit code. Failed every Monday from 28 Sep to 5 Oct (exit 0xC000013A, console window closed); fixed by this launcher. First good run 2026-10-06 05:55, result 0 (manual re-run; output rebuilt 06:11) |
| `ISZE_CursorWeekDigest_Weekly` | Ready | Sun 20:00 | `run_cursor_week_digest.cmd` | Claude/Cursor scorecard `05_memory/briefs/scorecard_*.md` | Name kept; runs the scorecard since brief E1. Last run 2026-10-04 20:00, result 0 |
| `ISZE_DiscountScanner_Weekly` | Ready | Thu 07:00 | `run_discount_scraper.bat` | `04_tools/discount-scanner/deals_dashboard.html` | Personal, outside the audit. |
| `ISZE_DelegatorWatch_20min` | Disabled | - | `run_overnight_orchestrator.cmd` | nothing | Off since 18 Sep; queue archived 5 Oct. |
| `ISZE_EQ_Hit_Session_20260919` | Disabled | - | `run_eq_hit_session_20260919.ps1` | nothing | One-off of 19 Sep, exited 1. |
| `SMID_DataFeed_0700` | Disabled | - | `Prive\investing\fetch_smid_data.py` | nothing | Personal; parked folder; exited 1. |
| `SMID_DataFeed_1200` | Disabled | - | `Prive\investing\fetch_smid_data.py` | nothing | Personal; parked folder; exited 1. |

**Decision drift (added 2026-09-16).** The same task now also runs `04_tools/workspace/check_decision_drift.ps1`, appended to the brief after the audit above. It compares `00_docs/ISZE_ROADMAP.md` §2 "Waiting on Jerome" against `DECISIONS.md` entries dated after the roadmap's own "Last updated" line, and prints a line for any item that may already be decided but still reads as waiting. Read-only, always exits 0, no second scheduled task, and it cannot change the audit's findings or exit code. Rule it serves: [`00_docs/DECISION_DISCIPLINE.md`](DECISION_DISCIPLINE.md).

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

None. The two rows closed on 25 Aug and the freshness path map were removed on 2026-10-05; see git history.
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
- Decision drift (roadmap §2 vs `DECISIONS.md`): `04_tools/workspace/check_decision_drift.ps1` · rule: `00_docs/DECISION_DISCIPLINE.md`
