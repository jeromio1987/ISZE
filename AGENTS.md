# Agent rules — ISZE workspace

**Agent sync:** 2026-06-13 · Layout: `paths.yaml` · Maps: `00_docs/MAPS.md`

## Path conventions

- **`paths.yaml`** is the folder contract — numbered folders (`01_data/` … `09_meetings/`). PRISM reads it via `config.py`; non-PRISM Python uses `04_tools/_shared/paths.py` or `04_tools/workspace/isze_paths.py`; PowerShell uses `04_tools/workspace/isze_root.ps1`.
- **`$env:ISZE_ROOT`** is the standard workspace root (set in launchers/skills; do not hardcode `C:\Users\jerom\...` in new docs, skills, or code).
- **Deploy-side compatibility paths** (`fetch('../Data/...')`, `Data/dashboards/` on GitHub Pages, deploy-side `Projects/`) are runtime URLs for published HTML — not local source paths. Local source: `01_data/`, `02_dashboards/`, `03_analytics/`.
- **`07_deploy/`** is a generated deploy mirror — never edit manually; edit `02_dashboards/` + run `sync_to_deploys.ps1`.

## Bootstrap (every session)

1. Read **`INDEX.md`** — numbered folders; do not recursive-glob the repo.
2. Read **`00_docs/ROUTING.yaml`** for the matching `tasks.<name>` entry — open only listed paths; stop when answered.
3. Fallback: **`00_docs/REFERENCE.md`** if no task key fits.
4. **Numbers (read in order, stop when answered):**
   - `01_data/derived/_verification_report.json` — must be green (`ok`) before quoting KPIs
   - `01_data/derived/metrics_snapshot.json` — headline figures (~2 KB)
   - `FACTS.md` — discussion context / pinned narrative only if needed
   - `03_analytics/Isuzu/prism/docs/metric_dictionary.md` — formulas when editing metrics
   - Never invent KPIs. Do not quote legacy PMS capture from old HTML without PRISM check.
5. **Pipeline changes:** run `.cursor/skills/isze-verify-pipeline` (or `03_analytics/Isuzu/prism/scripts/run_pipeline_and_verify.ps1`) before citing capture %, GPS, or BVP mix.
6. **Excel deliverables:** run checks in `00_docs/EXCEL_PRE_DELIVERY_CHECK.md` before shipping any workbook to Jerome.
7. **GPS / ITUK:** read `01_data/91_build/GPS_FILE_LINEAGE.md` and `.cursor/rules/isze-gps-ituk.mdc` — ITUK never on kickback or Other DBs tabs; dealer £ ≠ ISZE € wallet.
8. **Deploy mirror:** never read or edit `07_deploy/Master Dashboard/context/` — regenerated from `00_docs/context_sync_whitelist.txt`.

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

## Production — ask Jerome first

Scheduled SKILL paths, `06_uio/_CURRENT/*.xlsx` formulas, `sales_fact.parquet` rebuilds, GitHub Pages deploy.

## Memory vs markdown

| Layer | Role |
|-------|------|
| `05_memory/projects/*.md`, `05_memory/glossary.md` | Durable facts — never overrides KPIs |
| `03_analytics/Isuzu/prism/docs/*.md` | Metric definitions, build contracts |
| `01_data/DATA_MANIFEST.md` | File registry, ingest |

After large doc edits, reconcile `05_memory/` against PRISM / derived CSVs.
