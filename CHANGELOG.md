# ISZE changelog

**Scope:** Workspace structure, documentation, deploy layout — not PRISM code detail (see `03_analytics/Isuzu/prism/CHANGELOG.md`) or GPT pack detail (see `08_gpt/CHANGELOG.md`).

**Format:** [Keep a Changelog](https://keepachangelog.com/) style — newest first. Append only; do not rewrite past entries.

---

## [Unreleased]

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
