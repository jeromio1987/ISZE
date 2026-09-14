# ISZE changelog

**Scope:** Workspace structure, documentation, deploy layout — not PRISM code detail (see `03_analytics/Isuzu/prism/CHANGELOG.md`) or GPT pack detail (see `08_gpt/CHANGELOG.md`).

**Format:** [Keep a Changelog](https://keepachangelog.com/) style — newest first. Append only; do not rewrite past entries.

---

## [Unreleased]

### Added (2026-09-14) — Decision pack (ticks not applied)
- [`00_docs/DECISION_PACK_20260914.md`](00_docs/DECISION_PACK_20260914.md) — one sitting for B5/P4, list-to-pocket Mode A, G1, Book B, LLM, sell-out files. Recommended defaults written; **not applied**.
- Hub §2 and `DECISIONS.md` point at the pack. Gated productize waits on ticks.

### Changed (2026-08-26) — Roadmap reorganised: one queue, one closed list
- **`00_docs/ISZE_ROADMAP.md` rewritten.** The old "Build now" table mixed ~15 shipped/closed items with ~8 open ones and carried multi-paragraph rationale inside table cells. Now six sections: **1 Open queue** (14 items, each with the single thing that unblocks it), **2 Waiting on Jerome** (13 decisions, sourced from the Aftermarket BI Tier B list + AI-sales gates), **3 Live now**, **4 Shipped** (dated one-liners), **5 Closed — do not reopen**, **6 Domain roadmaps**. Rationale stays in `DECISIONS.md`; the hub is a queue, not an archive.
- **Caught up to 2026-08-25.** The hub had stopped at 2026-08-18 and did not mention PRISM IA phases 3–8 (2026-08-20), the Aftermarket BI Tier A batch (2026-08-19, 14/15 built), P5 forecast, the P8 Action Ledger, or the overnight audit (verify 116/0/0, `sales_fact` to 2026-06-30).
- **Stale surface references fixed:** `pages/16_AIM_GPS_Matrix.py` is archived — the quadrant is a tab in `network_intelligence.py`; `pages/_archive/` is retired and must not be linked as live.
- **`roadmaps/scrapers.md` rewritten** (was 2026-07-26 and contradicted an accepted decision): Nordics API keys listed as open issue #1 while `DECISIONS.md` 2026-08-25 closed them permanently. National portal coverage (8/29 countries live) is now the stated P0, per `_OPEN_BACKLOG_ARRANGED.md`.
- **`roadmaps/gps.md`:** ITUK UIO landmine documented — PRISM capture lane **23,068**, IML lane **22,389**, never blended (the file previously showed only 22,389).
- **`roadmaps/html.md` rebuilt** from the actual `02_dashboards/` tree (was missing the Command Center, replenishment, Action Ledger, pricing packs, BI twins, IDS).
- **`roadmaps/aim_prism_reinvention.md` + `ai_sales_intelligence.md`:** status blocks reconciled with what actually shipped; AI-sales blockers re-scored (B5 moved from build to sign-off; EPC validation and P4 thresholds opened).
- **Broken links fixed:** 4 domain roadmaps pointed at `../../ISZE_ROADMAP.md` (repo root, no such file); all 4 redirect stubs pointed at a non-existent `docs/` folder; `REFERENCE.md` used `docs/roadmaps/*` and `Tools/SCRAPERS_ROADMAP.md`; the P4 spec link in `ai_sales_intelligence.md` was missing `../`.
- **Navigation:** new `roadmap` task key in `ROUTING.yaml`; `MAP_REGISTRY.yaml` gains `roadmap_specs` (P4/P5/P8/tender backlog) and orders roadmaps active-first; `MAPS.md` states the hub-wins rule; `INDEX.md` + `REFERENCE.md` describe the roadmap as the queue.
- **Legacy `01_data/derived/` alias** replaced with `01_data/00_derived/` in `ROUTING.yaml`, `MAPS.md`, `INDEX.md` (the junction stays load-bearing on Jerome's machine; only the numbered path exists in a fresh clone). Same for `_INBOX` → `90_INBOX` and `dashboards` → `14_dashboards` in `ROUTING.yaml`.
- **No numbers were changed.** Every figure in the roadmap traces to `DECISIONS.md`, `CHANGELOG.md`, the build menu, or a derived artefact; no pipeline, KPI, or dashboard was touched.

### Fixed (2026-08-25) — Overnight process audit (workspace OS)
- Prism verify **green** 116/0/0; junctions restored; `sales_fact` through **2026-06-30**; SaTy min 92% with Q1 hole documented.
- Action Ledger `BILLING_HORIZON` now reads `max(sales_fact.billing_date)` (was hard-coded 2026-03-31).
- Nordics keys **CLOSED** for Jerome asks — SteerCo / exec one-pager / OPERATOR_INDEX purged of paste-key spam; SSOT `_NORDICS_BLOCKED.md`.
- Durable pack: `docs/OVERNIGHT_PROCESS_AUDIT_2026-08-25.md` + morning brief + command card.

### Added (2026-08-11) — Pricing FULL analysis pack (Mode A) + audit + self-Send
- Mega-pack builder `01_data/91_build/build_pricing_full_analysis_pack.py` → `02_dashboards/pricing/ISZE_Pricing_Full_Analysis_Pack.html` (PR00 realization, ZPR1 UTI≠UMI, AIM CY/FY, PMS **total** capture, GPS SPU, AIM×GPS, mix extra lens, MOS not-elasticity, NO_LIST, VPACC hooks, integrity).
- Meta/CSVs under `01_data/00_derived/pricing_full_analysis_pack.meta.json` + `pricing_pack_*`.
- Independent audit `01_data/91_build/audit_pricing_full_pack.py` → `_pricing_full_pack_audit.md` (**PASS_WITH_CAVEATS**; integrity **48/100** weak).
- Self-Send only to `jerome.van.der.pluym@isuzu-e.com` at 2026-08-11T06:25:53Z (no colleagues).
- Thin findings HTML now points to the full pack.

### Added (2026-08-11) — Pricing history findings dashboard (provisional)
- Builder `01_data/91_build/build_pricing_history_findings.py` → derived CSVs + `pricing_history_findings.meta.json`.
- Mode A HTML: `02_dashboards/pricing/ISZE_Pricing_History_Findings_Dashboard.html` (year-matched PR00 realization 2023–2026 YTD, ZPR1 UTI/UMI/2372, KPI MOS stock days, NO_LIST, VPACC status, integrity score).
- Status: **internal QA / provisional** — list-to-pocket not externally quotable while integrity is weak.

### Added (2026-08-11) — PR00+ZPR1 history; IDS MIDI v1.4; AIM CY/FY windows
- Landed ZPR1 2024/2025 + PR00 tabs 2024/2025 under `01_data/01_Pricing/history/`.
- **Also 2023:** Downloads `2023.xlsx` (mixed PR00+ZPR1) → `_raw/2023.xlsx` + split `history/ZPR1_2023-01-03.xlsx` / `IE40_PR00_2023-12-31.xlsx`; parquet `pricing_pr00_ie40_2023.parquet` / `pricing_zpr1_2023.parquet`. Not engine-wired; no leakage quotes until year-matched joins validated.
- **IDS v1.4:** Baumann FR/ES red-marked out of averages (20/5); IT/CH all dealers in averages (incl. zero shells — corrected after verify); MIDI packs in `09_meetings/IDS_2026_Country_Packs_v1.4/`; Outlook draft to Tomoe (not Sent).
- **AIM billing:** `aim_billing_windows.json` / `aim_billing_by_db_window.csv` (CY + FY Apr–Mar).
- Elasticity deferred to DB→DLR; brake 0.4/0.8 pending ITUK; gross/SPA closed (net-only).

### Locked (2026-07-31 / logged 2026-08-10) — Tomoe Baumann MIDI average rule — NEVER FORGET
- **On behalf of Tomoe Baumann:** red-marked FR+ES dealers in her ranking attachments → **exclude from averages only**; **IT + CH keep all dealers in** (including zero-score shells). Exact mail wording + full dealer list: `04_tools/ids_dealer_ranking/CHANGELOG.md` + `IDS_2026_LOGIC_CHECK.md` § MIDI Baumann rule. Attachments/body: `01_data/90_INBOX/tomoe_ids_mail_pull/20260731_0858_*`.
- **v1.4 applied 2026-08-11** (rebuild+ship OK): averages-only; list/map keep reds.

### Changed (2026-07-28) — IDS dealer map: MIDI FR/IT/ES/CH + UK LCV geo
- **`ids_dealer_geo.py`** — loads `MIDI_FR.xlsx` NETWORK (Town + lat/lon) for exact DLRName match; Switzerland uses Town city centres when NETWORK lat/lon blank; UK LCV residual dealers pinned from Isuzu Truck UK store pages. Geo sanity city floors for France/Italy/Spain/Switzerland.
- **Map fitBounds** — initial zoom prefers dense pin core so France DOM-TOM outliers do not force a world view.
- **Rebuild** `IDS_2026_dealer_compare.html` v1.2 → `02_dashboards/ids/` + `01_data/90_INBOX/IDS_2026/reports/dashboard/` (changelog, no dark Weak overlay, hover = score vs country national avg, Mode A English).

### Changed (2026-07-24) — Loops package: allowlist self-patch + open-loops digest
- **Scraper healthcheck** — allowlist auto-apply for KS/Tranzparts/TMC/Mekonomen/Auto365 URL/selector fixes; Tender remains propose-only (`DECISIONS.md` § 2026-07-24). Verifier block + `04_tools/applied_patches_log.md`.
- **Memory review** — may apply high-confidence factual syncs; logs `05_memory/briefs/memory_applied_log.md`; verifier table in weekly brief.
- **New skill** `isze-weekly-open-loops` — Monday merged digest → `05_memory/briefs/open_loops_YYYY-MM-DD.md`.
- **Model tiers** on all `Documents/Claude/Scheduled/*/SKILL.md` (CHEAP vs FRONTIER); register updated.
- **Deleted** empty duplicate dirs `isze-weekly-intel-brief`, `isze-tender-dashboard-refresh`.
- **Teach-skill drafts** under `00_docs/teach-skills/`; bookmark analyzer `Projects/twitter-mcp/analyze_bookmarks.py`; myPENS workflow `Projects/mypens/.claude/workflows/api-auth-audit.js`.

### Changed (2026-07-17) — ITUK/UIO landmine closed + Jarvis stack.json
- **ITUK UIO keep 23,068 (PRISM capture lane)** — deliberate 2026-07-15 decision confirmed: `verification_fixtures.yaml` `ituk_pilot.uio_units: 23068` matches `facts_anchor.yaml`. IML §1 / `iml_v7_ituk_cy2025.yaml` may stay **22,389** separately. No force-revert.
- **`DATA_MANIFEST.md` §1/§3/§7** — stale "scripts read v18 / decision pending" wording removed; `_CURRENT` = v19; root `v18` not load-bearing (archived to `92_archive/` when moved).
- **Stretch WIP** — `ISZE_IUK_UMI_Sales_Share_Stretch_TESTCASE_v2.xlsx` unlocked → archived; newest stays in `02_GPS/` (`…_v3`).
- **Jarvis V2.1** — Stack tracker projects moved out of `1_Stack.py` into `04_tools/isze-tools/data/stack.json` (behavior unchanged). Roadmap `00_docs/roadmaps/tools.md` marked done.
- **Verify green** — rebuilt P1 (bucketed ITUK 23,068) + updated `aim_gps_matrix` quadrants fixture to match 2026-07-17 DECISIONS (`defend`/`priority_target`/`attach_gap`/`wallet_gap`/`insufficient_data`). Result: **106 pass / 0 warn / 0 fail**.
- **Undid premature ITUK flat-override** in `build_bvp_p0_p1.py` that had re-pinned ITUK to 22,389 without final confirm — capture lane stays on bucketed 23,068.

### Changed (2026-07-16) — Workspace map rewrite + root de-clutter
- **`01_data/` root de-cluttered** — ~30 loose files re-filed into numbered topic folders; older duplicates → `92_archive/dedupe_2026-07-16/`, junk → `92_archive/junk_2026-07-16/`. Service PDFs → `03_PMS/service_schedules/`; Mainz conf → `09_meetings/European_Conference_2026_Mainz/`; stretch pilots → `02_GPS/` (newest per family); distributor studies → `08_Distributor/`; KPI/PL/budget dups → `11_planning/` + archive. Root now holds only script-wired files + docs. (`ISZE_IUK_UMI…TESTCASE_v2.xlsx` left at root — open in Excel during sort.)
- **INBOX "dump-then-sort" rule formalised** — `01_data/90_INBOX/` is the single drop zone; `01_data/` root is not. Documented in `DATA_MANIFEST.md` §0, `INDEX.md`, `MAPS.md`, `REFERENCE.md`, `MAP_REGISTRY.yaml`.
- **Maps rewritten** — `DATA_MANIFEST.md` (full), `MAP_REGISTRY.yaml` (v3), `MAPS.md`, `INDEX.md`, `REFERENCE.md`, `CANONICAL.md` refreshed to 2026-07-16 reality.
- **ISZE root scripts relocated** — `upload_gps_data.py`, `upload_ids_data.py`, `run_*_upload.bat` → `04_tools/github_upload/`; path resolution made location-independent (walks to `paths.yaml`). **Hardcoded GitHub PAT removed** — now read from `$ISZE_GH_TOKEN` (⚠ old token `ghp_5Ar8…` must be **revoked**).
- **`_OKF_assessment/`** moved root → `03_analytics/Isuzu/_OKF_assessment/`; hardcoded paths in its `_build/*.py` and `00_derived/pms_briefs/_build/gen_pms_briefs.py` updated.
- **Empty deprecated trees removed** from root: `Dashboards/`, `Projects/`.
- **`01_data/dashboards` junction** verified healthy + load-bearing (kept) — closes scraper health-check Item 7.
- **Task Scheduler:** `ISZE Tender Monitor` registered from the fixed XML (next run Mon 07:30). Competitive-pricing refresh confirmed already live as `ISZE_PMS_IAM_Refresh` (Mon 07:00, last result 0) — spare `ISZE_ScraperRefresh_WeeklyTask.xml` intentionally NOT imported (avoids double-run).
- **Claude Desktop onboarding** added: `00_docs/CLAUDE_DESKTOP_ONBOARDING.md` (paste-ready Project instructions); root `CLAUDE.md` refreshed.
- **GPS Calculator canonical resolved** — `_v9` (build output of `build_gps_v9.py`) declared canonical; the "missing unversioned file" was a stale CANONICAL.md entry (no code reads an unversioned name). Corrected.
- **Discount scanner manual refresh** 2026-07-16 — ran `discount_scraper.py` (after `playwright install chromium`): **168 deals** across Lidl (40) / Delhaize (30) / Colruyt (22) / AH (40) / Carrefour (36) → `04_tools/discount-scanner/deals.json` + `deals_dashboard.html`. Task still unregistered (XML ready).
- **Tender monitor publish FIXED + refreshed** 2026-07-16. Root cause of stale `tender_data.json` (since 2026-05-30): `publish_live_tender_json.ps1` dot-sourced a non-existent helper `..\workspace\isze_root.ps1` (`Get-IszePath`/`Get-DataSubfolderPath`), so step 2/3 always died (exit 1) even though the scraper succeeded. Rewrote the script to resolve `01_data/dashboards/tender_data.json` directly (no helper). `tender_data.json` now current (3.72 MB · 851 notices · 729 opportunities).
- **UIO v19 adoption (2026-07-16):** confirmed `_CURRENT/ISUZU_UIO_Overview_2026.xlsx` is already v19 and is the primary load everywhere; the `v18` entries in `config.py` (UIO_CANDIDATES) and `gps_v9_loaders.py` (UIO_FALLBACKS) were dormant fallbacks — re-pointed v18→v19. Ran full `run_pipeline_and_verify`: **105 pass / 1 fail**. Root `ISUZU_UIO_Overview_2026_v18.xlsx` **kept (not archived)** since not green.
- **ITUK UIO override drift** — closed 2026-07-17: keep **23,068** for PRISM capture lane (fixtures/FACTS aligned); IML DVLA **22,389** stays a separate lane. See `DATA_MANIFEST.md` §7.

### Changed (2026-07-14)
- **Tender Monitor Task Scheduler XML** — fixed dead post-reorg path in `ISZE_TenderMonitor_WeeklyTask.xml` (Jerome must re-import in Task Scheduler).
- **Competitive pricing refresh scheduler** — added `04_tools/autodoc_scraper/ISZE_ScraperRefresh_WeeklyTask.xml` (Sun 21:00 → `run_refresh_scheduled.bat`).
- **Autodoc/Oscaro retired** from scraper health check scope; `autodoc-monthly-refresh` skill retired.
- **Doc path cleanup** — `_HANDOFF_BUNDLE/*.md` `Tools\` → `04_tools\` references.
- `00_docs/ISZE_ROADMAP.md`, `00_docs/roadmaps/scrapers.md`, `00_docs/AUTOMATION_REGISTER.md`, `DECISIONS.md` updated.

### Changed (2026-07-03)
- **FY2025 completeness gap closed** — `sales_2026tillApril.XLSX` (Jan-Mar 2026) and `CY2024-2025.XLSX` (more-complete 2025 re-export, supersedes `CY2025.XLSX`) wired into the pipeline. `sales_fact.parquet` 434,858→477,505 rows, years [2023-2026]. FY2025 (Apr 2025-Mar 2026) is a complete fiscal year for the first time.
- **UIO confirmed on V19** (DVLA-based) — `uio_proxy_used=False` for all 2025 capture rows; the "2025 vs 2024 fleet proxy" caveat no longer applies.
- **Credit notes/returns (SaTy CR/RE) excluded from revenue metrics** — 280 rows / €1.65M network-wide, a documented judgment call (not ERP-confirmed, reversible). See `DECISIONS.md` 2026-07-03.
- **Parts base €94.26M→€103.57M, network GPS CY2025 50.2%→51.1%** — both legitimate (new data outweighs CR/RE removal), reconciled in FACTS.md.
- Verified `Sales_israel_1799&_1797.XLSX` is a redundant, already-captured export (footer-row artifact caused an apparent 2x total) — correctly left unwired.

### Changed (2026-07-02)
- **PMS capture is now interval-aware for air filters** — `air_filter` factor 1.0 → **0.5 PROVISIONAL** (pending IML ratio); air capture ~doubles vs pre-2026-07-02 outputs. See `DECISIONS.md` 2026-07-02.
- **`sales_fact.parquet` carries `fig_key`** (+ `fig_key_source`) — joined from `parts_catalog_dimension` (98.9% coverage), SAP `FIG KEY CLASSIFICATION` auto-ingested when the CY export adds it; new verify check `sales_fact.fig_key`. Roadmap "Build now" blockers updated in `00_docs/ISZE_ROADMAP.md`.

### Added
- `04_tools/workspace/verify_scheduled_paths.ps1` — fail-loud check for stale Scheduled skill paths
- `05_memory/projects/pricing-basket-2026.md` — confirmed pricing figures (unattended prompts cite this)
- `.github/workflows/prism-tests.yml` — CI pytest on PRISM `tests/`
- `04_tools/workspace/git_preflight.ps1` — pre-commit safety gate (billing, secrets, PAT scan, `git add -n` check)
- `04_tools/_shared/tests/conftest.py` — shared pytest fixtures for `IncrementalCsvWriter`
- Root `.gitignore` — full tier-0 policy (replaces md-only placeholder)
- `git init` on ISZE root (`main` branch, no commits yet)

### Changed
- Scraper I/O wave 2: `mekonomen_scraper.py`, `oscaro_scraper.py`, `mister_auto_scraper.py`, `autodoc_tld_scraper.py` → `_shared/scraper_io.IncrementalCsvWriter`
- `00_docs/RUNBOOK_MONTHLY_REFRESH.md` — Excel PQ steps documented (Phase 1–3); rollback table references root git + PRISM submodule
- `DECISIONS.md` — gitignore policy, PRISM submodule, deploy visibility pre-check entries
- Tier-1 path sweep: `FACTS.md`, `01_data/DATA_MANIFEST.md`, `05_memory/projects/sales-analytics-pipeline.md`, `01_data/gpt_safe/DATA_DICTIONARY.md`
- `INDEX.md`, `00_docs/README.md`, `00_docs/AUTOMATION_REGISTER.md` — links to new ops docs
- `00_docs/context_sync_whitelist.txt` — governance + onboarding docs added
- `01_data/DATA_DICTIONARY.md` — column dictionary index (phased expansion)
- `08_gpt/UPLOAD_STATUS.md` — GPT upload drift tracking (populated)

---

## 2026-06-13 — Path consolidation complete (Batches 1–3)

### Changed
- **Batch 1:** PRISM `config.py` folder constants; seven PRISM scripts; new `04_tools/workspace/isze_paths.py` and `isze_root.ps1` helpers. See audit-export `path-consolidation-batch1-report.md`.
- **Batch 2:** 32 Python/PowerShell files — Evidence sync, dashboard injectors, dealer sell-out, IDS ranking, tender publish, `sync_to_deploys.ps1` root resolution. Deploy-side `../Data/` and `Projects/` rewrites **preserved** as compatibility paths. See audit-export `path-consolidation-batch2-report.md`.
- **Batch 3:** 20 documentation files + 10 scheduled skills — numbered paths in Tier-1 docs, roadmaps, PRISM docs; path preflight blocks on all ISZE scheduled jobs. See audit-export `path-consolidation-batch3-docs-skills-report.md`.

### Documentation
- Scheduled skill path cleanup: 10 `SKILL.md` files under `Documents\Claude\Scheduled\` updated (~30 path mappings); path preflight gates added. See audit-export `scheduled-path-fix-report.md`.
- `00_docs/agent/NOTES.md` — scheduled inventory migrated to `00_docs/AUTOMATION_REGISTER.md`.
- `AGENTS.md`, `INDEX.md`, `00_docs/REFERENCE.md`, `00_docs/CANONICAL.md`, `00_docs/UI_STACK.md` — numbered folder paths.

### Decisions
- See [DECISIONS.md](DECISIONS.md) § 2026-06-13 entries (numbered layout, paths.yaml, deploy mirror, verify-before-quote, scraper propose-only).

---

## 2026-06-13 — Numbered folder reorg

### Changed
- Top-level folders renamed to numbered layout: `00_docs/` … `09_meetings/`, `90_archive/`, `91_legacy/`.
- Added `paths.yaml` as folder contract (read by PRISM `config.py` and agent docs).
- Slimmed `INDEX.md`; extended `00_docs/REFERENCE.md` and `00_docs/MAPS.md`.
- Introduced `00_docs/context_sync_whitelist.txt` for deploy context mirror sync.
- Standard workspace root: `$env:ISZE_ROOT` (see `paths.yaml`, `04_tools/workspace/isze_root.ps1`).

### Archived
- `isze-prism-analytics` duplicate repo → `90_archive/duplicate_repos/`.
- `GPT_VectorStore/` → `90_archive/` (superseded by `08_gpt/` — confirm no unique content; see [DECISIONS.md](DECISIONS.md) open items).

### Documentation
- `00_docs/ISZE_Cleanup_Plan.md` — target layout diagram updated to numbered tree (implemented state).
- Deploy-side `Data/` and `Projects/` paths documented as **compatibility paths only** for GitHub Pages runtime — local source is `01_data/`, `03_analytics/`. See [DECISIONS.md](DECISIONS.md) § deploy-side compatibility paths.

### Decisions
- [DECISIONS.md](DECISIONS.md) § 2026-06-13 — Numbered folder layout.
- [DECISIONS.md](DECISIONS.md) § 2026-06-13 — Primary external UI is HTML (GitHub Pages) — source: `00_docs/UI_STACK.md`.

---

## Backfill TODO

- [ ] Log Phase 0–4 cleanup plan items from `00_docs/ISZE_Cleanup_Plan.md` as dated entries when verified.
- [ ] Record Jerome decisions on unresolved scheduled-skill paths (intel brief publish target, freshness-check xlsx files).
- [ ] Link each structural change to a `DECISIONS.md` entry where applicable.
