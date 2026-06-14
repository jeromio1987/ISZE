# ISZE extended reference

**Not bootstrap.** Read `INDEX.md` → `00_docs/ROUTING.yaml` → `AGENTS.md` first. Open this file for documentation map, EU Conf assets, UI stack choice, archived maps, and deprecated paths.

**Agent sync:** 2026-06-13 (Tier 3 reference — see `docs/MAPS.md` for tiers)

---

## Documentation map

| Topic | Canonical markdown |
|-------|-------------------|
| Data files, ingest, GPT-safe | `01_data/DATA_MANIFEST.md` |
| Column dictionary | `01_data/DATA_DICTIONARY.md` |
| Human onboarding | `00_docs/HUMAN_ONBOARDING.md` |
| Monthly refresh runbook | `00_docs/RUNBOOK_MONTHLY_REFRESH.md` |
| Scheduled jobs register | `00_docs/AUTOMATION_REGISTER.md` |
| Workspace changelog / decisions | `CHANGELOG.md`, `DECISIONS.md` |
| GPT upload status | `08_gpt/UPLOAD_STATUS.md` |
| PMS / GPS / BVP / UIO metrics | `03_analytics/Isuzu/prism/docs/metric_dictionary.md` |
| PRISM dashboard CSV contracts | `03_analytics/Isuzu/prism/docs/dashboard_contracts.md` |
| Data integrity flags | `03_analytics/Isuzu/prism/docs/DATA_INTEGRITY_FLAGS_2026-05-28.md` |
| BVP strategy narrative | `03_analytics/Isuzu/prism/docs/BVP_Strategy_Report_2026-05-28.md` |
| Pipeline verify output | `01_data/derived/_verification_report.md` (sign-off only when `ok`) |
| Sales / phase models (Excel + derived) | `05_memory/projects/sales-analytics-pipeline.md` |
| PMS programme (ITUK pilot) | `05_memory/projects/pms-coverage.md` |
| EU Conf 26 GPS/PMS deck + MH review | `09_meetings/EU_Conf26/MH_Remarks_Changelog.md` |
| Pricing / IE40 | `05_memory/projects/competitiveness.md` |
| UIO workbook logic | `05_memory/projects/uio.md`, `06_uio/_CURRENT/README.md` |
| FY action plans | `05_memory/projects/action-plan-fy2026.md`, `action-plan-fy2027.md` |
| AIM / competitiveness / lubricants | `05_memory/projects/aftermarket-intelligence.md`, `competitiveness.md`, `lubricants.md` |
| Terms & entities | `05_memory/glossary.md` |
| Map registry / diagram | `docs/MAP_REGISTRY.yaml`, `docs/MAPS.md` |
| Versioned filenames | `00_docs/CANONICAL.md` |
| Roadmap (consolidated) | `00_docs/ISZE_ROADMAP.md` → `00_docs/roadmaps/` |
| HTML dashboard detail | `docs/roadmaps/html.md` |
| Scrapers programme | `docs/roadmaps/scrapers.md` |
| GPS / fig-key programme | `docs/roadmaps/gps.md` |
| Jarvis / tools programme | `docs/roadmaps/tools.md` |
| Claude vs GPT / tier protocol | `docs/agent/AI_STACK.md` (full memo: `AI_Stack_Architecture_Apr2026.md`) |
| Weekly briefs | `05_memory/briefs/` |
| PMS pilot artefacts | `03_analytics/Isuzu/pms-pilot/` |
| GPT Enterprise knowledge (upload) | `08_gpt/2_KNOWLEDGE_FILES/*.md` |
| Cleanup / dedupe plan | `00_docs/ISZE_Cleanup_Plan.md` |
| Repo overview | `00_docs/README.md` |

**Jerome working style:** `Isuzu/_SKILL_UPDATE/` or scheduled `isze-context` — see `docs/agent/NOTES.md`.

---

## UI stacks (decision 2026-06-13)

**Primary external share:** static **HTML** → GitHub Pages. Full record: **`docs/UI_STACK.md`**.

Pipeline output is one spine (`01_data/derived/`). UI choice is presentation only.

| Use case | Primary | Port / path |
|----------|---------|-------------|
| **External share (URL)** | **HTML** `02_dashboards/` → sync | GitHub Pages |
| Day-to-day KPI exploration, filters, PDF, decision models | **Streamlit PRISM** | `run_prism.ps1` · **8503** |
| Internal SQL-native BI boards | **Evidence** | `run_evidence.ps1` · **3000** |
| Offset Insights interactivity (sandbox) | **Dash** | `run_dash.ps1` · **8050** |
| Ops pages not yet in PRISM | **ISZE_Dashboard** (legacy sandbox) | `ISZE_Dashboard/Home.py` |

Hub: `02_dashboards/PROJECT_HUB.html`

---

## EU Conf 26 & deck assets

| Asset | Path |
|-------|------|
| Parts Sales deck (clean) | `09_meetings/EU_Conf26/EU Conf 26 ISZE Parts Sales 20260608 CLEAN.pptx` |
| MH remark changelog | `09_meetings/EU_Conf26/MH_Remarks_Changelog.md` |
| MH email draft | `09_meetings/EU_Conf26/MH_Remarks_Response_Email.txt` |
| Re-apply clean script | `09_meetings/EU_Conf26/_scan_and_clean_deck.py` |
| Jerome working copy | `C:\Users\jerom\Downloads\EU Conf 26 ISZE Parts Sales 20260608 CLEAN.pptx` |
| GPS/PMS standalone (7 slides) | `ISZE_GPS_PMS_Conf26_v3.pptx` |
| GPS/PMS section builder | `09_meetings/UTI/_build/build_gps_pms_section.py` → `GPS_PMS_Section.pptx` |

---

## Archived maps (historical — in `90_archive/`)

| Was | Now |
|-----|-----|
| `AUDIT_2026-05.md` | `90_archive/versioned_docs/AUDIT_2026-05.md` |
| `ISZE_Tooling_Map_2026-05-22.md` | `90_archive/versioned_docs/ISZE_Tooling_Map_2026-05-22.md` |
| `ISZE_GPS_PMS_Conf26_v1/v2.pptx` | `90_archive/versioned_docs/` |
| `isze-prism-analytics/` (local git clone) | `90_archive/duplicate_repos/isze-prism-analytics/` |
| `Master Dashboard/prism-analytics/` | `90_archive/duplicate_repos/Master_Dashboard_prism-analytics/` |

**Canonical PRISM code:** `03_analytics/Isuzu/prism/` only. Remote `isze-prism-analytics` git history preserved inside archive folder if you need to recover.

Live routing: `INDEX.md` + `docs/ROUTING.yaml` — refresh tooling map quarterly into `90_archive/versioned_docs/` if needed.

---

## Deprecated / superseded

| Path | Use instead |
|------|-------------|
| `memory/context/isuzu.md` | `05_memory/glossary.md` |
| `Isuzu/isze-company-context.md` | `03_analytics/Isuzu/_SKILL_UPDATE/isze-company-context.md` |
| `AI_Briefs/` (root) | `05_memory/briefs/` |
| `Isuzu/PMS project/` | `03_analytics/Isuzu/pms-pilot/` |
| `Projects/Isuzu/data/distributor_master_mapping.csv` | `03_analytics/Isuzu/prism/data/distributor_master_mapping.csv` |
| `02_dashboards/ROADMAP.md` | `00_docs/roadmaps/html.md` |
| `Tools/SCRAPERS_ROADMAP.md` | `00_docs/roadmaps/scrapers.md` |
| `tender scraper/` (root v2) | `04_tools/ISZE_Tender_Monitor_Install/` v3 |
| `02_dashboards/*.json` | `01_data/dashboards/*.json` only |
| `Tools/tender scraper/` | `90_archive/Tools_tender_scraper_legacy/` |
| `Tools/isze-tools-github/` | `90_archive/isze-tools-github/` |
| `prism/mockups/` | `90_archive/prism_mockups/mockups/` |
| `prism/data/sales_detailed_for_claude_full_fixed.tsv` | `01_data/derived/sales_fact.parquet` |
| `isze-prism-analytics/` | `03_analytics/Isuzu/prism/` |
| `EU Conf 26 ... MH CHK_FIXED.pptx` (Downloads) | **Do not use** — partial fix |
| `EU Conf 26 ... MH CHK.pptx` | `EU Conf 26 ISZE Parts Sales 20260608 CLEAN.pptx` |
| `ISZE_GPS_PMS_Conf26_v1.pptx` / `v2.pptx` | `ISZE_GPS_PMS_Conf26_v3.pptx` or EU Conf master deck |

---

## Drop zone

New SAP / exports → `01_data/_INBOX/` then file per `01_data/DATA_MANIFEST.md`.

---

## FACTS ↔ memory ↔ GPT reconciliation

| Layer | Role | Update when |
|-------|------|-------------|
| `01_data/derived/metrics_snapshot.json` | Machine-readable headline KPIs | Every green pipeline run |
| `FACTS.md` | Human-readable pinned figures + pricing anchors | Pipeline changes a headline number |
| `prism/data/facts_anchor.yaml` | Drift-check pins for `verify_facts_drift.py` | Same time as `FACTS.md` |
| `05_memory/projects/*.md` | Programme status, open questions — **not** duplicate formulas | Topic evolves; run `isze-memory-review` after large doc edits |
| `08_gpt/2_KNOWLEDGE_FILES/` | Monthly Custom GPT upload pack | Manual batch re-upload |

**Conflict rule:** `metrics_snapshot.json` (green verify) → `FACTS.md` wins over memory, decks, and GPT knowledge files. Fix the downstream copy.
