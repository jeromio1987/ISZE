# ISZE workspace index

**Parent workspace:** [`../../INDEX.md`](../../INDEX.md) · **Layout:** [`paths.yaml`](paths.yaml) · **Agent sync:** 2026-07-16.

## Root (bootstrap only)

| File | Role |
|------|------|
| `INDEX.md` | This file — start here |
| `AGENTS.md` | Agent rules |
| `CLAUDE.md` | Claude Code entry |
| `FACTS.md` | Pinned narrative / discussion anchors |
| `README.md` | One-line pointer → `00_docs/README.md` |
| `paths.yaml` | Folder constants (read by PRISM `config.py`) |

Everything else lives in numbered folders below.

## Numbered folders

| # | Folder | Role |
|---|--------|------|
| 00 | `00_docs/` | Routing, maps, roadmaps, human README, CANONICAL |
| 01 | `01_data/` | Raw + derived (`00_derived/`) + `14_dashboards/*.json` — subfolder map: `01_data/DATA_MANIFEST.md` §2. **New files → `01_data/90_INBOX/` then sort (§0)** |
| 02 | `02_dashboards/` | HTML source → `sync_to_deploys.ps1` |
| 03 | `03_analytics/` | PRISM, PMS pilot, GPS dashboard code |
| 04 | `04_tools/` | Scrapers, SPA, **`workspace/`** reorg scripts |
| 05 | `05_memory/` | Durable facts, briefs, glossary |
| 06 | `06_uio/` | UIO workbook + build scripts |
| 07 | `07_deploy/` | Master Dashboard + publish-site (deploy only) |
| 08 | `08_gpt/` | GPT Enterprise knowledge pack |
| 09 | `09_meetings/` | Decks, evaluaties, business plans |
| 90 | `90_archive/` | Cold storage |
| 91 | `91_legacy/` | Old Streamlit, orchestrator, experiments |

## Quick lookup

| Need | Path |
|------|------|
| **Drop / sort new data** | `01_data/90_INBOX/` → file per `01_data/DATA_MANIFEST.md` §0–§1 |
| Task routing | `00_docs/ROUTING.yaml` |
| Maps / registry | `00_docs/MAPS.md` · `00_docs/MAP_REGISTRY.yaml` |
| Programme roadmap | `00_docs/ISZE_ROADMAP.md` |
| Versioned filenames | `00_docs/CANONICAL.md` |
| **Excel pre-delivery check** | `00_docs/EXCEL_PRE_DELIVERY_CHECK.md` |
| Headline metrics | `01_data/derived/metrics_snapshot.json` + `FACTS.md` |
| Workspace root | `$env:ISZE_ROOT` (see `paths.yaml`) |
| PRISM | `03_analytics/Isuzu/prism/run_prism.ps1` (**8503**) |
| Human onboarding | `00_docs/HUMAN_ONBOARDING.md` |
| **Holiday laptop / GitHub clones** | `00_docs/HOLIDAY_LAPTOP.md` |
| Monthly refresh runbook | `00_docs/RUNBOOK_MONTHLY_REFRESH.md` |
| Automation register | `00_docs/AUTOMATION_REGISTER.md` |
| Data dictionary | `01_data/DATA_DICTIONARY.md` |
| Changelog | `CHANGELOG.md` |
| Decision log | `DECISIONS.md` |
| Workspace scripts | `04_tools/workspace/` |
| Scheduled path check | `04_tools/workspace/verify_scheduled_paths.ps1` |
| PRISM CI | `.github/workflows/prism-tests.yml` |

## Rules

- **New data:** always land in `01_data/90_INBOX/` first, then sort per `DATA_MANIFEST.md` §1 — never dump into `01_data/` root (root holds only wired files + docs)
- **Root:** `$env:ISZE_ROOT` + `paths.yaml` folder contract — only numbered folders + bootstrap MD/config live here
- **Numbers:** green `_verification_report.json` → `metrics_snapshot.json` → `FACTS.md`
- **HTML:** edit `02_dashboards/` only; never `07_deploy/`
- **MD:** edit bootstrap + numbered folders; never deploy `context/` mirror

Full reference: `00_docs/REFERENCE.md`
