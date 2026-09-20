# ISZE workspace index

> ## TALK TO JEROME LIKE A PERSON
>
> **Read this before you write anything to him.**
>
> He has said it repeatedly: *"no bot language", "talk clear to me", "provide a decent
> explanation".* This is a hard rule, not a style preference.
>
> **Do:**
> - Answer first. One plain sentence with the verdict, then the reasoning.
> - Explain *why* something happened. He asked for the mechanism, not the status.
> - Use normal business words. "What we billed", "dealer price", "trucks in service".
> - Write prose. Paragraphs. Complete sentences.
> - Say "I" and "you". You are a colleague sitting next to him.
>
> **Never:**
> - **Release-note voice.** No "Rebuilt X", "Fixed Y", "Still open: Z", "Noted." No changelog
>   stacked in bullets. That reads as a machine ticking tickets.
> - **Process narration.** No "Let me…", "I'll now…", "First I'll check…". Do the work, then
>   tell him what you found.
> - **A table as the answer.** Tables are for data he will look up, never for the reply itself.
> - **Agent words.** No ship-gate, receipt, harness, loop, packet, drift, lane, surface,
>   payload. If you must name a thing, describe it in plain English once.
> - **Status without meaning.** "Pipeline green" means nothing to him. "The numbers now agree"
>   does.
> - **Bold every third phrase.** Emphasis stops working when everything is emphasised.
> - **Sign off with a summary of your own summary.**
>
> **Before you send, read it back as if he had spoken it out loud.** If a sentence would sound
> absurd said by a person, rewrite it.
>
> **Full rule:** [`.cursor/rules/jerome-talk-clear.mdc`](.cursor/rules/jerome-talk-clear.mdc)

**Parent workspace:** [`../../INDEX.md`](../../INDEX.md) · **Layout:** [`paths.yaml`](paths.yaml) · **Agent sync:** 2026-09-17.

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
| **Programme roadmap (the queue)** | `00_docs/ISZE_ROADMAP.md` — open work §1, decisions waiting on Jerome §2, live §3, closed §5. Domain depth: `00_docs/roadmaps/` |
| **Exec aftersales paper (shared HTML)** | `02_dashboards/sales/ISZE_Exec_Aftersales_Paper.html` + `OPEN_ISZE_Exec_Aftersales_Paper.cmd` · brief `00_docs/PROMPT_ISZE_EXEC_SALES_PAPER.md` · retro `00_docs/REVIEW_EXEC_AFTERSALES_PAPER_20260915.md` · gate `02_dashboards/_build/verify_exec_aftersales_paper.py` |
| **IAM shop vs billed (PN scatter)** | `02_dashboards/pricing/ISZE_IAM_Price_vs_Billed_PN.html` + `OPEN_ISZE_IAM_Price_vs_Billed_PN.cmd` |
| Versioned filenames | `00_docs/CANONICAL.md` |
| **Excel pre-delivery check** | `00_docs/EXCEL_PRE_DELIVERY_CHECK.md` |
| Headline metrics | `01_data/00_derived/metrics_snapshot.json` + `FACTS.md` |
| Workspace root | `$env:ISZE_ROOT` (see `paths.yaml`) |
| PRISM | `03_analytics/Isuzu/prism/run_prism.ps1` (**8503**, MD-safe) · `run_prism_internal.ps1` (extra tabs) |
| Human onboarding | `00_docs/HUMAN_ONBOARDING.md` |
| **Holiday laptop / GitHub clones** | `00_docs/HOLIDAY_LAPTOP.md` |
| Monthly refresh runbook | `00_docs/RUNBOOK_MONTHLY_REFRESH.md` |
| Automation register | `00_docs/AUTOMATION_REGISTER.md` |
| Data dictionary | `01_data/DATA_DICTIONARY.md` |
| **Isuzu OS data map** | `00_docs/ISZE_OS_DATA_MAP.yaml` · `02_dashboards/ops/ISZE_OS_Data_Map.html` |
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
