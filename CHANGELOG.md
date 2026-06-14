# ISZE changelog

**Scope:** Workspace structure, documentation, deploy layout — not PRISM code detail (see `03_analytics/Isuzu/prism/CHANGELOG.md`) or GPT pack detail (see `08_gpt/CHANGELOG.md`).

**Format:** [Keep a Changelog](https://keepachangelog.com/) style — newest first. Append only; do not rewrite past entries.

---

## [Unreleased]

### Added
- `00_docs/HUMAN_ONBOARDING.md` — human successor entry point
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
