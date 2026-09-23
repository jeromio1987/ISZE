# Agent rules — ISZE workspace

**Agent sync:** 2026-08-25 · Layout: `paths.yaml` · Maps: `00_docs/MAPS.md`

## Path conventions

- **`paths.yaml`** is the folder contract — numbered folders (`01_data/` … `09_meetings/`). PRISM reads it via `config.py`; non-PRISM Python uses `04_tools/_shared/paths.py` or `04_tools/workspace/isze_paths.py`; PowerShell uses `04_tools/workspace/isze_root.ps1`.
- **`$env:ISZE_ROOT`** is the standard workspace root (set in launchers/skills; do not hardcode `C:\Users\jerom\...` in new docs, skills, or code).
- **Deploy-side compatibility paths** (`fetch('../Data/...')`, `Data/dashboards/` on GitHub Pages, deploy-side `Projects/`) are runtime URLs for published HTML — not local source paths. Local source: `01_data/`, `02_dashboards/`, `03_analytics/`.
- **`07_deploy/`** is a generated deploy mirror — never edit manually; edit `02_dashboards/` + run `sync_to_deploys.ps1`.

## Bootstrap (every session)

1. Read **`INDEX.md`** — numbered folders; do not recursive-glob the repo.
2. Read **`00_docs/ROUTING.yaml`** for the matching `tasks.<name>` entry — open only listed paths; stop when answered.
3. Fallback: **`00_docs/REFERENCE.md`** if no task key fits.
4. **Automation / overnight cron SSOT:** `00_docs/AUTOMATION_REGISTER.md` + `Documents\Claude\Scheduled\` + latest `05_memory/briefs/automation_drift_*.md`. Do not invent a second scheduler via Cursor `/loop` alone. Workspace OS audit: `../docs/OVERNIGHT_PROCESS_AUDIT_2026-08-25.md`.
5. **Numbers (read in order, stop when answered):**
   - `01_data/00_derived/_verification_report.json` — must be green (`ok`) before quoting KPIs
   - `01_data/00_derived/metrics_snapshot.json` — headline figures (~2 KB)
   - `FACTS.md` — discussion context / pinned narrative only if needed
   - `03_analytics/Isuzu/prism/docs/metric_dictionary.md` — formulas when editing metrics
   - Never invent KPIs. Do not quote legacy PMS capture from old HTML without PRISM check.
6. **Pipeline changes:** run `.cursor/skills/isze-verify-pipeline` (or `03_analytics/Isuzu/prism/scripts/run_pipeline_and_verify.ps1`) before citing capture %, GPS, or BVP mix.
7. **Excel deliverables:** run checks in `00_docs/EXCEL_PRE_DELIVERY_CHECK.md` before shipping any workbook to Jerome.
8. **Ship gate (all shared HTML / dashboards):** `.cursor/rules/isze-ship-gate.mdc` — exit 0 ≠ done; run verify + paint check before claiming done. **IDS HTML / maps / client packs:** also `isze-ids-delivery.mdc` + `04_tools/ids_dealer_ranking/IDS_2026_LOGIC_CHECK.md` §6b. Paint evidence: `isze-verify-rendered-output.mdc`.
9. **GPS / ITUK:** read `01_data/91_build/GPS_FILE_LINEAGE.md` and `.cursor/rules/isze-gps-ituk.mdc` — ITUK never on kickback or Other DBs tabs; dealer £ ≠ ISZE € wallet.
10. **Deploy mirror:** never read or edit `07_deploy/Master Dashboard/context/` — regenerated from `00_docs/context_sync_whitelist.txt`.
11. **Series → weight band (one authored map):** the only place an Isuzu series code (`NLR`, `NMR`, `NPR`, `NKR`, …) is turned into a weight band is `03_analytics/Isuzu/prism/data/series_to_band.csv` — one row per code, edited by hand. Read it through `03_analytics/Isuzu/prism/modules/vehicle_bands.py` (`band_for`, `group_for`, `gvw_t_for`); the neutral derived table built from it is `01_data/00_derived/vehicle_band_applicability.csv`. No script may keep its own dictionary of series codes — the retired probe `01_data/91_build/pn_ammo_probe_20260918/_tonnage_capable.py` is what that cost us, because its own copy had `NKR` on the 5.5 t band.

## Edits & deploy

| Change type | Workflow |
|-------------|----------|
| Static HTML | Edit `02_dashboards/` → `02_dashboards/sync_to_deploys.ps1` |
| Dashboard JSON | `build_isze_dashboard_json.py` → `01_data/dashboards/*.json` |
| PRISM UI | `03_analytics/Isuzu/prism/` — `run_prism.ps1` (**8503**) |

## Data safety

- Never commit or paste `01_data/raw/sales/*` line-level billing.
- Prefer `01_data/gpt_safe/` for external / GPT uploads.
- Tender live feed: **`01_data/dashboards/tender_data.json`** only.

## Shared vs internal language (Cursor + Claude)

Shared rule: `.cursor/rules/isze-external-iml-language.mdc` — **always on**.  
**Never use the old A/B audience labels** in chat or files Jerome opens — say **shared / external** vs **internal / private**.

**Defaults:** this chat = **internal**; `02_dashboards/`, meeting HTML, and Excel studies = **shared**.

- **Shared** decks/HTML/PDF/email: never use internal nicknames (**IML v7**, **Model B**, **PRISM lane**). Say **IML service schedule** and point to the real business source (Apr 2026 PMS analysis / trip report / business case / GIDSS). No personal contact names — roles only (IML / ITUK).
- **Internal** sparring / private notes: nicknames and blunt traps OK (`FACTS.md`, `DECISIONS.md`, memory, speaker notes, agent chat).

## Production — ask Jerome first

Scheduled SKILL paths, `06_uio/_CURRENT/*.xlsx` formulas, `sales_fact.parquet` rebuilds, GitHub Pages deploy. Outward mail/packs/versions: `.cursor/rules/isze-no-ship-without-ok.mdc` (draft-only; no silent version overwrite; rebuild/ship only on explicit ask). Customer / distributor mail: attach shared `.pptx`/`.pdf` only (never `.cmd`/`.md`/`.csv`/`.zip`/scripts); see skill `isze-managers-meeting-reply` § Customer attachments.

## Memory vs markdown

| Layer | Role |
|-------|------|
| `05_memory/projects/*.md`, `05_memory/glossary.md` | Durable facts — never overrides KPIs |
| `03_analytics/Isuzu/prism/docs/*.md` | Metric definitions, build contracts |
| `01_data/DATA_MANIFEST.md` | File registry, ingest |

After large doc edits, reconcile `05_memory/` against PRISM / derived CSVs.
